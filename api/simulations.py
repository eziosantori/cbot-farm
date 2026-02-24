from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from bots import get_strategy, list_strategies
from cbot_farm.backtest import run_real_backtest
from cbot_farm.optimization import evaluate_gates


class SimulationService:
    def __init__(
        self,
        reports_root: Path,
        data_root: Path,
        universe_cfg: Dict[str, Any],
        risk_cfg: Dict[str, Any],
    ) -> None:
        self.reports_root = reports_root
        self.data_root = data_root
        self.universe_cfg = universe_cfg
        self.risk_cfg = risk_cfg
        self.reports_root.mkdir(parents=True, exist_ok=True)

    def options(self) -> Dict[str, Any]:
        markets = self.universe_cfg.get("markets", {})
        return {
            "strategies": list_strategies(),
            "markets": markets,
            "defaults": {
                "strategy_id": "ema_cross_atr",
                "iterations": 1,
                "skip_ingest": True,
            },
        }

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        strategy_id = str(payload.get("strategy_id") or "ema_cross_atr")
        market = str(payload.get("market") or "forex")
        symbol = str(payload.get("symbol") or "EURUSD")
        timeframe = str(payload.get("timeframe") or "1h")
        params_override = payload.get("params") if isinstance(payload.get("params"), dict) else {}

        strategy = get_strategy(strategy_id)

        sampled = strategy.sample_params(iteration=1)
        merged_params = {**sampled, **params_override}

        metrics, bt_details = run_real_backtest(
            strategy=strategy,
            params=merged_params,
            data_root=self.data_root,
            markets_filter=[market],
            symbols_filter=[symbol],
            timeframes_filter=[timeframe],
            execution_cfg=self.risk_cfg.get("execution", {}),
        )
        gates = evaluate_gates(metrics, self.risk_cfg)

        now = datetime.now(timezone.utc)
        run_token = now.strftime("%Y%m%d_%H%M%S_%f")
        external_run_id = f"{run_token}_sim"
        run_stem = f"run_{external_run_id}"

        out_payload = {
            "run_id": external_run_id,
            "created_at": now.isoformat(),
            "mode": "simulation_manual",
            "strategy": strategy.display_name,
            "strategy_id": strategy.strategy_id,
            "market": market,
            "symbol": symbol,
            "timeframes": [timeframe],
            "params": merged_params,
            "optimization": {
                "mode": {
                    "source": "manual_override",
                    "candidate_index": None,
                    "total_candidates": 1,
                    "search_mode": "manual",
                    "truncated": False,
                    "raw_total_candidates": 1,
                }
            },
            "backtest": bt_details,
            "metrics": metrics.__dict__,
            "gates": gates,
            "retries_without_improvement": 0,
        }

        out_path = self.reports_root / f"{run_stem}.json"
        with out_path.open("w", encoding="utf-8") as fh:
            json.dump(out_payload, fh, indent=2)

        return {
            "run_id": run_stem,
            "external_run_id": external_run_id,
            "report_path": str(out_path.relative_to(self.reports_root.parent)),
            "metrics": metrics.__dict__,
            "gates": gates,
            "status": bt_details.get("status", "unknown"),
        }
