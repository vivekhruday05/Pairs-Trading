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
        description="Download data and run pair identification across 10 instruments."
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=DEFAULT_SYMBOLS,
        help="Instrument symbols to analyze (default: 10 large-cap US equities).",
    )
    parser.add_argument(
        "--start",
        default="2020-01-01",
        help="Start date in YYYY-MM-DD format (default: 2020-01-01).",
    )
    parser.add_argument(
        "--end",
        default=datetime.utcnow().strftime("%Y-%m-%d"),
        help="End date in YYYY-MM-DD format (default: today UTC).",
    )
    parser.add_argument(
        "--interval",
        default="1d",
        help="Bar interval passed to providers (default: 1d).",
    )
    parser.add_argument(
        "--provider-preference",
        nargs="+",
        default=["yahoo", "stooq"],
        help="Ordered provider preference list.",
    )
    parser.add_argument(
        "--min-correlation",
        type=float,
        default=0.75,
        help="Absolute correlation threshold for baseline screening.",
    )
    parser.add_argument(
        "--min-observations",
        type=int,
        default=200,
        help="Minimum overlapping observations required per pair.",
    )
    parser.add_argument(
        "--granger-max-lag",
        type=int,
        default=5,
        help="Maximum lag for Granger causality tests.",
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force API refresh during download phase (ignore cache reads).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Top N analyzed pairs to print (default: 20).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="Optional path to save full analysis table as CSV.",
    )
    return parser.parse_args()


def _parse_yyyy_mm_dd(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def main() -> None:
    args = _parse_args()

    start = _parse_yyyy_mm_dd(args.start)
    end = _parse_yyyy_mm_dd(args.end)

    instruments = [Instrument(symbol=s.upper()) for s in args.symbols]

    print("=== Download phase ===")
    print(f"Symbols: {[i.symbol for i in instruments]}")
    print(
        f"Range: {start.date()} -> {end.date()} | interval={args.interval} | "
        f"providers={args.provider_preference}"
    )

    downloader = DataDownloader()
    snapshots = downloader.fetch_many(
        instruments=instruments,
        start=start,
        end=end,
        interval=args.interval,
        provider_preference=args.provider_preference,
        force_refresh=args.force_refresh,
    )

    for symbol in sorted(snapshots.keys()):
        snapshot = snapshots[symbol]
        print(
            f"{symbol:<6} provider={snapshot.provider:<6} "
            f"from_cache={str(snapshot.from_cache):<5} rows={len(snapshot.data)}"
        )

    print("\n=== Pair identification phase ===")
    engine = PairIdentificationEngine(downloader=downloader)

    report = engine.identify_pairs(
        instruments=instruments,
        start=start,
        end=end,
        interval=args.interval,
        provider_preference=args.provider_preference,
        force_refresh=False,
        min_correlation=args.min_correlation,
        min_observations=args.min_observations,
        granger_max_lag=args.granger_max_lag,
    )

    print(f"Correlation candidates: {len(report.correlation_candidates)}")
    print(f"Analyzed pairs: {len(report.analyzed_pairs)}")

    result_frame = report.to_frame()
    if result_frame.empty:
        print("No pairs passed the current thresholds.")
        return

    display_columns = [
        "symbol_x",
        "symbol_y",
        "observations",
        "correlation",
        "engle_granger_pvalue",
        "adf_pvalue",
        "granger_xy_min_pvalue",
        "granger_yx_min_pvalue",
        "strongest_granger_pvalue",
    ]

    top_n = max(args.top, 1)
    print(f"\nTop {top_n} pairs by statistical ranking:")
    print(result_frame[display_columns].head(top_n).to_string(index=False))

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result_frame.to_csv(output_path, index=False)
        print(f"\nSaved full pair table to: {output_path}")


if __name__ == "__main__":
    main()
