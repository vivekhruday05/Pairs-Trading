from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from pairs_trading.data import DataDownloader, Instrument
from pairs_trading.pair_identification import PairIdentificationEngine
from pairs_trading.signal_generation import PairSignalEngine, SignalParameters

DEFAULT_SYMBOLS = [
    "MSFT",
    "AAPL",
    "GOOGL",
    "AMZN",
    "META",
    "NVDA",
    "ORCL",
    "IBM",
    "INTC",
    "CSCO",
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download data, identify a pair, and generate signals plus position sizing."
    )
    parser.add_argument("--symbols", nargs="+", default=DEFAULT_SYMBOLS)
    parser.add_argument("--start", default="2020-01-01")
    parser.add_argument("--end", default=datetime.utcnow().strftime("%Y-%m-%d"))
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--provider-preference", nargs="+", default=["yahoo", "stooq"])
    parser.add_argument("--min-correlation", type=float, default=0.75)
    parser.add_argument("--min-observations", type=int, default=200)
    parser.add_argument("--granger-max-lag", type=int, default=5)
    parser.add_argument("--zscore-window", type=int, default=20)
    parser.add_argument("--volatility-window", type=int, default=20)
    parser.add_argument("--entry-threshold", type=float, default=2.0)
    parser.add_argument("--exit-threshold", type=float, default=0.5)
    parser.add_argument("--target-gross-exposure", type=float, default=1.0)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--output", type=str, default="")
    return parser.parse_args()


def _parse_yyyy_mm_dd(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def main() -> None:
    args = _parse_args()
    start = _parse_yyyy_mm_dd(args.start)
    end = _parse_yyyy_mm_dd(args.end)
    instruments = [Instrument(symbol=s.upper()) for s in args.symbols]

    print("=== Download phase ===")
    downloader = DataDownloader()
    snapshots = downloader.fetch_many(
        instruments=instruments,
        start=start,
        end=end,
        interval=args.interval,
        provider_preference=args.provider_preference,
    )

    for symbol in sorted(snapshots.keys()):
        snapshot = snapshots[symbol]
        print(
            f"{symbol:<6} provider={snapshot.provider:<6} "
            f"from_cache={str(snapshot.from_cache):<5} rows={len(snapshot.data)}"
        )

    print("\n=== Pair identification phase ===")
    pair_engine = PairIdentificationEngine(downloader=downloader)
    report = pair_engine.identify_pairs(
        instruments=instruments,
        start=start,
        end=end,
        interval=args.interval,
        provider_preference=args.provider_preference,
        min_correlation=args.min_correlation,
        min_observations=args.min_observations,
        granger_max_lag=args.granger_max_lag,
    )

    pairs_frame = report.to_frame()
    if pairs_frame.empty:
        print("No candidate pairs passed the screening rules.")
        return

    top_pair = pairs_frame.iloc[0]
    symbol_x = str(top_pair["symbol_x"])
    symbol_y = str(top_pair["symbol_y"])
    print(f"Selected pair: {symbol_x} / {symbol_y}")

    print("\n=== Signal generation phase ===")
    signal_engine = PairSignalEngine()
    params = SignalParameters(
        zscore_window=args.zscore_window,
        volatility_window=args.volatility_window,
        entry_threshold=args.entry_threshold,
        exit_threshold=args.exit_threshold,
        target_gross_exposure=args.target_gross_exposure,
    )

    signal_result = signal_engine.generate_for_pair(
        price_frame=report.price_matrix,
        symbol_x=symbol_x,
        symbol_y=symbol_y,
        parameters=params,
    )

    frame = signal_result.to_frame()
    display_columns = [
        symbol_x,
        symbol_y,
        "spread",
        "zscore",
        "raw_signal",
        "position",
        "rolling_volatility",
        "inverse_vol_scale",
        "weight_x",
        "weight_y",
        "gross_exposure",
    ]

    print(frame[display_columns].tail(args.top).to_string())

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(output_path, index=True)
        print(f"\nSaved signal table to: {output_path}")


if __name__ == "__main__":
    main()
