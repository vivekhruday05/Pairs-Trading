from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class RiskParameters:
    """Risk-control configuration for an active pair trade."""

    stop_loss_fraction: float = 0.03
    max_holding_period: int = 20
    var_window: int = 30
    var_confidence: float = 0.95
    max_var_exposure: float = 0.02
    minimum_history: int = 5


@dataclass(frozen=True)
class RiskAdjustmentResult:
    """Result of applying risk controls to a signal table."""

    symbol_x: str
    symbol_y: str
    parameters: RiskParameters
    frame: pd.DataFrame

    def to_frame(self) -> pd.DataFrame:
        return self.frame.copy()
