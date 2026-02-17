#!/usr/bin/env python3
import argparse
import csv
import json
import math
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from statistics import mean, pstdev
from typing import List

import backtrader as bt

from bots import get_strategy
from cbot_farm.backtest import run_real_backtest
from cbot_farm.config import load_configs
from cbot_farm.param_optimization import build_param_plan, params_for_iteration


def bars_per_year(timeframe: str) -> int:
    mapping = {
        "1m": 525600,
        "5m": 105120,
        "15m": 35040,
        "30m": 17520,
        "1h": 8760,
        "4h": 2190,
        "1d": 365,
    }
    return mapping.get(timeframe.lower(), 8760)


def oos_degradation_pct(returns: List[float]) -> float:
    n = len(returns)
    if n < 20:
        return 100.0

    split = int(n * 0.8)
    is_returns = returns[:split]
    oos_returns = returns[split:]
    is_total = math.prod((1.0 + r) for r in is_returns) - 1.0
    oos_total = math.prod((1.0 + r) for r in oos_returns) - 1.0

    if is_total <= 0:
        return 100.0

    degradation = ((is_total - oos_total) / abs(is_total)) * 100.0
    return max(0.0, round(degradation, 2))


def resolve_cost_profile(risk_cfg: dict, market: str) -> dict:
    execution = risk_cfg.get("execution", {})
    default_cfg = execution.get("default", {})
    market_cfg = execution.get("market_costs", {}).get(market.lower(), {})

    fee_bps = float(market_cfg.get("fee_bps_per_side", default_cfg.get("fee_bps_per_side", 0.0)))
    slippage_bps = float(market_cfg.get("slippage_bps_per_side", default_cfg.get("slippage_bps_per_side", 0.0)))
    fee = fee_bps / 10000.0
    slippage = slippage_bps / 10000.0

    return {
        "fee_bps_per_side": fee_bps,
        "slippage_bps_per_side": slippage_bps,
        "fee_fraction": fee,
        "slippage_fraction": slippage,
        "per_side_cost_fraction": fee + slippage,
    }


def convert_csv_for_backtrader(src_csv: Path) -> Path:
    temp_fd, temp_path = tempfile.mkstemp(prefix="bt_parity_", suffix=".csv")
    Path(temp_path).unlink(missing_ok=True)
    try:
        import os
        os.close(temp_fd)
    except OSError:
        pass
    dst = Path(temp_path)

    with src_csv.open("r", encoding="utf-8") as src, dst.open("w", encoding="utf-8", newline="") as out:
        reader = csv.DictReader(src)
        writer = csv.writer(out)
        writer.writerow(["datetime", "open", "high", "low", "close"])
        for row in reader:
            ts_ms = int(float(row["timestamp"]))
            dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
            writer.writerow(
                [
                    dt.strftime("%Y-%m-%d %H:%M:%S"),
                    row["open"],
                    row["high"],
                    row["low"],
                    row["close"],
                ]
            )
    return dst


class EmaCrossAtrBTStrategy(bt.Strategy):
    params = (
        ("ema_fast", 20),
        ("ema_slow", 50),
        ("atr_period", 14),
        ("atr_mult_stop", 1.5),
        ("atr_mult_take", 2.0),
    )

    def __init__(self):
        self.ema_fast = bt.indicators.EMA(self.data.close, period=int(self.p.ema_fast))
        self.ema_slow = bt.indicators.EMA(self.data.close, period=int(self.p.ema_slow))
        self.cross = bt.indicators.CrossOver(self.ema_fast, self.ema_slow)
        self.atr = bt.indicators.ATR(self.data, period=int(self.p.atr_period))

        self.stop_price = None
        self.take_price = None
        self.current_trade = None
        self.trade_log = []

    def _open_trade(self, side: str):
        close = float(self.data.close[0])
        atr_v = float(self.atr[0]) if self.atr[0] else close * 0.005
        stop_dist = atr_v * float(self.p.atr_mult_stop)
        take_dist = atr_v * float(self.p.atr_mult_take)

        if side == "long":
            self.stop_price = close - stop_dist
            self.take_price = close + take_dist
        else:
            self.stop_price = close + stop_dist
            self.take_price = close - take_dist

        self.current_trade = {
            "entry_datetime": self.data.datetime.datetime(0, tz=timezone.utc).isoformat(),
            "side": side,
            "entry_price": round(close, 6),
            "stop_price": round(self.stop_price, 6),
            "take_price": round(self.take_price, 6),
        }

    def _close_trade(self, reason: str, exit_price: float):
        if not self.current_trade:
            return
        trade = dict(self.current_trade)
        trade["exit_datetime"] = self.data.datetime.datetime(0, tz=timezone.utc).isoformat()
        trade["exit_reason"] = reason
        trade["exit_price"] = round(float(exit_price), 6)
        self.trade_log.append(trade)
        self.current_trade = None
        self.stop_price = None
        self.take_price = None

    def next(self):
        close = float(self.data.close[0])
        high = float(self.data.high[0])
        low = float(self.data.low[0])

        if self.position.size > 0:
            if self.stop_price is not None and low <= self.stop_price:
                self.close()
                self._close_trade("stop_loss", self.stop_price)
                return
            if self.take_price is not None and high >= self.take_price:
                self.close()
                self._close_trade("take_profit", self.take_price)
                return
            if self.cross[0] < 0:
                self.close()
                self._close_trade("signal_flip", close)
                return

        elif self.position.size < 0:
            if self.stop_price is not None and high >= self.stop_price:
                self.close()
                self._close_trade("stop_loss", self.stop_price)
                return
            if self.take_price is not None and low <= self.take_price:
                self.close()
                self._close_trade("take_profit", self.take_price)
                return
            if self.cross[0] > 0:
                self.close()
                self._close_trade("signal_flip", close)
                return

        if not self.position:
            if self.cross[0] > 0:
                self.buy()
                self._open_trade("long")
            elif self.cross[0] < 0:
                self.sell()
                self._open_trade("short")


def run_backtrader_parity(csv_path: Path, params: dict, timeframe: str, cost_profile: dict) -> dict:
    prepared_csv = convert_csv_for_backtrader(csv_path)
    try:
        data = bt.feeds.GenericCSVData(
            dataname=str(prepared_csv),
            dtformat="%Y-%m-%d %H:%M:%S",
            datetime=0,
            open=1,
            high=2,
            low=3,
            close=4,
            volume=-1,
            openinterest=-1,
            headers=True,
            timeframe=bt.TimeFrame.Minutes,
            compression=60,
        )

        cerebro = bt.Cerebro(stdstats=False)
        cerebro.adddata(data)
        cerebro.broker.setcash(100000.0)
        cerebro.broker.set_coc(True)
        cerebro.broker.setcommission(commission=float(cost_profile["fee_fraction"]))
        cerebro.broker.set_slippage_perc(perc=float(cost_profile["slippage_fraction"]))

        cerebro.addsizer(bt.sizers.PercentSizer, percents=95)

        cerebro.addstrategy(
            EmaCrossAtrBTStrategy,
            ema_fast=int(params["ema_fast"]),
            ema_slow=int(params["ema_slow"]),
            atr_period=int(params.get("atr_period", 14)),
            atr_mult_stop=float(params["atr_mult_stop"]),
            atr_mult_take=float(params["atr_mult_take"]),
        )

        cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="timereturn")
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")

        strat = cerebro.run()[0]

        returns_series = list(strat.analyzers.timereturn.get_analysis().values())
        final_value = cerebro.broker.getvalue()
        total_return = ((final_value / 100000.0) - 1.0) * 100.0

        std = pstdev(returns_series) if len(returns_series) > 1 else 0.0
        sharpe = (
            (mean(returns_series) / std) * math.sqrt(bars_per_year(timeframe))
            if std > 0
            else 0.0
        )

        drawdown = strat.analyzers.drawdown.get_analysis()
        max_dd = float(drawdown.get("max", {}).get("drawdown", 0.0))

        trade_an = strat.analyzers.trades.get_analysis()
        total_closed = int(trade_an.get("total", {}).get("closed", 0) or 0)
        won = int(trade_an.get("won", {}).get("total", 0) or 0)
        win_rate = (won / total_closed * 100.0) if total_closed > 0 else 0.0

        return {
            "status": "ok",
            "metrics": {
                "total_return_pct": round(total_return, 2),
                "sharpe": round(sharpe, 2),
                "max_drawdown_pct": round(max_dd, 2),
                "oos_degradation_pct": round(oos_degradation_pct(returns_series), 2),
            },
            "details": {
                "trades_count": total_closed,
                "win_rate_pct": round(win_rate, 2),
                "trade_log_sample": strat.trade_log[:10],
                "trade_log_truncated": len(strat.trade_log) > 10,
            },
        }
    finally:
        prepared_csv.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", default="ema_cross_atr")
    parser.add_argument("--market", default="forex")
    parser.add_argument("--symbol", default="EURUSD")
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--iteration", type=int, default=1)
    args = parser.parse_args()

    universe, risk = load_configs()
    strategy = get_strategy(args.strategy)

    data_root = Path(universe.get("ingestion", {}).get("output_dir", "data/dukascopy"))
    if not data_root.is_absolute():
        data_root = ROOT / data_root

    sampled = strategy.sample_params(args.iteration)
    plan = build_param_plan(strategy.strategy_id, risk)
    params, optimization_meta = params_for_iteration(args.iteration, plan, sampled)

    engine_metrics, engine_details = run_real_backtest(
        strategy=strategy,
        params=params,
        data_root=data_root,
        markets_filter=[args.market],
        symbols_filter=[args.symbol],
        timeframes_filter=[args.timeframe],
        execution_cfg=risk.get("execution", {}),
    )

    if engine_details.get("status") != "ok":
        raise RuntimeError(f"Engine backtest failed: {engine_details}")

    dataset = Path(engine_details["dataset"])
    effective_params = engine_details.get("params_effective", params)
    cost_profile = resolve_cost_profile(risk, args.market)

    bt_result = run_backtrader_parity(
        csv_path=dataset,
        params=effective_params,
        timeframe=args.timeframe,
        cost_profile=cost_profile,
    )

    if bt_result.get("status") != "ok":
        raise RuntimeError(f"Backtrader run failed: {bt_result}")

    bt_metrics = bt_result["metrics"]
    comparison = {
        "delta_total_return_pct": round(bt_metrics["total_return_pct"] - engine_metrics.total_return_pct, 4),
        "delta_sharpe": round(bt_metrics["sharpe"] - engine_metrics.sharpe, 4),
        "delta_max_drawdown_pct": round(bt_metrics["max_drawdown_pct"] - engine_metrics.max_drawdown_pct, 4),
        "delta_oos_degradation_pct": round(
            bt_metrics["oos_degradation_pct"] - engine_metrics.oos_degradation_pct, 4
        ),
    }

    strict_thresholds = {
        "abs_delta_total_return_pct_max": 3.0,
        "abs_delta_sharpe_max": 2.0,
        "abs_delta_max_drawdown_pct_max": 3.0,
    }

    directional_thresholds = {
        "abs_delta_total_return_pct_max": 12.0,
        "abs_delta_max_drawdown_pct_max": 12.0,
        "min_trade_count_ratio": 0.75,
    }

    strict_parity_pass = (
        abs(comparison["delta_total_return_pct"]) <= strict_thresholds["abs_delta_total_return_pct_max"]
        and abs(comparison["delta_sharpe"]) <= strict_thresholds["abs_delta_sharpe_max"]
        and abs(comparison["delta_max_drawdown_pct"]) <= strict_thresholds["abs_delta_max_drawdown_pct_max"]
    )

    engine_return = float(engine_metrics.total_return_pct)
    bt_return = float(bt_metrics["total_return_pct"])
    same_return_direction = (engine_return == 0.0 and bt_return == 0.0) or (engine_return * bt_return > 0.0)

    engine_dd = float(engine_metrics.max_drawdown_pct)
    bt_dd = float(bt_metrics["max_drawdown_pct"])
    trade_count_engine = int(engine_details.get("trades_count", 0))
    trade_count_bt = int(bt_result.get("details", {}).get("trades_count", 0))
    trade_count_ratio = (trade_count_bt / trade_count_engine) if trade_count_engine > 0 else 0.0

    directional_parity_pass = (
        same_return_direction
        and abs(bt_return - engine_return) <= directional_thresholds["abs_delta_total_return_pct_max"]
        and abs(bt_dd - engine_dd) <= directional_thresholds["abs_delta_max_drawdown_pct_max"]
        and trade_count_ratio >= directional_thresholds["min_trade_count_ratio"]
    )

    payload = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "strategy_id": args.strategy,
        "market": args.market,
        "symbol": args.symbol,
        "timeframe": args.timeframe,
        "iteration": args.iteration,
        "optimization_mode": optimization_meta,
        "params_effective": effective_params,
        "dataset": str(dataset),
        "cost_profile": cost_profile,
        "engine": {
            "metrics": engine_metrics.__dict__,
            "details": {
                "trades_count": engine_details.get("trades_count", 0),
                "win_rate_pct": engine_details.get("win_rate_pct", 0.0),
            },
        },
        "backtrader": bt_result,
        "comparison": comparison,
        "thresholds": {
            "strict": strict_thresholds,
            "directional": directional_thresholds,
        },
        "parity": {
            "strict_pass": strict_parity_pass,
            "directional_pass": directional_parity_pass,
            "status": (
                "strict_pass"
                if strict_parity_pass
                else ("directional_pass" if directional_parity_pass else "fail")
            ),
            "trade_count_ratio": round(trade_count_ratio, 4),
            "same_return_direction": same_return_direction,
        },
    }

    out_dir = ROOT / "reports" / "parity"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"backtrader_parity_{stamp}.json"
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    print(f"[parity] report: {out_path}")
    print(
        f"[parity] status: {payload['parity']['status']} "
        f"(strict={strict_parity_pass}, directional={directional_parity_pass})"
    )


if __name__ == "__main__":
    main()
