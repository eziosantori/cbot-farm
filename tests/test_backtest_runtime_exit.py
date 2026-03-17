import csv
import tempfile
import unittest
from pathlib import Path

from bots.base import BaseBotStrategy
from cbot_farm.backtest import run_real_backtest


class RuntimeExitStrategy(BaseBotStrategy):
    strategy_id = "runtime_exit_test"
    display_name = "Runtime Exit Test"

    def sample_params(self, iteration: int) -> dict:
        return {}

    def normalize_params(self, params: dict, bars_count: int) -> dict:
        return dict(params)

    def prepare_indicators(self, bars, params: dict) -> dict:
        return {}

    def entry_signal(self, i: int, bars, indicators: dict) -> int:
        return 1 if i == 1 else 0

    def should_flip(self, i: int, position: int, bars, indicators: dict) -> bool:
        return False

    def risk_levels(self, i: int, side: int, entry_price: float, bars, indicators: dict, params: dict):
        return 90.0, 130.0

    def update_risk_levels(
        self,
        i: int,
        position: int,
        stop_price: float,
        take_price: float,
        open_trade: dict,
        bars,
        indicators: dict,
        params: dict,
    ):
        if i == 2:
            return 104.0, take_price
        return stop_price, take_price


class BacktestRuntimeExitTestCase(unittest.TestCase):
    def test_runtime_stop_update_is_applied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "indices" / "nas100" / "1h" / "download"
            csv_path.mkdir(parents=True, exist_ok=True)
            dataset = csv_path / "sample.csv"

            rows = [
                {"timestamp": 0, "open": 100, "high": 100, "low": 100, "close": 100},
                {"timestamp": 1, "open": 100, "high": 105, "low": 100, "close": 105},
                {"timestamp": 2, "open": 105, "high": 106, "low": 103, "close": 105},
                {"timestamp": 3, "open": 105, "high": 106, "low": 103, "close": 104},
                {"timestamp": 4, "open": 104, "high": 104, "low": 104, "close": 104},
                {"timestamp": 5, "open": 104, "high": 104, "low": 104, "close": 104},
                {"timestamp": 6, "open": 104, "high": 104, "low": 104, "close": 104},
                {"timestamp": 7, "open": 104, "high": 104, "low": 104, "close": 104},
                {"timestamp": 8, "open": 104, "high": 104, "low": 104, "close": 104},
                {"timestamp": 9, "open": 104, "high": 104, "low": 104, "close": 104},
                {"timestamp": 10, "open": 104, "high": 104, "low": 104, "close": 104},
                {"timestamp": 11, "open": 104, "high": 104, "low": 104, "close": 104},
            ]
            with dataset.open("w", encoding="utf-8", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=["timestamp", "open", "high", "low", "close"])
                writer.writeheader()
                writer.writerows(rows)

            metrics, details = run_real_backtest(
                strategy=RuntimeExitStrategy(),
                params={},
                data_root=Path(tmp_dir),
                markets_filter=["indices"],
                symbols_filter=["nas100"],
                timeframes_filter=["1h"],
                execution_cfg={"default": {"fee_bps_per_side": 0.0, "slippage_bps_per_side": 0.0}},
            )

            self.assertEqual(details["status"], "ok")
            self.assertEqual(details["trades_count"], 1)
            self.assertEqual(details["trade_log"][0]["exit_reason"], "stop_loss")
            self.assertEqual(details["trade_log"][0]["exit_price"], 104.0)
            self.assertEqual(details["trade_log"][0]["stop_price"], 104.0)
            self.assertLess(metrics.total_return_pct, 0.0)


if __name__ == "__main__":
    unittest.main()
