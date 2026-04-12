"""Pairs trading strategy framework package."""

from .pair_identification import (
	CorrelationCandidate,
	PairAnalysisResult,
	PairIdentificationEngine,
	PairIdentificationReport,
)

__all__ = [
	"CorrelationCandidate",
	"PairAnalysisResult",
	"PairIdentificationEngine",
	"PairIdentificationReport",
]
