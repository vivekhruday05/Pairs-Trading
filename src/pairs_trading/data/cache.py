from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class CacheResult:
    """Cache read result that includes data and metadata for observability."""

    data: pd.DataFrame
    metadata: dict[str, Any]


class DiskCache:
    """Simple file-based cache for market data payloads."""

    def __init__(self, cache_dir: str | Path = ".cache/market_data") -> None:
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def build_key(
        self,
        *,
        provider: str,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str,
        adjusted: bool,
    ) -> str:
        raw_key = {
            "provider": provider.lower(),
            "symbol": symbol.upper(),
            "start": start.isoformat(),
            "end": end.isoformat(),
            "interval": interval,
            "adjusted": adjusted,
        }
        blob = json.dumps(raw_key, sort_keys=True).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    def get(self, key: str) -> CacheResult | None:
        data_path = self._cache_dir / f"{key}.pkl"
        meta_path = self._cache_dir / f"{key}.meta.json"
        if not data_path.exists() or not meta_path.exists():
            return None

        frame = pd.read_pickle(data_path)
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        return CacheResult(data=frame, metadata=metadata)

    def set(self, key: str, data: pd.DataFrame, metadata: dict[str, Any]) -> None:
        data_path = self._cache_dir / f"{key}.pkl"
        meta_path = self._cache_dir / f"{key}.meta.json"
        data.to_pickle(data_path)
        meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
