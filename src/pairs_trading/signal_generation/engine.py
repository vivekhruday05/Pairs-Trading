from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd

from pairs_trading.pair_identification import PairIdentificationReport

from .models import PairSignalResult, SignalParameters


@dataclass
class PairSignalEngine:
    """Generate z-score signals and inverse-volatility position sizes for a pair."""

    def generate_for_pair(
        self,
        *,
        price_frame: pd.DataFrame,
        symbol_x: str,
        symbol_y: str,
        hedge_ratio: float | None = None,
        parameters: SignalParameters | None = None,
    ) -> PairSignalResult:
        """Build the full signal table for one pair."""

        params = parameters or SignalParameters()
        pair = self._prepare_pair_frame(price_frame, symbol_x=symbol_x, symbol_y=symbol_y)

        if hedge_ratio is None:
            hedge_ratio = self._estimate_hedge_ratio(pair, symbol_x=symbol_x, symbol_y=symbol_y)

        frame = self._build_signal_frame(
            pair=pair,
            symbol_x=symbol_x,
            symbol_y=symbol_y,
            hedge_ratio=hedge_ratio,
            parameters=params,
        )

        return PairSignalResult(
            symbol_x=symbol_x,
            symbol_y=symbol_y,
            hedge_ratio=float(hedge_ratio),
            parameters=params,
            frame=frame,
        )

    def generate_from_report(
        self,
        *,
        report: PairIdentificationReport,
        pair: tuple[str, str] | None = None,
        parameters: SignalParameters | None = None,
    ) -> PairSignalResult:
        """Convenience wrapper that picks a pair from a pair-identification report."""

        if report.price_matrix.empty:
            raise ValueError("Pair identification report has no price data")

        if pair is None:
            ranked = report.to_frame()
            if ranked.empty:
                raise ValueError("Pair identification report has no analyzed pairs to trade")
            symbol_x = str(ranked.iloc[0]["symbol_x"])
            symbol_y = str(ranked.iloc[0]["symbol_y"])
        else:
            symbol_x, symbol_y = pair

        return self.generate_for_pair(
            price_frame=report.price_matrix,
            symbol_x=symbol_x,
            symbol_y=symbol_y,
            parameters=parameters,
        )

    def build_signal_matrix(
        self,
        *,
        price_frame: pd.DataFrame,
        pairs: Iterable[tuple[str, str]],
        parameters: SignalParameters | None = None,
    ) -> dict[tuple[str, str], PairSignalResult]:
        """Generate signals for multiple pairs."""

        results: dict[tuple[str, str], PairSignalResult] = {}
        for symbol_x, symbol_y in pairs:
            results[(symbol_x, symbol_y)] = self.generate_for_pair(
                price_frame=price_frame,
                symbol_x=symbol_x,
                symbol_y=symbol_y,
                parameters=parameters,
            )
        return results

    @staticmethod
    def _prepare_pair_frame(
        price_frame: pd.DataFrame,
        *,
        symbol_x: str,
        symbol_y: str,
    ) -> pd.DataFrame:
        if symbol_x not in price_frame.columns or symbol_y not in price_frame.columns:
            missing = [symbol for symbol in (symbol_x, symbol_y) if symbol not in price_frame.columns]
            raise ValueError(f"Missing columns in price frame: {missing}")

        pair = price_frame[[symbol_x, symbol_y]].dropna().copy()
        if pair.empty:
            raise ValueError("No overlapping price history for the selected pair")

        pair.columns = [symbol_x, symbol_y]
        return pair

    @staticmethod
    def _estimate_hedge_ratio(
        pair: pd.DataFrame,
        *,
        symbol_x: str,
        symbol_y: str,
    ) -> float:
        sm_api = PairSignalEngine._get_statsmodels_api()
        x = pair[symbol_x]
        y = pair[symbol_y]
        x_with_const = sm_api.add_constant(x)
        result = sm_api.OLS(y, x_with_const).fit()
        slope = result.params.iloc[-1]
        return float(slope)

    def _build_signal_frame(
        self,
        *,
        pair: pd.DataFrame,
        symbol_x: str,
        symbol_y: str,
        hedge_ratio: float,
        parameters: SignalParameters,
    ) -> pd.DataFrame:
        spread = pair[symbol_y] - hedge_ratio * pair[symbol_x]
        rolling_mean = spread.rolling(window=parameters.zscore_window, min_periods=parameters.zscore_window).mean()
        rolling_std = spread.rolling(window=parameters.zscore_window, min_periods=parameters.zscore_window).std(ddof=0)
        zscore = (spread - rolling_mean) / rolling_std.replace(0, pd.NA)

        spread_change = spread.diff()
        rolling_vol = spread_change.rolling(
            window=parameters.volatility_window,
            min_periods=parameters.volatility_window,
        ).std(ddof=0)
        rolling_vol = rolling_vol.clip(lower=parameters.minimum_volatility)
        inverse_vol_scale = parameters.target_gross_exposure / rolling_vol

        raw_signal = self._generate_raw_signal(
            zscore=zscore,
            entry_threshold=parameters.entry_threshold,
            exit_threshold=parameters.exit_threshold,
        )

        position = raw_signal.astype(float)

        position_scale = inverse_vol_scale.fillna(0)
        position_scale = position_scale.clip(upper=parameters.max_gross_exposure)
        normalized_scale = position_scale / (1.0 + hedge_ratio.__abs__())

        weight_y = position * normalized_scale
        weight_x = -position * hedge_ratio * normalized_scale
        gross_exposure = weight_x.abs() + weight_y.abs()

        frame = pd.DataFrame(
            {
                symbol_x: pair[symbol_x],
                symbol_y: pair[symbol_y],
                "hedge_ratio": hedge_ratio,
                "spread": spread,
                "rolling_mean": rolling_mean,
                "rolling_std": rolling_std,
                "zscore": zscore,
                "raw_signal": raw_signal,
                "position": position,
                "spread_change": spread_change,
                "rolling_volatility": rolling_vol,
                "inverse_vol_scale": inverse_vol_scale,
                "weight_x": weight_x,
                "weight_y": weight_y,
                "gross_exposure": gross_exposure,
            },
            index=pair.index,
        )
        return frame

    @staticmethod
    def _generate_raw_signal(
        *,
        zscore: pd.Series,
        entry_threshold: float,
        exit_threshold: float,
    ) -> pd.Series:
        signals: list[float] = []
        position = 0.0

        for value in zscore.tolist():
            if pd.isna(value):
                signals.append(0.0)
                continue

            if position == 0.0:
                if value >= entry_threshold:
                    position = -1.0
                elif value <= -entry_threshold:
                    position = 1.0
            elif position > 0.0 and value >= -exit_threshold:
                position = 0.0
            elif position < 0.0 and value <= exit_threshold:
                position = 0.0

            signals.append(position)

        return pd.Series(signals, index=zscore.index, name="raw_signal")

    @staticmethod
    def _get_statsmodels_api():
        try:
            import statsmodels.api as sm_api  # pylint: disable=import-outside-toplevel
        except ImportError as exc:  # pragma: no cover - dependency issue
            raise ImportError(
                "statsmodels is required for pair signal generation. "
                "Install dependencies with: pip install -r requirements.txt"
            ) from exc

        return sm_api
