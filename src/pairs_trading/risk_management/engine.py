from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .models import RiskAdjustmentResult, RiskParameters


@dataclass
class PairRiskEngine:
    """Apply stop-loss, time-stop, and VaR exposure controls to pair signals."""

    def apply_controls(
        self,
        *,
        signal_frame: pd.DataFrame,
        symbol_x: str,
        symbol_y: str,
        parameters: RiskParameters | None = None,
    ) -> RiskAdjustmentResult:
        """Return a risk-adjusted frame with position gating and control flags."""

        params = parameters or RiskParameters()
        frame = self._validate_frame(signal_frame, symbol_x=symbol_x, symbol_y=symbol_y)

        risk_rows: list[dict[str, float | int | bool | str]] = []
        active_position = 0.0
        entry_gross_exposure = 0.0
        trade_pnl_since_entry = 0.0
        bars_held = 0
        pnl_history: list[float] = []
        prev_price_x = float(frame.iloc[0][symbol_x])
        prev_price_y = float(frame.iloc[0][symbol_y])
        prev_adj_weight_x = 0.0
        prev_adj_weight_y = 0.0

        for i, (_, row) in enumerate(frame.iterrows()):
            price_x = float(row[symbol_x])
            price_y = float(row[symbol_y])
            raw_position = float(row["position"])
            base_weight_x, base_weight_y = self._base_weights(row)

            step_pnl = 0.0
            if i > 0:
                ret_x = (price_x - prev_price_x) / prev_price_x if prev_price_x != 0 else 0.0
                ret_y = (price_y - prev_price_y) / prev_price_y if prev_price_y != 0 else 0.0
                step_pnl = prev_adj_weight_x * ret_x + prev_adj_weight_y * ret_y

            if active_position != 0.0:
                trade_pnl_since_entry += step_pnl
                bars_held += 1
                pnl_history.append(step_pnl)

            var_exposure = self._rolling_var_exposure(
                pnl_history=pnl_history,
                window=params.var_window,
                confidence=params.var_confidence,
                minimum_history=params.minimum_history,
            )

            desired_position = raw_position
            stop_loss_triggered = False
            time_stop_triggered = False
            var_limit_triggered = False

            if active_position != 0.0:
                # stop_loss_triggered is based on fraction of capital lost.
                # trade_pnl_since_entry is the cumulative return on capital for this trade.
                stop_loss_triggered = trade_pnl_since_entry <= -params.stop_loss_fraction
                time_stop_triggered = bars_held >= params.max_holding_period
                var_limit_triggered = var_exposure >= params.max_var_exposure

                if stop_loss_triggered or time_stop_triggered or var_limit_triggered or raw_position == 0.0:
                    desired_position = 0.0
                    active_position = 0.0
                    entry_gross_exposure = 0.0
                    trade_pnl_since_entry = 0.0
                    bars_held = 0
                    pnl_history = []
                else:
                    desired_position = active_position
            elif raw_position != 0.0:
                desired_position = raw_position
                active_position = raw_position
                entry_gross_exposure = float(abs(row.get("gross_exposure", 0.0)))
                trade_pnl_since_entry = 0.0
                bars_held = 0
                pnl_history = []

            adjusted_weight_x = base_weight_x * desired_position
            adjusted_weight_y = base_weight_y * desired_position
            adjusted_gross_exposure = abs(adjusted_weight_x) + abs(adjusted_weight_y)

            if stop_loss_triggered:
                risk_reason = "stop_loss"
            elif time_stop_triggered:
                risk_reason = "time_stop"
            elif var_limit_triggered:
                risk_reason = "var_limit"
            elif raw_position == 0.0 and active_position == 0.0 and i > 0 and prev_adj_weight_x != 0.0:
                risk_reason = "signal_exit"
            else:
                risk_reason = "active" if desired_position != 0.0 else "flat"

            risk_rows.append(
                {
                    "risk_position": desired_position,
                    "risk_weight_x": adjusted_weight_x,
                    "risk_weight_y": adjusted_weight_y,
                    "risk_gross_exposure": adjusted_gross_exposure,
                    "trade_pnl_since_entry": trade_pnl_since_entry,
                    "bars_held": bars_held,
                    "rolling_var_exposure": var_exposure,
                    "risk_reason": risk_reason,
                    "stop_loss_triggered": stop_loss_triggered,
                    "time_stop_triggered": time_stop_triggered,
                    "var_limit_triggered": var_limit_triggered,
                }
            )

            prev_price_x = price_x
            prev_price_y = price_y
            prev_adj_weight_x = adjusted_weight_x
            prev_adj_weight_y = adjusted_weight_y

        risk_frame = frame.copy()
        risk_frame = pd.concat([risk_frame, pd.DataFrame(risk_rows, index=frame.index)], axis=1)
        risk_frame["risk_reason"] = risk_frame["risk_reason"].astype(str)
        return RiskAdjustmentResult(
            symbol_x=symbol_x,
            symbol_y=symbol_y,
            parameters=params,
            frame=risk_frame,
        )

    @staticmethod
    def _validate_frame(signal_frame: pd.DataFrame, *, symbol_x: str, symbol_y: str) -> pd.DataFrame:
        required = {symbol_x, symbol_y, "position", "weight_x", "weight_y"}
        missing = [column for column in required if column not in signal_frame.columns]
        if missing:
            raise ValueError(f"Signal frame is missing required columns: {missing}")

        frame = signal_frame[[symbol_x, symbol_y, "position", "weight_x", "weight_y"]].copy()
        if "gross_exposure" not in signal_frame.columns:
            frame["gross_exposure"] = frame["weight_x"].abs() + frame["weight_y"].abs()
        else:
            frame["gross_exposure"] = signal_frame["gross_exposure"].copy()

        return frame.dropna(subset=[symbol_x, symbol_y])

    @staticmethod
    def _base_weights(row: pd.Series) -> tuple[float, float]:
        position = float(row["position"])
        if position == 0.0:
            return 0.0, 0.0

        weight_x = float(row["weight_x"]) / position
        weight_y = float(row["weight_y"]) / position
        return weight_x, weight_y

    @staticmethod
    def _rolling_var_exposure(
        *,
        pnl_history: list[float],
        window: int,
        confidence: float,
        minimum_history: int,
    ) -> float:
        if len(pnl_history) < minimum_history:
            return 0.0

        recent = pd.Series(pnl_history[-window:])
        var_level = float(abs(recent.quantile(1.0 - confidence)))
        if np.isnan(var_level):
            return 0.0
        return var_level
