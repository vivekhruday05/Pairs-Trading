from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd


@dataclass(frozen=True)
class Instrument:
    """Tradable instrument descriptor used across the project."""

    symbol: str
    exchange: str | None = None
    asset_class: str = "equity"
    currency: str | None = None


@dataclass(frozen=True)
class MarketDataSnapshot:
    """Container for time-series data and provenance metadata."""

    instrument: Instrument
    data: pd.DataFrame
    provider: str
    start: datetime
    end: datetime
    interval: str
    from_cache: bool = False
