from random import uniform

from .types import Metrics


def simulate_backtest() -> Metrics:
    # Temporary stub: replace with a real backtesting engine.
    return Metrics(
        total_return_pct=round(uniform(-2.0, 8.0), 2),
        sharpe=round(uniform(0.6, 1.8), 2),
        max_drawdown_pct=round(uniform(6.0, 16.0), 2),
        oos_degradation_pct=round(uniform(5.0, 45.0), 2),
    )
