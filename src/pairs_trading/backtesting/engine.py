from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from pairs_trading.signal_generation import PairSignalResult
from pairs_trading.risk_management import PairRiskEngine, RiskAdjustmentResult, RiskParameters

from .models import BacktestParameters, BacktestResult


@dataclass
class PairBacktestEngine:
    """Simulate transaction costs and P&L for a risk-adjusted pair strategy."""

    risk_engine: PairRiskEngine | None = None

    def __post_init__(self) -> None:
        self._risk_engine = self.risk_engine or PairRiskEngine()

    def run(
        self,
        *,
        signal_result: PairSignalResult,
        risk_parameters: RiskParameters | None = None,
        backtest_parameters: BacktestParameters | None = None,
    ) -> BacktestResult:
        """Apply risk controls, then compute transaction costs and P&L."""

        params = backtest_parameters or BacktestParameters()
        risk_result = self._risk_engine.apply_controls(
            signal_frame=signal_result.frame,
            symbol_x=signal_result.symbol_x,
            symbol_y=signal_result.symbol_y,
            parameters=risk_parameters,
        )
        frame = self._build_backtest_frame(
            risk_result=risk_result,
            signal_result=signal_result,
            backtest_parameters=params,
        )
        return BacktestResult(
            symbol_x=signal_result.symbol_x,
            symbol_y=signal_result.symbol_y,
            parameters=params,
            frame=frame,
        )

    def _build_backtest_frame(
        self,
        *,
        risk_result: RiskAdjustmentResult,
        signal_result: PairSignalResult,
        backtest_parameters: BacktestParameters,
    ) -> pd.DataFrame:
        frame = risk_result.frame.copy()
        symbol_x = signal_result.symbol_x
        symbol_y = signal_result.symbol_y

        price_x = frame[symbol_x].astype(float)
        price_y = frame[symbol_y].astype(float)
        adjusted_weight_x = frame["risk_weight_x"].astype(float)
        adjusted_weight_y = frame["risk_weight_y"].astype(float)

        delta_x = price_x.diff().fillna(0.0)
        delta_y = price_y.diff().fillna(0.0)
        
        prev_price_x = price_x.shift(1).fillna(price_x)
        prev_price_y = price_y.shift(1).fillna(price_y)
        
        # Avoid division by zero
        prev_price_x = prev_price_x.replace(0, 1e-8)
        prev_price_y = prev_price_y.replace(0, 1e-8)

        ret_x = delta_x / prev_price_x
        ret_y = delta_y / prev_price_y

        prev_weight_x = adjusted_weight_x.shift(1).fillna(0.0)
        prev_weight_y = adjusted_weight_y.shift(1).fillna(0.0)

        # Dollar allocation
        prev_alloc_x = prev_weight_x * backtest_parameters.initial_capital
        prev_alloc_y = prev_weight_y * backtest_parameters.initial_capital

        gross_pnl = prev_alloc_x * ret_x + prev_alloc_y * ret_y
        
        turnover_x = adjusted_weight_x.diff().abs().fillna(adjusted_weight_x.abs()) * backtest_parameters.initial_capital
        turnover_y = adjusted_weight_y.diff().abs().fillna(adjusted_weight_y.abs()) * backtest_parameters.initial_capital
        turnover = turnover_x + turnover_y
        transaction_cost = turnover * backtest_parameters.transaction_cost_rate
        net_pnl = gross_pnl - transaction_cost

        frame["delta_x"] = delta_x
        frame["delta_y"] = delta_y
        frame["gross_pnl"] = gross_pnl
        frame["turnover"] = turnover
        frame["transaction_cost"] = transaction_cost
        frame["net_pnl"] = net_pnl
        frame["cumulative_gross_pnl"] = gross_pnl.cumsum()
        frame["cumulative_net_pnl"] = net_pnl.cumsum()
        frame["equity_curve"] = backtest_parameters.initial_capital + frame["cumulative_net_pnl"]
        frame["active_trade"] = frame["risk_position"].ne(0)
        return frame
