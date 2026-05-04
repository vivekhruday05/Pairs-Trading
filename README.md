# Pairs Trading Terminal

A comprehensive algorithmic trading platform designed for identifying, analyzing, and backtesting statistical arbitrage opportunities through pairs trading. The system uses cointegration and dynamic hedging ratios to detect mean-reverting relationships between financial assets.

## Features

- **Pair Identification**: Automatically scan universes of assets (e.g., NASDAQ-100) using correlation filters and Engle-Granger cointegration tests to find statistically robust pairs.
- **Dynamic Signal Generation**: Generate z-score based trading signals with rolling mean and volatility windows. Automatically calculate inverse-volatility position sizing to manage risk.
- **Robust Backtesting Engine**: Test trading strategies with historical data. The backtester includes transaction costs, dynamic stop-losses, maximum holding periods, and realistic portfolio equity tracking.
- **Live Pair Testing & Streaming**: Connect via WebSockets to stream live market data and calculate incremental PnL, current z-scores, and positions in real-time.
- **Interactive Analytics Dashboard**: A rich, dynamic React frontend for visualizing equity curves, drawdown, historical spreads, and real-time PnL performance metrics.

## Technology Stack

- **Backend**: Python, FastAPI, Pandas, Statsmodels
- **Frontend**: React, Vite, TailwindCSS, Recharts, Lucide-React
- **Data Delivery**: WebSockets (Live Data) & REST API (Historical/Analytical Data)

## Architecture

The project is split into an independent backend and frontend architecture. For a detailed technical and mathematical breakdown of the engines (Identification, Signal Generation, Backtesting, and Data), please see [docs/architecture.md](docs/architecture.md).

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Conda (optional but recommended for environment management)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd Pairs-Trading
   ```

2. **Backend Setup:**
   It's recommended to use a virtual environment or conda environment (e.g., `myenv`).
   ```bash
   conda create -n myenv python=3.10
   conda activate myenv
   cd backend
   pip install -r requirements.txt
   ```

3. **Frontend Setup:**
   ```bash
   cd frontend
   npm install
   ```

### Running the Terminal

You can use the provided shell scripts to easily start and stop the terminal.

To start the terminal (ensure your environment is active):
```bash
./start_terminal.sh
```

- **Frontend UI**: `http://localhost:3000`
- **Backend API Docs**: `http://localhost:8000/docs`

To stop the terminal safely:
```bash
./stop_terminal.sh
```

## Project Structure

- `/src/pairs_trading/`: Core Python trading engine algorithms.
- `/backend/`: FastAPI application exposing the core engine via REST and WebSockets.
- `/frontend/`: React application providing the visual terminal.
- `/docs/`: Architectural documentation and mathematical proofs.
- `/examples/`: Example scripts demonstrating engine usage in raw Python.

## Testing & Evaluation

This project includes invariant tests to ensure leverage limits and weight balancing are maintained, as well as a comparative experiment script that validates causal-based pair selection against correlation-based selection out-of-sample.

1. **Run Invariant Tests:**
   ```bash
   conda run -n myenv env PYTHONPATH=src python -m unittest discover tests/
   ```

2. **Run Comparative Experiment:**
   ```bash
   conda run -n myenv env PYTHONPATH=src python examples/comparative_experiment.py
   ```
   *This will output PnL visualizations to `docs/report/figures/`.*

3. **Integrated Demo Notebook:**
   You can view or run the end-to-end integration demo notebook located at `examples/Integrated_Demo.ipynb`.

4. **Evaluation Report:**
   The final evaluation report documenting insights from the causal vs. correlation study is available in `docs/report/report.tex`.
