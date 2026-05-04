import unittest
import pandas as pd
import numpy as np

from pairs_trading.signal_generation import PairSignalEngine, SignalParameters
from pairs_trading.risk_management import PairRiskEngine, RiskParameters

class TestInvariants(unittest.TestCase):

    def setUp(self):
        np.random.seed(42)
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        
        # Coin-integrated-like series
        x = np.cumsum(np.random.normal(0, 1, 100)) + 100
        y = x * 1.5 + np.random.normal(0, 0.5, 100)
        
        # Introduce some spread divergence to trigger signals
        y[50:60] += 5.0
        y[80:90] -= 5.0
        
        self.dummy_price_data = pd.DataFrame({"A": x, "B": y}, index=dates)

    def test_weights_balance_out(self):
        """Ensure that the short and long exposures balance out properly based on hedge ratio."""
        engine = PairSignalEngine()
        params = SignalParameters(
            zscore_window=10, 
            volatility_window=10, 
            entry_threshold=1.0, 
            exit_threshold=0.0
        )
        
        result = engine.generate_for_pair(
            price_frame=self.dummy_price_data,
            symbol_x="A",
            symbol_y="B",
            parameters=params
        )
        
        df = result.frame
        
        # Drop rows where there's no position
        active_df = df[df["position"] != 0].copy()
        
        if len(active_df) == 0:
            self.skipTest("No signals generated, cannot test invariants.")
            
        hedge_ratio = result.hedge_ratio
        
        for _, row in active_df.iterrows():
            wx = row["weight_x"]
            wy = row["weight_y"]
            # Ensure they have opposite signs (if hedge ratio is positive)
            if hedge_ratio > 0:
                self.assertTrue(wx * wy <= 0, f"Weights should be opposite: {wx}, {wy}")
            
            # Ensure they balance out according to hedge ratio
            # wy is proportional to 1, wx is proportional to -hedge_ratio
            # So wy * -hedge_ratio should equal wx roughly
            np.testing.assert_almost_equal(wy * -hedge_ratio, wx, decimal=4)

    def test_max_leverage_invariant(self):
        """Ensure that weights never exceed the maximum configured leverage/exposure."""
        engine = PairSignalEngine()
        params = SignalParameters(
            zscore_window=10, 
            volatility_window=10, 
            target_gross_exposure=1.0,
            entry_threshold=1.0, 
            exit_threshold=0.0
        )
        
        result = engine.generate_for_pair(
            price_frame=self.dummy_price_data,
            symbol_x="A",
            symbol_y="B",
            parameters=params
        )
        
        df = result.frame
        max_gross_exposure = df["gross_exposure"].max()
        self.assertLessEqual(max_gross_exposure, params.max_gross_exposure + 1e-4)

    def test_risk_management_exposure_limits(self):
        """Ensure risk engine controls also don't exceed max exposure."""
        signal_engine = PairSignalEngine()
        signal_params = SignalParameters(
            zscore_window=10, 
            volatility_window=10, 
            target_gross_exposure=2.0,
            entry_threshold=1.0, 
            exit_threshold=0.0
        )
        
        signal_result = signal_engine.generate_for_pair(
            price_frame=self.dummy_price_data,
            symbol_x="A",
            symbol_y="B",
            parameters=signal_params
        )
        
        risk_engine = PairRiskEngine()
        risk_params = RiskParameters(
            stop_loss_fraction=0.01,
            max_holding_period=5
        )
        
        risk_result = risk_engine.apply_controls(
            signal_frame=signal_result.frame,
            symbol_x="A",
            symbol_y="B",
            parameters=risk_params
        )
        
        df = risk_result.frame
        max_risk_gross_exposure = df["risk_gross_exposure"].max()
        
        # Risk gross exposure should be at most the signal gross exposure, thus <= target
        self.assertLessEqual(max_risk_gross_exposure, signal_params.max_gross_exposure + 1e-4)

if __name__ == '__main__':
    unittest.main()
