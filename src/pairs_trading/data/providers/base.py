from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd


class MarketDataProvider(ABC):
    """Provider interface for historical OHLCV downloads."""

    name: str

    @abstractmethod
    def fetch_ohlcv(
        self,
        *,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str,
        adjusted: bool,
    ) -> pd.DataFrame:
        """Return OHLCV data indexed by timestamp."""
