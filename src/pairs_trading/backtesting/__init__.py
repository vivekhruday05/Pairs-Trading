"""Backtest and P&L accounting for pair trading."""

from .engine import PairBacktestEngine
from .models import BacktestParameters, BacktestResult

__all__ = [
    "BacktestParameters",
    "BacktestResult",
    "PairBacktestEngine",
]
