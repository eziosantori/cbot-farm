from .types import Metrics


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
