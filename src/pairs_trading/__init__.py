"""Pairs trading strategy framework package."""

from .pair_identification import (
	CorrelationCandidate,
	PairAnalysisResult,
	PairIdentificationEngine,
	PairIdentificationReport,
)
from .backtesting import BacktestParameters, BacktestResult, PairBacktestEngine
from .risk_management import PairRiskEngine, RiskAdjustmentResult, RiskParameters
from .signal_generation import PairSignalEngine, PairSignalResult, SignalParameters

__all__ = [
	"CorrelationCandidate",
	"BacktestParameters",
	"BacktestResult",
	"PairAnalysisResult",
	"PairIdentificationEngine",
	"PairIdentificationReport",
	"PairBacktestEngine",
	"PairRiskEngine",
	"RiskAdjustmentResult",
	"RiskParameters",
	"PairSignalEngine",
	"PairSignalResult",
	"SignalParameters",
]
