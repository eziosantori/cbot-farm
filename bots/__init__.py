from typing import Dict

from bots.base import BaseBotStrategy
from bots.ema_cross_atr import EmaCrossAtrBot
from bots.supertrend_rsi import SuperTrendRsiBot


REGISTRY = {
    EmaCrossAtrBot.strategy_id: EmaCrossAtrBot,
    SuperTrendRsiBot.strategy_id: SuperTrendRsiBot,
}


def get_strategy(strategy_id: str) -> BaseBotStrategy:
    bot_cls = REGISTRY.get(strategy_id)
    if not bot_cls:
        available = ", ".join(sorted(REGISTRY.keys()))
        raise ValueError(f"Unknown strategy '{strategy_id}'. Available: {available}")
    return bot_cls()


def list_strategies() -> Dict[str, str]:
    return {sid: cls.display_name for sid, cls in REGISTRY.items()}
