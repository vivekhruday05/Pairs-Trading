from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class BacktestParameters:
    """Transaction-cost and capital assumptions for the backtest."""

    transaction_cost_rate: float = 0.0005
    initial_capital: float = 100000.0


@dataclass(frozen=True)
class BacktestResult:
    """Output of a backtest run."""

    symbol_x: str
    symbol_y: str
    parameters: BacktestParameters
    frame: pd.DataFrame

    def to_frame(self) -> pd.DataFrame:
        return self.frame.copy()

    def summary(self) -> dict[str, float]:
        frame = self.frame
        cumulative_net_pnl = float(frame["net_pnl"].sum())
        cumulative_gross_pnl = float(frame["gross_pnl"].sum())
        total_costs = float(frame["transaction_cost"].sum())
        equity_curve = frame["equity_curve"]
        running_max = equity_curve.cummax()
        max_drawdown = float((equity_curve - running_max).min())
        return {
            "cumulative_gross_pnl": cumulative_gross_pnl,
            "cumulative_net_pnl": cumulative_net_pnl,
            "total_costs": total_costs,
            "max_drawdown": max_drawdown,
            "ending_equity": float(equity_curve.iloc[-1]) if not equity_curve.empty else self.parameters.initial_capital,
        }
