# Quick Start Guide - Pairs Trading Terminal

Get the terminal running in 3 minutes!

## Method 1: Automatic Startup (Recommended)

```bash
cd /home/vivek/test/gitrepo/Pairs-Trading

# Make script executable
chmod +x start_terminal.sh

# Run it
./start_terminal.sh
```

This will:
1. Check prerequisites (Python 3, Node.js)
2. Install dependencies if needed
3. Start backend on http://localhost:8000
4. Start frontend on http://localhost:3000

Then open your browser to **http://localhost:3000**

## Method 2: Manual Startup

**Terminal 1 - Backend:**
```bash
cd /home/vivek/test/gitrepo/Pairs-Trading/backend
pip install -r requirements.txt  # First time only
python main.py
```

Output should show:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 - Frontend:**
```bash
cd /home/vivek/test/gitrepo/Pairs-Trading/frontend
npm install  # First time only
npm run dev
```

Output should show:
```
VITE v4.1.0 ready in XXX ms
➜  Local:   http://localhost:3000
```

Then open **http://localhost:3000** in your browser

## First Steps in the Terminal

### 1. Live Stream Data
- Click **LIVE STREAM** tab
- Default symbols: AAPL, GOOGL, MSFT, AMZN, TSLA
- Add more symbols or remove any you want
- Click **REFRESH** to get latest prices

### 2. Find Cointegrated Pairs
- Click **PAIR FINDER** tab
- Symbols are pre-populated
- Adjust date range and correlation threshold
- Click **FIND COINTEGRATED PAIRS**
- Results show correlation, ADF p-value, and cointegration scores

### 3. Generate Signals
- Click **SIGNALS** tab
- Enter pair (e.g., AAPL and GOOGL)
- Adjust entry/exit thresholds
- Click **GENERATE SIGNALS**
- See z-score and position charts

### 4. Analyze Pair Performance
- Click **ANALYZER** tab
- Choose **MANUAL SELECT** mode or **AUTO FINDER** mode
- For auto: it finds and suggests pairs to test
- For manual: enter symbols and run analysis
- View live portfolio performance and P&L

### 5. Full Backtest
- Click **BACKTEST** tab
- Enter pair and parameters
- Configure risk controls (stop loss, max holding period)
- Click **RUN BACKTEST**
- See equity curve, P&L breakdown, and summary stats
- Download report as text file

## Troubleshooting

### Port Already in Use
```bash
# Kill existing process on port 8000
lsof -i :8000
kill -9 <PID>

# Or use different port in backend/main.py
```

### No Module Error
```bash
# Make sure PYTHONPATH includes src directory
export PYTHONPATH="${PYTHONPATH}:./src"
```

### Frontend shows blank page
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### API returns empty data
- Check symbol spelling (use Yahoo Finance symbols)
- Try recent symbols like MSFT, AAPL, GOOGL
- Verify date range is valid (not too far back)

## What You Can Do

✅ Stream live market data  
✅ Find statistically cointegrated pairs  
✅ Generate algorithmic trading signals  
✅ Test on historical data with backtests  
✅ Simulate transaction costs and risk controls  
✅ Analyze pair performance live  
✅ Download backtest reports  

## Next

For detailed documentation, see **TERMINAL_README.md**

For framework documentation, see **README.md**

## Stop the Terminal

To stop, press **Ctrl+C** (or Cmd+C on Mac) in both terminals.

---

Enjoy the Pairs Trading Terminal! 🚀
