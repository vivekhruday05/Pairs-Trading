from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class CorrelationCandidate:
    """Pair candidate produced by correlation screening."""

    symbol_x: str
    symbol_y: str
    correlation: float
    observations: int


@dataclass(frozen=True)
class PairAnalysisResult:
    """Statistical test output for a candidate pair."""

    symbol_x: str
    symbol_y: str
    observations: int
    correlation: float
    half_life: float | None
    engle_granger_stat: float
    engle_granger_pvalue: float
    adf_stat: float
    adf_pvalue: float
    adf_critical_values: dict[str, float]
    granger_xy_min_pvalue: float
    granger_yx_min_pvalue: float
    granger_xy_pvalues: dict[int, float]
    granger_yx_pvalues: dict[int, float]

    @property
    def strongest_granger_pvalue(self) -> float:
        """Smallest directional p-value across both Granger directions."""

        return min(self.granger_xy_min_pvalue, self.granger_yx_min_pvalue)


@dataclass(frozen=True)
class PairIdentificationReport:
    """Final output for one pair-identification run."""

    price_matrix: pd.DataFrame
    correlation_candidates: list[CorrelationCandidate]
    analyzed_pairs: list[PairAnalysisResult]

    def to_frame(self) -> pd.DataFrame:
        """Represent analyzed pairs as a sortable dataframe."""

        records: list[dict[str, float | str | int]] = []
        for row in self.analyzed_pairs:
            records.append(
                {
                    "symbol_x": row.symbol_x,
                    "symbol_y": row.symbol_y,
                    "observations": row.observations,
                    "correlation": row.correlation,
                    "half_life": row.half_life,
                    "engle_granger_stat": row.engle_granger_stat,
                    "engle_granger_pvalue": row.engle_granger_pvalue,
                    "adf_stat": row.adf_stat,
                    "adf_pvalue": row.adf_pvalue,
                    "granger_xy_min_pvalue": row.granger_xy_min_pvalue,
                    "granger_yx_min_pvalue": row.granger_yx_min_pvalue,
                    "strongest_granger_pvalue": row.strongest_granger_pvalue,
                }
            )

        if not records:
            return pd.DataFrame(
                columns=[
                    "symbol_x",
                    "symbol_y",
                    "observations",
                    "correlation",
                    "half_life",
                    "engle_granger_stat",
                    "engle_granger_pvalue",
                    "adf_stat",
                    "adf_pvalue",
                    "granger_xy_min_pvalue",
                    "granger_yx_min_pvalue",
                    "strongest_granger_pvalue",
                ]
            )

        return pd.DataFrame.from_records(records).sort_values(
            by=["engle_granger_pvalue", "adf_pvalue", "strongest_granger_pvalue"],
            ascending=[True, True, True],
        )
