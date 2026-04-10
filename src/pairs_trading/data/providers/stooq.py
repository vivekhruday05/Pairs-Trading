from __future__ import annotations

from datetime import datetime
from io import StringIO

import pandas as pd
import requests

from .base import MarketDataProvider


class StooqProvider(MarketDataProvider):
    """Stooq daily historical price adapter via CSV endpoint."""

    name = "stooq"

    def fetch_ohlcv(
        self,
        *,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str,
        adjusted: bool,
    ) -> pd.DataFrame:
        if interval != "1d":
            raise ValueError("Stooq provider currently supports only interval='1d'")

        url = f"https://stooq.com/q/d/l/?s={symbol.lower()}&i=d"
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        frame = pd.read_csv(StringIO(response.text))
        if frame.empty:
            raise ValueError(f"No data returned by Stooq for {symbol}")

        frame["Date"] = pd.to_datetime(frame["Date"], utc=True)
        mask = (frame["Date"] >= pd.Timestamp(start, tz="UTC")) & (
            frame["Date"] <= pd.Timestamp(end, tz="UTC")
        )
        frame = frame.loc[mask].copy()
        if frame.empty:
            raise ValueError(
                f"Stooq returned data for {symbol}, but not in requested range"
            )

        frame = frame.rename(
            columns={
                "Date": "timestamp",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )
        frame = frame.set_index("timestamp").sort_index()
        return frame
