#!/usr/bin/env python3
import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from random import random, uniform

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
REPORTS_DIR = ROOT / "reports"


@dataclass
class Metrics:
    total_return_pct: float
    sharpe: float
    max_drawdown_pct: float
    oos_degradation_pct: float


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def ingest_data(provider: str) -> dict:
    # Placeholder: integrate real download here (dukascopy-node CLI/API).
    return {"provider": provider, "status": "ok"}


def simulate_backtest() -> Metrics:
    # Stub deterministico di esempio: sostituire con motore reale.
    return Metrics(
        total_return_pct=round(uniform(-2.0, 8.0), 2),
        sharpe=round(uniform(0.6, 1.8), 2),
        max_drawdown_pct=round(uniform(6.0, 16.0), 2),
        oos_degradation_pct=round(uniform(5.0, 45.0), 2),
    )


def optimize_params(iteration: int) -> dict:
    return {
        "ema_fast": 20 + iteration,
        "ema_slow": 50 + iteration,
        "atr_mult_stop": round(1.2 + 0.1 * random(), 2),
    }


def evaluate_gates(metrics: Metrics, risk_cfg: dict) -> dict:
    limits = risk_cfg["risk_limits"]
    opt = risk_cfg["optimization"]
    pass_dd = metrics.max_drawdown_pct <= limits["strategy_max_drawdown_pct"]
    pass_sharpe = metrics.sharpe >= opt["min_sharpe"]
    pass_oos = metrics.oos_degradation_pct <= opt["max_oos_degradation_pct"]
    return {
        "pass_drawdown": pass_dd,
        "pass_sharpe": pass_sharpe,
        "pass_oos_degradation": pass_oos,
        "promoted": pass_dd and pass_sharpe and pass_oos,
    }


def run(iterations: int) -> None:
    universe = load_json(CONFIG_DIR / "universe.json")
    risk = load_json(CONFIG_DIR / "risk.json")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ingest_state = ingest_data(universe["source"]["provider"])

    retries_without_improvement = 0
    best_score = float("-inf")

    for i in range(1, iterations + 1):
        params = optimize_params(i)
        metrics = simulate_backtest()
        gates = evaluate_gates(metrics, risk)
        score = metrics.total_return_pct - metrics.max_drawdown_pct

        if score > best_score:
            best_score = score
            retries_without_improvement = 0
        else:
            retries_without_improvement += 1

        run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        payload = {
            "run_id": f"{run_id}_{i}",
            "iteration": i,
            "ingest": ingest_state,
            "strategy": "S1 Trend EMA Breakout",
            "market": "multi",
            "timeframes": ["5m", "15m", "1h"],
            "params": params,
            "metrics": metrics.__dict__,
            "gates": gates,
            "retries_without_improvement": retries_without_improvement,
        }

        out = REPORTS_DIR / f"run_{run_id}_{i}.json"
        with out.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)

        print(f"[iteration {i}] report: {out}")
        if gates["promoted"]:
            print(f"[iteration {i}] candidate promoted")
            break

        if retries_without_improvement >= risk["optimization"]["max_retries"]:
            print("[stop] max retries without improvement reached")
            break


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=5)
    args = parser.parse_args()
    run(iterations=args.iterations)


if __name__ == "__main__":
    main()
