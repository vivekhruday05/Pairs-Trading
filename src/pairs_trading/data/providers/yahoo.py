from __future__ import annotations

import importlib
from datetime import datetime

import pandas as pd

from .base import MarketDataProvider


class YahooFinanceProvider(MarketDataProvider):
    """Yahoo Finance adapter powered by yfinance."""

    name = "yahoo"

    def fetch_ohlcv(
        self,
        *,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str,
        adjusted: bool,
    ) -> pd.DataFrame:
        yf = importlib.import_module("yfinance")
        frame = yf.download(
            symbol,
            start=start,
            end=end,
            interval=interval,
            auto_adjust=adjusted,
            progress=False,
            actions=False,
        )
        if frame.empty:
            raise ValueError(f"No data returned by Yahoo Finance for {symbol}")

        frame.index = pd.to_datetime(frame.index, utc=True)
        frame = frame.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adj_close",
                "Volume": "volume",
            }
        )
        return frame.sort_index()
