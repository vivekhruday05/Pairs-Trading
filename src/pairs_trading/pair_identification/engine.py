from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from itertools import combinations
from typing import Iterable
import warnings

import pandas as pd
import numpy as np

from pairs_trading.data import DataDownloader, Instrument

from .models import CorrelationCandidate, PairAnalysisResult, PairIdentificationReport


@dataclass
class PairIdentificationEngine:
    """Identify candidate pairs using correlation, cointegration, and causality tests."""

    downloader: DataDownloader | None = None

    def __post_init__(self) -> None:
        self._downloader = self.downloader or DataDownloader()

    def build_price_matrix(
        self,
        *,
        instruments: Iterable[Instrument],
        start: datetime,
        end: datetime,
        interval: str = "1d",
        adjusted: bool = True,
        price_column: str = "close",
        provider_preference: Iterable[str] | None = None,
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        """Fetch instrument history and align selected price columns into one matrix."""

        snapshots = self._downloader.fetch_many(
            instruments=instruments,
            start=start,
            end=end,
            interval=interval,
            adjusted=adjusted,
            provider_preference=provider_preference,
            force_refresh=force_refresh,
        )

        series_by_symbol: dict[str, pd.Series] = {}
        for symbol, snapshot in snapshots.items():
            resolved_column = self._resolve_price_column(snapshot.data, preferred=price_column)
            selected = snapshot.data.loc[:, resolved_column]

            # Some providers can surface duplicate column labels or MultiIndex slices,
            # which yields a DataFrame for a single logical field. Normalize to Series.
            if isinstance(selected, pd.DataFrame):
                selected = selected.iloc[:, 0]

            series = pd.to_numeric(selected, errors="coerce").rename(symbol).sort_index()
            series_by_symbol[symbol] = series

        if not series_by_symbol:
            return pd.DataFrame()

        matrix = pd.concat(series_by_symbol.values(), axis=1)
        matrix = matrix.sort_index()
        return matrix

    def correlation_screen(
        self,
        *,
        price_matrix: pd.DataFrame,
        min_correlation: float = 0.8,
        min_observations: int = 120,
        method: str = "pearson",
    ) -> list[CorrelationCandidate]:
        """Return pairs with absolute correlation above threshold."""

        if price_matrix.empty:
            return []

        candidates: list[CorrelationCandidate] = []
        symbols = list(price_matrix.columns)

        for symbol_x, symbol_y in combinations(symbols, 2):
            pair = price_matrix[[symbol_x, symbol_y]].dropna()
            if len(pair) < min_observations:
                continue

            corr_value = pair[symbol_x].corr(pair[symbol_y], method=method)
            if pd.isna(corr_value):
                continue

            if abs(corr_value) >= min_correlation:
                candidates.append(
                    CorrelationCandidate(
                        symbol_x=symbol_x,
                        symbol_y=symbol_y,
                        correlation=float(corr_value),
                        observations=len(pair),
                    )
                )

        return sorted(candidates, key=lambda c: abs(c.correlation), reverse=True)

    def identify_pairs(
        self,
        *,
        instruments: Iterable[Instrument],
        start: datetime,
        end: datetime,
        interval: str = "1d",
        adjusted: bool = True,
        provider_preference: Iterable[str] | None = None,
        force_refresh: bool = False,
        price_column: str = "close",
        min_correlation: float = 0.8,
        min_observations: int = 120,
        granger_max_lag: int = 5,
    ) -> PairIdentificationReport:
        """Run full candidate-discovery pipeline and return statistical test results."""

        price_matrix = self.build_price_matrix(
            instruments=instruments,
            start=start,
            end=end,
            interval=interval,
            adjusted=adjusted,
            provider_preference=provider_preference,
            force_refresh=force_refresh,
            price_column=price_column,
        )

        candidates = self.correlation_screen(
            price_matrix=price_matrix,
            min_correlation=min_correlation,
            min_observations=min_observations,
        )

        analyzed: list[PairAnalysisResult] = []
        min_required = max(min_observations, granger_max_lag + 5)

        for candidate in candidates:
            pair = price_matrix[[candidate.symbol_x, candidate.symbol_y]].dropna()
            if len(pair) < min_required:
                continue

            analyzed.append(
                self._analyze_pair(
                    pair=pair,
                    symbol_x=candidate.symbol_x,
                    symbol_y=candidate.symbol_y,
                    correlation=candidate.correlation,
                    granger_max_lag=granger_max_lag,
                )
            )

        return PairIdentificationReport(
            price_matrix=price_matrix,
            correlation_candidates=candidates,
            analyzed_pairs=analyzed,
        )

    def _analyze_pair(
        self,
        *,
        pair: pd.DataFrame,
        symbol_x: str,
        symbol_y: str,
        correlation: float,
        granger_max_lag: int,
    ) -> PairAnalysisResult:
        """Compute Engle-Granger cointegration, ADF residual test, and Granger tests."""

        stattools = self._get_stattools()
        sm_api = self._get_statsmodels_api()

        x = pair[symbol_x]
        y = pair[symbol_y]

        x_with_const = sm_api.add_constant(x)
        ols_result = sm_api.OLS(y, x_with_const).fit()
        residuals = ols_result.resid

        coint_stat, coint_pvalue, _ = stattools.coint(y, x)
        adf_stat, adf_pvalue, _, _, adf_critical_values, _ = stattools.adfuller(
            residuals,
            autolag="AIC",
        )

        # Calculate half-life of mean reversion
        delta_resid = residuals.diff().dropna()
        prev_resid = residuals.shift().dropna()
        lambda_result = sm_api.OLS(delta_resid, prev_resid).fit()
        lambda_coeff = lambda_result.params.iloc[0]
        
        if lambda_coeff < 0:
            half_life = -np.log(2) / lambda_coeff
        else:
            half_life = None

        granger_xy = self._granger_min_pvalue(
            pair=pair,
            target=symbol_y,
            cause=symbol_x,
            max_lag=granger_max_lag,
        )
        granger_yx = self._granger_min_pvalue(
            pair=pair,
            target=symbol_x,
            cause=symbol_y,
            max_lag=granger_max_lag,
        )

        return PairAnalysisResult(
            symbol_x=symbol_x,
            symbol_y=symbol_y,
            observations=len(pair),
            correlation=correlation,
            half_life=half_life if half_life is not None else float('nan'),
            engle_granger_stat=float(coint_stat),
            engle_granger_pvalue=float(coint_pvalue),
            adf_stat=float(adf_stat),
            adf_pvalue=float(adf_pvalue),
            adf_critical_values={str(k): float(v) for k, v in adf_critical_values.items()},
            granger_xy_min_pvalue=float(min(granger_xy.values())),
            granger_yx_min_pvalue=float(min(granger_yx.values())),
            granger_xy_pvalues=granger_xy,
            granger_yx_pvalues=granger_yx,
        )

    def _granger_min_pvalue(
        self,
        *,
        pair: pd.DataFrame,
        target: str,
        cause: str,
        max_lag: int,
    ) -> dict[int, float]:
        stattools = self._get_stattools()

        test_input = pair[[target, cause]]
        # statsmodels keeps `verbose` but warns about deprecation in newer versions.
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="verbose is deprecated",
                category=FutureWarning,
            )
            output = stattools.grangercausalitytests(test_input, maxlag=max_lag, verbose=False)

        pvalues: dict[int, float] = {}
        for lag, results in output.items():
            pvalues[int(lag)] = float(results[0]["ssr_ftest"][1])

        return pvalues

    @staticmethod
    def _resolve_price_column(frame: pd.DataFrame, preferred: str) -> str:
        if preferred in frame.columns:
            return preferred

        fallback_order = {
            "close": ["adj_close", "open", "high", "low"],
            "adj_close": ["close", "open", "high", "low"],
        }

        for column in fallback_order.get(preferred, []):
            if column in frame.columns:
                return column

        for column in ["close", "adj_close", "open", "high", "low"]:
            if column in frame.columns:
                return column

        raise ValueError(
            f"Unable to find a usable price column for preferred='{preferred}'. "
            f"Available columns: {list(frame.columns)}"
        )

    @staticmethod
    def _get_stattools():
        try:
            from statsmodels.tsa import stattools  # pylint: disable=import-outside-toplevel
        except ImportError as exc:  # pragma: no cover - dependency issue
            raise ImportError(
                "statsmodels is required for pair identification. "
                "Install dependencies with: pip install -r requirements.txt"
            ) from exc

        return stattools

    @staticmethod
    def _get_statsmodels_api():
        try:
            import statsmodels.api as sm_api  # pylint: disable=import-outside-toplevel
        except ImportError as exc:  # pragma: no cover - dependency issue
            raise ImportError(
                "statsmodels is required for pair identification. "
                "Install dependencies with: pip install -r requirements.txt"
            ) from exc

        return sm_api
