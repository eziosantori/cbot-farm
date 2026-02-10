import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .backtest import run_real_backtest
from .config import REPORTS_DIR, ROOT, load_configs
from .ingestion import ingest_data
from .optimization import evaluate_gates, optimize_params


def run_cycle(
    iterations: int,
    skip_ingest: bool,
    from_override: Optional[str],
    to_override: Optional[str],
    ingest_only: bool,
    markets_filter: Optional[List[str]],
    symbols_filter: Optional[List[str]],
    timeframes_filter: Optional[List[str]],
) -> None:
    universe, risk = load_configs()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if skip_ingest:
        ingest_state = {
            "provider": universe.get("source", {}).get("provider", "unknown"),
            "status": "skipped",
        }
    else:
        ingest_state = ingest_data(
            universe=universe,
            from_override=from_override,
            to_override=to_override,
            markets_filter=markets_filter,
            symbols_filter=symbols_filter,
            timeframes_filter=timeframes_filter,
        )

    if ingest_only:
        print(
            f"[ingest-only] status={ingest_state.get('status')} "
            f"manifest={ingest_state.get('manifest_path')}"
        )
        return

    retries_without_improvement = 0
    best_score = float("-inf")

    data_root = ROOT / universe.get("ingestion", {}).get("output_dir", "data/dukascopy")

    for iteration in range(1, iterations + 1):
        params = optimize_params(iteration)
        metrics, bt_details = run_real_backtest(
            params=params,
            data_root=data_root,
            markets_filter=markets_filter,
            symbols_filter=symbols_filter,
            timeframes_filter=timeframes_filter,
        )
        gates = evaluate_gates(metrics, risk)
        score = metrics.total_return_pct - metrics.max_drawdown_pct

        if score > best_score:
            best_score = score
            retries_without_improvement = 0
        else:
            retries_without_improvement += 1

        run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        payload = {
            "run_id": f"{run_id}_{iteration}",
            "iteration": iteration,
            "ingest": ingest_state,
            "strategy": "S1 Trend EMA Cross (real backtest)",
            "market": markets_filter[0] if markets_filter and len(markets_filter) == 1 else "multi",
            "timeframes": timeframes_filter or ["5m", "15m", "1h"],
            "params": params,
            "backtest": bt_details,
            "metrics": metrics.__dict__,
            "gates": gates,
            "retries_without_improvement": retries_without_improvement,
        }

        out_path = Path(REPORTS_DIR) / f"run_{run_id}_{iteration}.json"
        with out_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)

        print(f"[iteration {iteration}] report: {out_path}")
        if gates["promoted"]:
            print(f"[iteration {iteration}] candidate promoted")
            break

        if retries_without_improvement >= risk["optimization"]["max_retries"]:
            print("[stop] max retries without improvement reached")
            break
