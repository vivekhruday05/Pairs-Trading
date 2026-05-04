import warnings
warnings.filterwarnings("ignore")

import os
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from pairs_trading.data import DataDownloader, Instrument
from pairs_trading.pair_identification import PairIdentificationEngine
from pairs_trading.signal_generation import PairSignalEngine, SignalParameters
from pairs_trading.risk_management import PairRiskEngine, RiskParameters
from pairs_trading.backtesting import PairBacktestEngine, BacktestParameters

def compute_drawdown(pnl_series, initial_capital):
    equity = initial_capital + pnl_series
    peak = equity.cummax()
    drawdown = (equity - peak) / peak
    return drawdown

def compute_sharpe(pnl_series, initial_capital, risk_free_rate=0.0):
    daily_returns = pnl_series.diff().fillna(0) / initial_capital
    if daily_returns.std() == 0:
        return 0
    return np.sqrt(252) * (daily_returns.mean() - risk_free_rate) / daily_returns.std()

def main():
    print("Starting Expanded Comparative Experiment & Stress Testing")
    
    train_start = datetime(2020, 1, 1)
    train_end = datetime(2022, 12, 31)
    test_start = datetime(2023, 1, 1)
    test_end = datetime(2024, 1, 1)

    symbols = ["AAPL", "MSFT", "GOOGL", "META", "AMZN", "JPM", "BAC", "C", "WFC", "GS", "XOM", "CVX", "PFE", "JNJ", "UNH", "V", "MA", "PG", "KO", "PEP"]
    instruments = [Instrument(symbol=s) for s in symbols]
    
    engine = PairIdentificationEngine()
    
    print(f"Fetching in-sample data from {train_start.date()} to {train_end.date()}...")
    report_train = engine.identify_pairs(
        instruments=instruments,
        start=train_start,
        end=train_end,
        min_correlation=0.5,
        min_observations=100
    )
    
    df_analyzed = report_train.to_frame()
    if df_analyzed.empty:
        print("No pairs identified in training set.")
        return

    # Pair Selection
    corr_sorted = df_analyzed.sort_values(by="correlation", ascending=False)
    corr_pairs = corr_sorted.head(2)[["symbol_x", "symbol_y"]].values.tolist()
    
    df_analyzed['min_granger_pvalue'] = df_analyzed[['granger_xy_min_pvalue', 'granger_yx_min_pvalue']].min(axis=1)
    causal_sorted = df_analyzed.sort_values(by="min_granger_pvalue", ascending=True)
    coint_causal = causal_sorted[causal_sorted['engle_granger_pvalue'] < 0.1]
    
    if len(coint_causal) >= 2:
        causal_pairs = coint_causal.head(2)[["symbol_x", "symbol_y"]].values.tolist()
    else:
        causal_pairs = causal_sorted.head(2)[["symbol_x", "symbol_y"]].values.tolist()

    print("Correlation pairs:", corr_pairs)
    print("Causal pairs:", causal_pairs)
    
    print(f"Fetching out-of-sample data from {test_start.date()} to {test_end.date()}...")
    price_matrix_test = engine.build_price_matrix(
        instruments=instruments,
        start=test_start,
        end=test_end
    )
    
    signal_engine = PairSignalEngine()
    risk_engine = PairRiskEngine()
    
    initial_capital = 100_000
    os.makedirs("docs/report/figures", exist_ok=True)
    plt.style.use("seaborn-v0_8-darkgrid")

    # Store base configuration results
    results_pnl = {}
    results_dd = {}
    daily_returns_dict = {}
    gross_exposure_dict = {}
    
    all_pairs = {"Correlation": corr_pairs, "Causal": causal_pairs}
    
    # 1. Base Backtest & Drawdown Analysis
    for approach, pairs in all_pairs.items():
        cumulative_pnl = pd.Series(dtype=float)
        cumulative_exposure = pd.Series(dtype=float)
        
        for sx, sy in pairs:
            if sx not in price_matrix_test.columns or sy not in price_matrix_test.columns: continue
            
            train_pair_data = report_train.price_matrix[[sx, sy]].dropna()
            if train_pair_data.empty: continue
            sm_api = engine._get_statsmodels_api()
            x = train_pair_data[sx]
            res = sm_api.OLS(train_pair_data[sy], sm_api.add_constant(x)).fit()
            hr = float(res.params.iloc[-1])
            
            sig_res = signal_engine.generate_for_pair(
                price_frame=price_matrix_test, symbol_x=sx, symbol_y=sy,
                hedge_ratio=hr, parameters=SignalParameters()
            )
            bt_engine = PairBacktestEngine(risk_engine=risk_engine)
            bt_res = bt_engine.run(
                signal_result=sig_res,
                risk_parameters=RiskParameters(),
                backtest_parameters=BacktestParameters(initial_capital=initial_capital)
            )
            
            if cumulative_pnl.empty:
                cumulative_pnl = bt_res.frame["net_pnl"]
                cumulative_exposure = bt_res.frame["gross_pnl"] # Placeholder for now, exposure is below
            else:
                cumulative_pnl += bt_res.frame["net_pnl"]
                
        results_pnl[approach] = cumulative_pnl.cumsum()
        results_dd[approach] = compute_drawdown(results_pnl[approach], initial_capital)
        daily_returns_dict[approach] = results_pnl[approach].diff().fillna(0) / initial_capital

    # VIZ 1: Performance Comparison
    fig, ax = plt.subplots(figsize=(10, 5))
    for approach, pnl in results_pnl.items():
        if not pnl.empty: ax.plot(pnl.index, pnl, label=f"{approach} PnL")
    ax.set_title("Out-of-Sample Performance")
    ax.legend()
    plt.tight_layout()
    plt.savefig("docs/report/figures/viz1_performance.png")
    
    # VIZ 2: Drawdown Analysis
    fig, ax = plt.subplots(figsize=(10, 5))
    for approach, dd in results_dd.items():
        if not dd.empty: ax.fill_between(dd.index, dd, 0, alpha=0.3, label=f"{approach} Drawdown")
    ax.set_title("Drawdown Analysis")
    ax.legend()
    plt.tight_layout()
    plt.savefig("docs/report/figures/viz2_drawdown.png")
    
    # VIZ 3: Daily Return Distribution
    fig, ax = plt.subplots(figsize=(10, 5))
    for approach, rets in daily_returns_dict.items():
        if not rets.empty: sns.kdeplot(rets, fill=True, label=approach, ax=ax)
    ax.set_title("Daily Return Distribution")
    ax.legend()
    plt.tight_layout()
    plt.savefig("docs/report/figures/viz3_returns_kde.png")

    # 4. Stress Testing: Transaction Costs
    costs = np.linspace(0, 0.005, 10)
    tc_results = {"Correlation": [], "Causal": []}
    
    for tc in costs:
        for approach, pairs in all_pairs.items():
            total_pnl = 0
            for sx, sy in pairs:
                if sx not in price_matrix_test.columns or sy not in price_matrix_test.columns: continue
                train_pair_data = report_train.price_matrix[[sx, sy]].dropna()
                if train_pair_data.empty: continue
                sm_api = engine._get_statsmodels_api()
                hr = float(sm_api.OLS(train_pair_data[sy], sm_api.add_constant(train_pair_data[sx])).fit().params.iloc[-1])
                sig_res = signal_engine.generate_for_pair(price_frame=price_matrix_test, symbol_x=sx, symbol_y=sy, hedge_ratio=hr)
                bt_res = PairBacktestEngine(risk_engine=risk_engine).run(
                    signal_result=sig_res,
                    backtest_parameters=BacktestParameters(transaction_cost_rate=tc)
                )
                total_pnl += bt_res.frame["net_pnl"].sum()
            tc_results[approach].append(total_pnl)
            
    # VIZ 4: Transaction Cost Sensitivity
    fig, ax = plt.subplots(figsize=(10, 5))
    for approach, pnl_list in tc_results.items():
        ax.plot(costs, pnl_list, marker='o', label=approach)
    ax.set_title("Sensitivity to Transaction Costs")
    ax.set_xlabel("Transaction Cost Rate")
    ax.set_ylabel("Total Net PnL")
    ax.legend()
    plt.tight_layout()
    plt.savefig("docs/report/figures/viz4_tc_sensitivity.png")
    
    # 5. Stress Testing: Stop Loss Levels
    stop_losses = np.linspace(0.01, 0.10, 10)
    sl_results = {"Correlation": [], "Causal": []}
    
    for sl in stop_losses:
        for approach, pairs in all_pairs.items():
            total_pnl = 0
            for sx, sy in pairs:
                if sx not in price_matrix_test.columns or sy not in price_matrix_test.columns: continue
                train_pair_data = report_train.price_matrix[[sx, sy]].dropna()
                if train_pair_data.empty: continue
                sm_api = engine._get_statsmodels_api()
                hr = float(sm_api.OLS(train_pair_data[sy], sm_api.add_constant(train_pair_data[sx])).fit().params.iloc[-1])
                sig_res = signal_engine.generate_for_pair(price_frame=price_matrix_test, symbol_x=sx, symbol_y=sy, hedge_ratio=hr)
                bt_res = PairBacktestEngine().run(
                    signal_result=sig_res,
                    risk_parameters=RiskParameters(stop_loss_fraction=sl)
                )
                total_pnl += bt_res.frame["net_pnl"].sum()
            sl_results[approach].append(total_pnl)
            
    # VIZ 5: Stop Loss Sensitivity
    fig, ax = plt.subplots(figsize=(10, 5))
    for approach, pnl_list in sl_results.items():
        ax.plot(stop_losses, pnl_list, marker='s', label=approach)
    ax.set_title("Sensitivity to Stop Loss Levels")
    ax.set_xlabel("Stop Loss Fraction")
    ax.set_ylabel("Total Net PnL")
    ax.legend()
    plt.tight_layout()
    plt.savefig("docs/report/figures/viz5_sl_sensitivity.png")
    
    # VIZ 6: Half-life Distribution
    half_lives = df_analyzed["half_life"].dropna()
    half_lives = half_lives[half_lives < 100] # filter outliers
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(half_lives, bins=20, kde=True, ax=ax)
    ax.set_title("Distribution of Mean Reversion Half-Lives (Days)")
    plt.tight_layout()
    plt.savefig("docs/report/figures/viz6_halflife.png")
    
    # VIZ 7: Correlation vs Causality Scatter
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.scatterplot(data=df_analyzed, x="correlation", y="min_granger_pvalue", hue="engle_granger_pvalue", ax=ax, palette="coolwarm")
    ax.set_title("Correlation vs. Minimum Granger p-value")
    plt.tight_layout()
    plt.savefig("docs/report/figures/viz7_corr_vs_causal.png")

    # VIZ 8: Rolling Hedge Ratio Stability
    sx_c, sy_c = causal_pairs[0]
    train_causal_data = report_train.price_matrix[[sx_c, sy_c]].dropna()
    rolling_beta = []
    window = 60
    sm_api = engine._get_statsmodels_api()
    for i in range(window, len(train_causal_data)):
        y = train_causal_data[sy_c].iloc[i-window:i]
        x = sm_api.add_constant(train_causal_data[sx_c].iloc[i-window:i])
        rolling_beta.append(sm_api.OLS(y, x).fit().params.iloc[-1])
        
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(train_causal_data.index[window:], rolling_beta)
    ax.set_title(f"Rolling Hedge Ratio (60d) for Causal Pair: {sx_c}-{sy_c}")
    plt.tight_layout()
    plt.savefig("docs/report/figures/viz8_rolling_hr.png")

    # VIZ 9: Holding Period Sensitivity
    hp_list = [5, 10, 15, 20, 30, 45, 60]
    hp_results = {"Correlation": [], "Causal": []}
    for hp in hp_list:
        for approach, pairs in all_pairs.items():
            total_pnl = 0
            for sx, sy in pairs:
                if sx not in price_matrix_test.columns or sy not in price_matrix_test.columns: continue
                train_pair_data = report_train.price_matrix[[sx, sy]].dropna()
                if train_pair_data.empty: continue
                hr = float(sm_api.OLS(train_pair_data[sy], sm_api.add_constant(train_pair_data[sx])).fit().params.iloc[-1])
                sig_res = signal_engine.generate_for_pair(price_frame=price_matrix_test, symbol_x=sx, symbol_y=sy, hedge_ratio=hr)
                bt_res = PairBacktestEngine().run(
                    signal_result=sig_res,
                    risk_parameters=RiskParameters(max_holding_period=hp)
                )
                total_pnl += bt_res.frame["net_pnl"].sum()
            hp_results[approach].append(total_pnl)
            
    fig, ax = plt.subplots(figsize=(10, 5))
    for approach, pnl_list in hp_results.items():
        ax.plot(hp_list, pnl_list, marker='d', label=approach)
    ax.set_title("Sensitivity to Max Holding Period")
    ax.set_xlabel("Holding Period (Days)")
    ax.set_ylabel("Total Net PnL")
    ax.legend()
    plt.tight_layout()
    plt.savefig("docs/report/figures/viz9_hp_sensitivity.png")
    
    # VIZ 10: Gross Exposure Over Time
    fig, ax = plt.subplots(figsize=(10, 5))
    for approach, pairs in all_pairs.items():
        cum_exposure = pd.Series(dtype=float)
        for sx, sy in pairs:
            if sx not in price_matrix_test.columns or sy not in price_matrix_test.columns: continue
            train_pair_data = report_train.price_matrix[[sx, sy]].dropna()
            if train_pair_data.empty: continue
            hr = float(sm_api.OLS(train_pair_data[sy], sm_api.add_constant(train_pair_data[sx])).fit().params.iloc[-1])
            sig_res = signal_engine.generate_for_pair(price_frame=price_matrix_test, symbol_x=sx, symbol_y=sy, hedge_ratio=hr)
            # Use risk_gross_exposure
            risk_res = risk_engine.apply_controls(signal_frame=sig_res.frame, symbol_x=sx, symbol_y=sy)
            if cum_exposure.empty: cum_exposure = risk_res.frame["risk_gross_exposure"]
            else: cum_exposure += risk_res.frame["risk_gross_exposure"]
        ax.plot(cum_exposure.index, cum_exposure, label=approach, alpha=0.7)
    ax.set_title("Realized Gross Exposure Over Time")
    ax.legend()
    plt.tight_layout()
    plt.savefig("docs/report/figures/viz10_exposure.png")

    print("Generated 10 Visualizations. Data saved.")
    
    # Save a CSV with table data for the report
    table_data = []
    for approach in all_pairs.keys():
        ret = results_pnl[approach].iloc[-1]
        dd = results_dd[approach].min()
        sharpe = compute_sharpe(results_pnl[approach], initial_capital)
        table_data.append({"Approach": approach, "Total PnL": ret, "Max Drawdown": dd, "Sharpe Ratio": sharpe})
    
    pd.DataFrame(table_data).to_csv("docs/report/results_table.csv", index=False)
    print("Saved table data to docs/report/results_table.csv")

if __name__ == "__main__":
    main()
