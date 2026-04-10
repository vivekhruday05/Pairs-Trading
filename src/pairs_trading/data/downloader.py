from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable

from .cache import DiskCache
from .models import Instrument, MarketDataSnapshot
from .providers.base import MarketDataProvider
from .providers.stooq import StooqProvider
from .providers.yahoo import YahooFinanceProvider


@dataclass
class DataDownloader:
    """Facade for provider-based downloads with transparent disk caching."""

    cache: DiskCache = field(default_factory=DiskCache)
    providers: dict[str, MarketDataProvider] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.providers:
            self.providers = {
                "yahoo": YahooFinanceProvider(),
                "stooq": StooqProvider(),
            }

    def register_provider(self, provider: MarketDataProvider) -> None:
        """Register or override a provider by its canonical name."""

        self.providers[provider.name] = provider

    def fetch(
        self,
        *,
        instrument: Instrument,
        start: datetime,
        end: datetime,
        interval: str = "1d",
        adjusted: bool = True,
        provider_preference: Iterable[str] | None = None,
        force_refresh: bool = False,
    ) -> MarketDataSnapshot:
        ordered_providers = list(provider_preference or self.providers.keys())
        if not ordered_providers:
            raise ValueError("No providers configured for data download")

        errors: list[str] = []
        for provider_name in ordered_providers:
            provider = self.providers.get(provider_name)
            if provider is None:
                errors.append(f"Unknown provider: {provider_name}")
                continue

            cache_key = self.cache.build_key(
                provider=provider_name,
                symbol=instrument.symbol,
                start=start,
                end=end,
                interval=interval,
                adjusted=adjusted,
            )

            if not force_refresh:
                cached = self.cache.get(cache_key)
                if cached is not None:
                    return MarketDataSnapshot(
                        instrument=instrument,
                        data=cached.data,
                        provider=provider_name,
                        start=start,
                        end=end,
                        interval=interval,
                        from_cache=True,
                    )

            try:
                frame = provider.fetch_ohlcv(
                    symbol=instrument.symbol,
                    start=start,
                    end=end,
                    interval=interval,
                    adjusted=adjusted,
                )
            except Exception as exc:
                errors.append(f"{provider_name}: {exc}")
                continue

            self.cache.set(
                cache_key,
                frame,
                metadata={
                    "symbol": instrument.symbol,
                    "provider": provider_name,
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "interval": interval,
                    "adjusted": adjusted,
                },
            )
            return MarketDataSnapshot(
                instrument=instrument,
                data=frame,
                provider=provider_name,
                start=start,
                end=end,
                interval=interval,
                from_cache=False,
            )

        raise RuntimeError("Unable to fetch data from configured providers: " + "; ".join(errors))

    def fetch_many(
        self,
        *,
        instruments: Iterable[Instrument],
        start: datetime,
        end: datetime,
        interval: str = "1d",
        adjusted: bool = True,
        provider_preference: Iterable[str] | None = None,
        force_refresh: bool = False,
    ) -> dict[str, MarketDataSnapshot]:
        """Fetch multiple symbols with consistent parameters."""

        snapshots: dict[str, MarketDataSnapshot] = {}
        for instrument in instruments:
            snapshots[instrument.symbol] = self.fetch(
                instrument=instrument,
                start=start,
                end=end,
                interval=interval,
                adjusted=adjusted,
                provider_preference=provider_preference,
                force_refresh=force_refresh,
            )
        return snapshots
