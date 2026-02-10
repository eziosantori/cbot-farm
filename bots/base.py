from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class BaseBotStrategy(ABC):
    strategy_id: str = "base"
    display_name: str = "Base Strategy"

    @abstractmethod
    def sample_params(self, iteration: int) -> dict:
        """Return strategy parameters for this optimization iteration."""

    @abstractmethod
    def normalize_params(self, params: dict, bars_count: int) -> dict:
        """Adapt params to current dataset constraints."""

    @abstractmethod
    def prepare_indicators(self, bars: List[Dict[str, float]], params: dict) -> dict:
        """Precompute indicator series and return as a dict."""

    @abstractmethod
    def entry_signal(
        self,
        i: int,
        bars: List[Dict[str, float]],
        indicators: dict,
    ) -> int:
        """Return 1 (long), -1 (short), or 0 (no entry)."""

    @abstractmethod
    def should_flip(
        self,
        i: int,
        position: int,
        bars: List[Dict[str, float]],
        indicators: dict,
    ) -> bool:
        """Return True when current position should be exited due to signal flip."""

    @abstractmethod
    def risk_levels(
        self,
        i: int,
        side: int,
        entry_price: float,
        bars: List[Dict[str, float]],
        indicators: dict,
        params: dict,
    ) -> tuple[float, float]:
        """Return (stop_price, take_price) for the new position."""

    def default_trade_cost(self, market: Optional[str], timeframe: Optional[str]) -> float:
        """Per-side transaction cost (fractional), override for market-specific profiles."""
        return 0.0002
