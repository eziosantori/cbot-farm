from dataclasses import dataclass


@dataclass
class Metrics:
    total_return_pct: float
    sharpe: float
    max_drawdown_pct: float
    oos_degradation_pct: float
