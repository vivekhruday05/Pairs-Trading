# Pairs Trading Architecture and Mathematical Foundations

## Overview

The Pairs Trading Terminal is structured into a modular system where computational heavy-lifting is decoupled from data delivery and visualization. The core logic resides in a standalone Python package (`src/pairs_trading`), which is wrapped by a FastAPI backend (`backend/main.py`), and visualized by a React frontend (`frontend/src`).

This document details the mathematical logic and software architecture underlying the core components.

---

## 1. Pair Identification Engine

**Objective:** Identify asset pairs that exhibit a stable, mean-reverting relationship over time.

### Methodology
We rely on the concept of **Cointegration**, which implies that even if two price series $X_t$ and $Y_t$ are non-stationary (they wander randomly), a linear combination of them is stationary.

1. **Correlation Filter:** 
   To reduce computational load, pairs must first pass a basic Pearson correlation threshold.
   $$ \rho_{X,Y} = \frac{\text{cov}(X,Y)}{\sigma_X \sigma_Y} \ge \rho_{\text{min}} $$

2. **Engle-Granger Cointegration Test:**
   If the correlation passes, we perform an Ordinary Least Squares (OLS) regression:
   $$ Y_t = \beta X_t + \alpha + \epsilon_t $$
   Here, $\beta$ is the *hedge ratio*. We then apply the Augmented Dickey-Fuller (ADF) test on the residual spread $\epsilon_t$:
   $$ \Delta \epsilon_t = \gamma \epsilon_{t-1} + \sum_{i=1}^p \delta_i \Delta \epsilon_{t-i} + u_t $$
   If the p-value of the ADF test statistic on $\gamma$ is below a defined significance level (e.g., 0.05), we reject the null hypothesis of a unit root, concluding the residual spread $\epsilon_t$ is stationary. The pair is deemed cointegrated.

3. **Half-Life of Mean Reversion:**
   To determine how quickly the spread reverts to its mean, we model the residuals using an Ornstein-Uhlenbeck (OU) process. By running an OLS regression of the change in residuals against the previous residuals:
   $$ \Delta \epsilon_t = \lambda \epsilon_{t-1} + u_t $$
   If $\lambda < 0$, the process is mean-reverting. We calculate the half-life $H$ (in days, assuming daily data) as:
   $$ H = -\frac{\ln(2)}{\lambda} $$
   A shorter half-life indicates a faster reversion, which is generally more desirable for higher-frequency pairs trading.

### Software Implementation
The `PairIdentificationEngine` iterates through combinations of a given universe of assets, running the `statsmodels` OLS and `coint` (cointegration) functions. Results are packaged into a `PairIdentificationReport`.

---

## 2. Signal Generation Engine

**Objective:** Transform the stationary spread of a cointegrated pair into actionable entry and exit signals, and determine position sizing.

### Mathematical Logic

1. **Rolling Hedge Ratio:**
   While the Engle-Granger test calculates a static $\beta$, in trading, we continually update $\beta$ or use rolling approximations to define the spread:
   $$ S_t = Y_t - \beta X_t $$

2. **Z-Score Normalization:**
   To standardize the spread, we calculate a rolling z-score using a trailing window $W$:
   $$ \mu_t = \frac{1}{W}\sum_{i=0}^{W-1} S_{t-i} \quad , \quad \sigma_t = \sqrt{\frac{1}{W-1} \sum_{i=0}^{W-1} (S_{t-i} - \mu_t)^2} $$
   $$ Z_t = \frac{S_t - \mu_t}{\sigma_t} $$

3. **Trading Logic:**
   - **Entry Short:** If $Z_t \ge T_{entry}$, we expect the spread to revert downwards. We sell the spread (Short $Y$, Long $X$).
   - **Entry Long:** If $Z_t \le -T_{entry}$, we expect the spread to revert upwards. We buy the spread (Long $Y$, Short $X$).
   - **Exit:** If the position is open and $Z_t$ crosses back through $T_{exit}$ (or $-T_{exit}$), we close the position.

4. **Inverse Volatility Position Sizing:**
   To equalize risk across different market conditions, capital allocation is scaled inversely to the spread's volatility:
   $$ \text{Scale}_t = \frac{\text{Target Exposure}}{\max(\text{Vol}_t, \text{Min Vol})} $$

### Software Implementation
The `PairSignalEngine` utilizes `pandas` rolling windows to efficiently vectorize z-score computations over the entire price dataframe. It iterates through the z-score series to apply the path-dependent entry/exit state machine, outputting a DataFrame of target weights.

---

## 3. Backtesting Engine

**Objective:** Simulate the trading strategy over historical data to evaluate performance, considering market frictions.

### Methodology

1. **Mark-to-Market PnL:**
   Gross daily returns are calculated based on the day-over-day change in the spread, scaled by the position size.
   $$ \text{Gross PnL}_t = \text{Position}_{t-1} \times (S_t - S_{t-1}) $$

2. **Transaction Costs:**
   Every time the position size changes, transaction costs are incurred.
   $$ \text{Cost}_t = |\text{Position}_t - \text{Position}_{t-1}| \times C_{\text{rate}} $$

3. **Risk Management:**
   - **Stop Loss:** If the cumulative loss of an open trade exceeds the predefined stop-loss fraction of capital, the trade is forced to close.
   - **Max Holding Period:** If a trade remains open longer than a defined threshold of days without reverting, it is liquidated to free up capital.

4. **Performance Metrics:**
   The backtester calculates Total Net PnL, Maximum Drawdown (peak-to-trough drop in equity), and the Sharpe Ratio to evaluate risk-adjusted returns.

### Software Implementation
The `PairBacktestEngine` integrates tightly with `PairSignalResult`. It walks through the signals, applies risk overrides (stop-loss, holding period), subtracts transaction costs, and accumulates an equity curve.

---

## 4. Frontend & WebSocket Architecture

**Objective:** Provide a low-latency, responsive visual interface for the mathematical engines.

- **FastAPI Backend:** Handles all heavy compute asynchronously. Exposes standard REST routes (`/api/signals/generate`, `/api/backtest/run`) for bulk historical calculations.
- **Live Stream via WebSockets:** For live pair testing (`/ws/pair-stream/{symbol_x}/{symbol_y}`), the backend maintains an open WebSocket connection. It polls the `DataDownloader` at a fixed interval, pushes the latest data through the `PairSignalEngine` to calculate the *current* real-time $Z_t$ and incremental PnL, and broadcasts the localized tail of the DataFrame to the React frontend.
- **Global State Management:** The React frontend utilizes a global `symbols` state, allowing a user to identify a cointegrated pair in the "Pair Finder", and instantly push that pair into the Signal Generator, Backtester, or Live Streamer without re-entering data.
