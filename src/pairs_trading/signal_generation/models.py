from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SignalParameters:
    """Threshold and sizing configuration for pair signals."""

    zscore_window: int = 20
    volatility_window: int = 20
    entry_threshold: float = 2.0
    exit_threshold: float = 0.5
    target_gross_exposure: float = 1.0
    minimum_volatility: float = 1e-8


@dataclass(frozen=True)
class PairSignalResult:
    """Output of the signal-generation pipeline for one pair."""

    symbol_x: str
    symbol_y: str
    hedge_ratio: float
    parameters: SignalParameters
    frame: pd.DataFrame

    def to_frame(self) -> pd.DataFrame:
        """Return a defensive copy of the underlying signal frame."""

        return self.frame.copy()
