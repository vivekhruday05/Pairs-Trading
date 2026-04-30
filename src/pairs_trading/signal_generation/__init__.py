"""Signal generation and position sizing for pairs trading."""

from .engine import PairSignalEngine
from .models import PairSignalResult, SignalParameters

__all__ = [
    "PairSignalEngine",
    "PairSignalResult",
    "SignalParameters",
]
