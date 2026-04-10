# Pairs-Trading

Pairs trading strategy framework with a modular architecture so each project phase can be integrated cleanly.

## Implemented so far

This repository now includes the **Week 1 data pipeline foundation** from the proposal:

- Historical market data downloader.
- Multi-provider support (`yahoo`, `stooq`) with provider fallback.
- File-based cache for repeatable and faster runs.
- Shared domain models (`Instrument`, `MarketDataSnapshot`) to be reused by pair-identification, signal, risk, and backtest modules.

## Project structure

```text
src/
  pairs_trading/
    data/
      cache.py            # Disk cache abstraction
      downloader.py       # Orchestrates providers + caching
      models.py           # Shared data contracts
      providers/
        base.py           # Provider interface
        yahoo.py          # Yahoo Finance adapter (yfinance)
        stooq.py          # Stooq CSV adapter
```

## Installation

From repository root:

```bash
pip install -r requirements.txt
```

If you run scripts from the project root, set:

```bash
export PYTHONPATH=src
```

## Usage

### 1) Fetch one instrument

```python
from datetime import datetime

from pairs_trading.data import DataDownloader, Instrument

downloader = DataDownloader()

snapshot = downloader.fetch(
    instrument=Instrument(symbol="MSFT"),
    start=datetime(2022, 1, 1),
    end=datetime(2023, 1, 1),
    interval="1d",
    provider_preference=["yahoo", "stooq"],
)

print(snapshot.provider)
print(snapshot.from_cache)
print(snapshot.data.head())
```

### 2) Fetch a basket (for pair screening)

```python
from datetime import datetime

from pairs_trading.data import DataDownloader, Instrument

downloader = DataDownloader()
instruments = [Instrument(symbol="MSFT"), Instrument(symbol="AAPL")]

all_data = downloader.fetch_many(
    instruments=instruments,
    start=datetime(2022, 1, 1),
    end=datetime(2023, 1, 1),
)

msft_frame = all_data["MSFT"].data
aapl_frame = all_data["AAPL"].data
```

### 3) Force refresh instead of cache

```python
snapshot = downloader.fetch(
    instrument=Instrument(symbol="MSFT"),
    start=datetime(2022, 1, 1),
    end=datetime(2023, 1, 1),
    force_refresh=True,
)
```

## Caching behavior

- Cache directory: `.cache/market_data/`
- Cache key dimensions: provider, symbol, start/end, interval, adjusted flag
- Stored files per query:
  - `<key>.pkl` (DataFrame payload)
  - `<key>.meta.json` (request metadata)

`.cache/` is already ignored by git.

## Notes for future modules

- Use `Instrument` and `MarketDataSnapshot` as shared interfaces across modules.
- Keep strategy logic independent of provider specifics by using `DataDownloader` only.
- For new data sources, implement `MarketDataProvider` and register it via `DataDownloader.register_provider(...)`.

This keeps pair-selection, signal generation, and backtesting components decoupled from raw ingestion details.