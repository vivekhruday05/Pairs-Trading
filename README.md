# Pairs-Trading

Pairs trading strategy framework with a modular architecture so each project phase can be integrated cleanly.

## Implemented so far

This repository now includes the **Week 1 data pipeline foundation** from the proposal:

- Historical market data downloader.
- Multi-provider support (`yahoo`, `stooq`) with provider fallback.
- File-based cache for repeatable and faster runs.
- Polling-based live stream layer built on top of the downloader.
- Shared domain models (`Instrument`, `MarketDataSnapshot`) to be reused by pair-identification, signal, risk, and backtest modules.

It also now includes the **pair identification engine** from the proposal:

- Correlation-based pair screening (baseline).
- Cointegration testing using Engle-Granger (`coint`) and ADF on spread residuals.
- Causal-relationship analysis using Granger causality tests.

## Project structure

```text
src/
  pairs_trading/
    data/
      cache.py            # Disk cache abstraction
      downloader.py       # Orchestrates providers + caching
      streaming.py        # Polling-based live stream API
      models.py           # Shared data contracts
      providers/
        base.py           # Provider interface
        yahoo.py          # Yahoo Finance adapter (yfinance)
        stooq.py          # Stooq CSV adapter
    pair_identification/
      engine.py           # Pair screening + statistical test pipeline
      models.py           # Result contracts for pair analysis
```

## Installation

From repository root:

```bash
pip install -r requirements.txt
```

The pair engine depends on `statsmodels` (already included in `requirements.txt`).

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

### 4) Live data stream (polling)

```python
from datetime import timedelta

from pairs_trading.data import Instrument, LiveDataStreamer

streamer = LiveDataStreamer()

for event in streamer.stream(
  instrument=Instrument(symbol="MSFT"),
  interval="1m",
  lookback=timedelta(days=2),
  poll_seconds=20,
  provider_preference=["yahoo", "stooq"],
  max_polls=10,
):
  if event.new_rows.empty:
    print(f"[{event.polled_at.isoformat()}] No new rows")
    continue

  print(f"[{event.polled_at.isoformat()}] New rows: {len(event.new_rows)}")
  print(event.new_rows.tail(1))
```

### 5) Identify candidate pairs

```python
from datetime import datetime

from pairs_trading.data import Instrument
from pairs_trading.pair_identification import PairIdentificationEngine

engine = PairIdentificationEngine()

instruments = [
    Instrument(symbol="MSFT"),
    Instrument(symbol="AAPL"),
    Instrument(symbol="GOOGL"),
    Instrument(symbol="AMZN"),
]

report = engine.identify_pairs(
    instruments=instruments,
    start=datetime(2020, 1, 1),
    end=datetime(2024, 1, 1),
    interval="1d",
    provider_preference=["yahoo", "stooq"],
    min_correlation=0.75,
    min_observations=200,
    granger_max_lag=5,
)

print("Correlation candidates:", len(report.correlation_candidates))
print(report.to_frame().head(10))
```

Live stream behavior:
- The streamer uses `force_refresh=True` internally, so each poll calls provider APIs.
- Even in live mode, successful API responses are still written into cache by `DataDownloader`.
- `event.new_rows` contains only unseen rows since the previous poll.

## Caching behavior

- Cache directory: `.cache/market_data/`
- Cache key dimensions: provider, symbol, start/end, interval, adjusted flag
- Stored files per query:
  - `<key>.pkl` (DataFrame payload)
  - `<key>.meta.json` (request metadata)

`.cache/` is already ignored by git.

## Data pipeline and cache flow

`DataDownloader.fetch(...)` follows this pipeline:

1. Build ordered provider list.
2. For each provider, build deterministic cache key from request params.
3. If `force_refresh=False`, try cache lookup first.
4. If cache hit: return cached snapshot immediately (`from_cache=True`), no API call.
5. If cache miss (or `force_refresh=True`): call provider API.
6. On successful API response: write payload + metadata to cache.
7. Return fresh snapshot (`from_cache=False`).
8. If provider fails, try next provider in preference order.
9. If all providers fail, raise error with provider-specific messages.

Decision summary:
- Historical/research workloads: default `force_refresh=False` to maximize cache reuse.
- Latency-sensitive/live workloads: `force_refresh=True` to avoid stale reads.

## Pair identification pipeline

`PairIdentificationEngine.identify_pairs(...)` follows this flow:

1. Fetch aligned price history for each `Instrument` through `DataDownloader`.
2. Build a shared price matrix indexed by timestamp.
3. Run correlation screening and keep pairs above `min_correlation`.
4. For each candidate pair, run Engle-Granger cointegration (`coint`).
5. Run ADF on OLS spread residuals to confirm mean-reversion tendency.
6. Run Granger causality in both directions up to `granger_max_lag`.
7. Return a `PairIdentificationReport` with pair-level statistics and a `to_frame()` helper.

## How to run pair identification

From repository root:

```bash
export PYTHONPATH=src
python - <<'PY'
from datetime import datetime

from pairs_trading.data import Instrument
from pairs_trading.pair_identification import PairIdentificationEngine

engine = PairIdentificationEngine()
report = engine.identify_pairs(
  instruments=[
    Instrument(symbol="MSFT"),
    Instrument(symbol="AAPL"),
    Instrument(symbol="GOOGL"),
    Instrument(symbol="AMZN"),
  ],
  start=datetime(2020, 1, 1),
  end=datetime(2024, 1, 1),
  interval="1d",
  provider_preference=["yahoo", "stooq"],
  min_correlation=0.75,
  min_observations=200,
  granger_max_lag=5,
)

print(report.to_frame().head(10))
PY
```

Tips:
- Increase `min_observations` for more stable statistical tests.
- Use higher `min_correlation` to reduce candidate count before expensive tests.
- Keep strategy modules decoupled by consuming this engine through `DataDownloader` only.

## Example script: 10 instruments end-to-end

An executable example is included at `examples/run_pair_identification.py`.
It performs both phases:

- Data download for 10 instruments using `DataDownloader.fetch_many(...)`.
- Pair identification using correlation screening, Engle-Granger + ADF, and Granger causality.

Run from repository root:

```bash
export PYTHONPATH=src
python examples/run_pair_identification.py
```

Optional arguments:

```bash
export PYTHONPATH=src
python examples/run_pair_identification.py \
  --start 2019-01-01 \
  --end 2024-12-31 \
  --min-correlation 0.8 \
  --min-observations 250 \
  --granger-max-lag 6 \
  --top 25 \
  --output outputs/pairs_top_table.csv
```

## Notes for future modules

- Use `Instrument` and `MarketDataSnapshot` as shared interfaces across modules.
- Keep strategy logic independent of provider specifics by using `DataDownloader` only.
- For new data sources, implement `MarketDataProvider` and register it via `DataDownloader.register_provider(...)`.

This keeps pair-selection, signal generation, and backtesting components decoupled from raw ingestion details.