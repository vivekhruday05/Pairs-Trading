import json

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Pairs Trading: Integrated Demo & Comparative Analysis\n",
                "This notebook demonstrates the end-to-end functionality of our Pairs Trading Framework.\n",
                "It explores identifying pairs, generating signals, and running risk-adjusted backtests.\n",
                "Furthermore, it compares a traditional Correlation-based selection with a Causal-based (Granger) approach."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import warnings\n",
                "warnings.filterwarnings(\"ignore\")\n",
                "\n",
                "from datetime import datetime\n",
                "import pandas as pd\n",
                "import matplotlib.pyplot as plt\n",
                "import seaborn as sns\n",
                "\n",
                "from pairs_trading.data import DataDownloader, Instrument\n",
                "from pairs_trading.pair_identification import PairIdentificationEngine\n",
                "from pairs_trading.signal_generation import PairSignalEngine, SignalParameters\n",
                "from pairs_trading.risk_management import PairRiskEngine, RiskParameters\n",
                "from pairs_trading.backtesting import PairBacktestEngine, BacktestParameters\n",
                "\n",
                "plt.style.use(\"seaborn-v0_8-darkgrid\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 1. Data Fetching & Pair Identification\n",
                "We fetch data for popular tickers and run the identification pipeline."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "train_start = datetime(2020, 1, 1)\n",
                "train_end = datetime(2022, 12, 31)\n",
                "symbols = [\"AAPL\", \"MSFT\", \"GOOGL\", \"META\", \"AMZN\", \"JPM\", \"BAC\", \"C\", \"WFC\", \"GS\", \"XOM\", \"CVX\"]\n",
                "instruments = [Instrument(symbol=s) for s in symbols]\n",
                "\n",
                "engine = PairIdentificationEngine()\n",
                "report_train = engine.identify_pairs(\n",
                "    instruments=instruments,\n",
                "    start=train_start,\n",
                "    end=train_end,\n",
                "    min_correlation=0.5,\n",
                "    min_observations=100\n",
                ")\n",
                "df_analyzed = report_train.to_frame()\n",
                "df_analyzed.head()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 2. Pair Selection (Correlation vs Causal)\n",
                "We select the top 2 pairs based on correlation, and the top 2 based on causality."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "corr_sorted = df_analyzed.sort_values(by=\"correlation\", ascending=False)\n",
                "corr_pairs = corr_sorted.head(2)[[\"symbol_x\", \"symbol_y\"]].values.tolist()\n",
                "\n",
                "df_analyzed['min_granger_pvalue'] = df_analyzed[['granger_xy_min_pvalue', 'granger_yx_min_pvalue']].min(axis=1)\n",
                "causal_sorted = df_analyzed.sort_values(by=\"min_granger_pvalue\", ascending=True)\n",
                "coint_causal = causal_sorted[causal_sorted['engle_granger_pvalue'] < 0.1]\n",
                "\n",
                "if len(coint_causal) >= 2:\n",
                "    causal_pairs = coint_causal.head(2)[[\"symbol_x\", \"symbol_y\"]].values.tolist()\n",
                "else:\n",
                "    causal_pairs = causal_sorted.head(2)[[\"symbol_x\", \"symbol_y\"]].values.tolist()\n",
                "\n",
                "print(\"Correlation pairs:\", corr_pairs)\n",
                "print(\"Causal pairs:\", causal_pairs)"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 3. Out-of-Sample Validation & Signal Generation\n",
                "Now we test both sets of pairs on data from 2023 onwards."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "test_start = datetime(2023, 1, 1)\n",
                "test_end = datetime(2024, 1, 1)\n",
                "price_matrix_test = engine.build_price_matrix(instruments=instruments, start=test_start, end=test_end)\n",
                "\n",
                "signal_engine = PairSignalEngine()\n",
                "risk_engine = PairRiskEngine()\n",
                "backtest_engine = PairBacktestEngine(risk_engine=risk_engine)\n",
                "\n",
                "signal_params = SignalParameters(zscore_window=30, volatility_window=30)\n",
                "risk_params = RiskParameters(stop_loss_fraction=0.05)\n",
                "backtest_params = BacktestParameters(initial_capital=100_000)\n",
                "\n",
                "results = {}\n",
                "all_pairs = {\"Correlation\": corr_pairs, \"Causal\": causal_pairs}\n",
                "\n",
                "for approach, pairs in all_pairs.items():\n",
                "    cumulative_pnl = pd.Series(dtype=float)\n",
                "    for sx, sy in pairs:\n",
                "        train_pair_data = report_train.price_matrix[[sx, sy]].dropna()\n",
                "        if train_pair_data.empty: continue\n",
                "        \n",
                "        sm_api = engine._get_statsmodels_api()\n",
                "        x = train_pair_data[sx]\n",
                "        x_with_const = sm_api.add_constant(x)\n",
                "        res = sm_api.OLS(train_pair_data[sy], x_with_const).fit()\n",
                "        hr = float(res.params.iloc[-1])\n",
                "        \n",
                "        sig_res = signal_engine.generate_for_pair(\n",
                "            price_frame=price_matrix_test, symbol_x=sx, symbol_y=sy,\n",
                "            hedge_ratio=hr, parameters=signal_params\n",
                "        )\n",
                "        bt_res = backtest_engine.run(signal_result=sig_res, risk_parameters=risk_params, backtest_parameters=backtest_params)\n",
                "        bt_df = bt_res.frame\n",
                "        if cumulative_pnl.empty: cumulative_pnl = bt_df[\"net_pnl\"]\n",
                "        else: cumulative_pnl += bt_df[\"net_pnl\"]\n",
                "    \n",
                "    results[approach] = cumulative_pnl.cumsum()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 4. Results & Visualization\n",
                "Finally, we visualize the resulting Equity Curves for both approaches."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "fig, ax = plt.subplots(figsize=(10, 5))\n",
                "for approach, pnl_series in results.items():\n",
                "    if not pnl_series.empty:\n",
                "        ax.plot(pnl_series.index, pnl_series, label=f\"{approach} PnL\", linewidth=2)\n",
                "ax.set_title(\"Out-of-Sample Performance\")\n",
                "ax.legend()\n",
                "plt.show()"
            ]
        }
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.8.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

with open("examples/Integrated_Demo.ipynb", "w") as f:
    json.dump(notebook, f, indent=2)

print("Notebook generated successfully!")
