from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from time import sleep
from typing import Iterable, Iterator

import pandas as pd

from .downloader import DataDownloader
from .models import Instrument, MarketDataSnapshot


@dataclass(frozen=True)
class StreamEvent:
    """Represents one polling cycle in the live data stream."""

    snapshot: MarketDataSnapshot
    new_rows: pd.DataFrame
    polled_at: datetime


class LiveDataStreamer:
    """Polling-based live stream built on top of configured market-data providers."""

    def __init__(self, downloader: DataDownloader | None = None) -> None:
        self._downloader = downloader or DataDownloader()

    def stream(
        self,
        *,
        instrument: Instrument,
        interval: str = "1m",
        lookback: timedelta = timedelta(days=5),
        poll_seconds: int = 15,
        adjusted: bool = True,
        provider_preference: Iterable[str] | None = None,
        max_polls: int | None = None,
    ) -> Iterator[StreamEvent]:
        """Yield new rows as they appear while continuously polling providers.

        Notes:
        - Uses `force_refresh=True` so each poll hits APIs instead of serving stale cache.
        - Each fresh API result is still written to cache by DataDownloader.
        """

        last_seen_timestamp: pd.Timestamp | None = None
        poll_count = 0

        while True:
            if max_polls is not None and poll_count >= max_polls:
                break

            poll_time = datetime.now(timezone.utc)
            start = poll_time - lookback

            snapshot = self._downloader.fetch(
                instrument=instrument,
                start=start,
                end=poll_time,
                interval=interval,
                adjusted=adjusted,
                provider_preference=provider_preference,
                force_refresh=True,
            )
            frame = snapshot.data.sort_index()

            if frame.empty:
                new_rows = frame
            elif last_seen_timestamp is None:
                new_rows = frame.tail(1)
                last_seen_timestamp = frame.index[-1]
            else:
                new_rows = frame.loc[frame.index > last_seen_timestamp]
                if not new_rows.empty:
                    last_seen_timestamp = new_rows.index[-1]

            yield StreamEvent(snapshot=snapshot, new_rows=new_rows, polled_at=poll_time)

            poll_count += 1
            sleep(poll_seconds)
