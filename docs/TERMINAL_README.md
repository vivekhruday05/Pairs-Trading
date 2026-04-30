# Pairs Trading Terminal - Frontend & Backend

Professional Bloomberg Terminal-style interface for the Pairs Trading Framework with live data streaming, advanced charting, and risk management features.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  React Frontend (Port 3000)                  │
│  - Bloomberg Terminal UI                                    │
│  - Live Charts (Recharts)                                   │
│  - Real-time Data Streaming                                 │
│  - Manual/Auto Pair Selection                               │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/WebSocket
┌────────────────────▼────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                     │
│  - REST Endpoints                                           │
│  - WebSocket Streams                                        │
│  - Pairs Trading Core Integration                           │
└─────────────────────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│         Pairs Trading Framework (src/pairs_trading/)         │
│  - Data Download                                            │
│  - Pair Identification                                      │
│  - Signal Generation                                        │
│  - Risk Management                                          │
│  - Backtesting Engine                                       │
└─────────────────────────────────────────────────────────────┘
```

## Features

### Frontend Features
- **Live Data Streaming** - Real-time price updates with color-coded changes
- **Pair Identification** - Automatic discovery of cointegrated pairs
- **Signal Generation** - Z-score signals with inverse-volatility position sizing
- **Backtesting** - Full P&L accounting with risk controls
- **Pair Analyzer** - Manual selection or auto-recommendation mode
- **Professional Charts** - Interactive Recharts visualizations with multiple metrics
- **Bloomberg Terminal Styling** - Dark theme with clean typography and grid layouts
- **Responsive Design** - Works on desktop, tablet, mobile

### Backend Features
- **REST API** - All pairs trading functions exposed via HTTP
- **WebSocket Streams** - Live price and pair signal updates
- **CORS Support** - Frontend/backend on different ports
- **Data Caching** - Disk-based cache to minimize API calls
- **Error Handling** - Comprehensive error messages and validation

## Installation

### Prerequisites
- Python 3.11+ (backend)
- Node.js 16+ (frontend)
- macOS/Linux/Windows

### Backend Setup

1. **Install Python dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Verify installation:**
```bash
python main.py
# Server should start at http://localhost:8000
```

### Frontend Setup

1. **Install Node dependencies:**
```bash
cd frontend
npm install
```

2. **Verify installation:**
```bash
npm run dev
# Frontend should start at http://localhost:3000
```

## Running the Application

### Option 1: Sequential Start (Recommended for Development)

**Terminal 1 - Start Backend:**
```bash
cd /home/vivek/test/gitrepo/Pairs-Trading/backend
python main.py
# Output: INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 - Start Frontend:**
```bash
cd /home/vivek/test/gitrepo/Pairs-Trading/frontend
npm run dev
# Output: VITE v4.1.0 ready in 1234 ms
#         ➜ Local:   http://localhost:3000
```

Visit: **http://localhost:3000**

### Option 2: Using Docker (Coming Soon)

```bash
docker-compose up
```

### Option 3: Production Build

**Build frontend:**
```bash
cd frontend
npm run build
# Creates dist/ folder with optimized assets
```

**Run backend with frontend static files:**
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Data Endpoints
- `POST /api/data/download` - Download market data for symbols
- `GET /api/data/latest/{symbol}` - Get latest price for a symbol

### Pair Identification
- `POST /api/pairs/identify` - Identify cointegrated pairs using correlation + Engle-Granger

### Signal Generation
- `POST /api/signals/generate` - Generate z-score signals for a pair

### Backtesting
- `POST /api/backtest/run` - Run full backtest with risk controls and P&L accounting

### WebSocket Streams
- `WS /ws/live-stream/{symbol}` - Live price updates every 5 seconds
- `WS /ws/pair-stream/{symbol_x}/{symbol_y}` - Live pair z-score updates every 10 seconds

### Utility
- `GET /api/health` - Health check
- `GET /api/config/defaults` - Default configuration values

## Frontend Navigation

### Dashboard
Overview of features and quick status checks

### Live Stream
Real-time price updates for selected symbols with volume and daily changes

### Pair Finder
Automatic pair identification using correlation and cointegration analysis
- Configurable date range, correlation threshold, and result count
- Shows correlation, ADF p-value, cointegration p-value, and half-life

### Signals
Z-score signal generation for selected pair
- Charts for spread, z-score, positions, and exposure
- Interactive parameter adjustment

### Analyzer
Dual-mode pair analysis with manual selection or auto-recommendation
- **Manual Mode**: Enter symbols directly
- **Auto Mode**: System suggests cointegrated pairs from symbol list
- Support for historical or live data streams
- Real-time portfolio performance visualization

### Backtest
Full pipeline execution with complete P&L accounting
- Signal generation with risk controls (stop-loss, time-stop, VaR)
- Transaction cost simulation
- Summary metrics and downloadable report
- Equity curve visualization

## Configuration

### Backend Configuration (in `main.py`)

Change server settings:
```python
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Frontend Configuration (in `frontend/vite.config.js`)

Change API proxy and port:
```javascript
server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
```

## Default Parameters

All endpoints use these defaults if not specified:

**Pair Identification:**
- Date range: Last 2 years
- Min correlation: 0.8
- Max results: 10

**Signal Generation:**
- Entry threshold: 2.0σ
- Exit threshold: 0.5σ
- Target exposure: 1.0

**Risk Management:**
- Stop loss: 3% of entry exposure
- Max holding period: 20 days

**Backtesting:**
- Transaction cost: 0.1% per turnover
- Initial capital: $100,000

## Troubleshooting

### Backend Issues

**"Port 8000 already in use"**
```bash
# Find and kill process on port 8000
lsof -i :8000
kill -9 <PID>
```

**"ModuleNotFoundError: No module named 'pairs_trading'"**
- Ensure you're in the correct directory
- Check PYTHONPATH in main.py (should point to `../src`)

**"No data available for symbol"**
- Check symbol spelling (use Yahoo Finance symbols)
- Verify date range is valid
- Try a different symbol like AAPL, MSFT, GOOGL

### Frontend Issues

**"Cannot GET /api/..." or CORS errors**
- Verify backend is running on http://localhost:8000
- Check vite.config.js proxy settings
- Clear browser cache (Ctrl+Shift+Delete)

**"Blank page with errors in console"**
- Check browser console (F12) for JavaScript errors
- Verify all node_modules installed: `npm install`
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`

**"Charts not rendering**
- Verify Recharts is installed: `npm list recharts`
- Check browser console for errors
- Ensure data is populated from backend

### Common Fixes

**Restart both services:**
```bash
# Kill backend
Ctrl+C in backend terminal

# Kill frontend
Ctrl+C in frontend terminal

# Start again
# Terminal 1: python backend/main.py
# Terminal 2: npm run dev (in frontend dir)
```

**Clear caches:**
```bash
# Backend (Python)
find . -type d -name __pycache__ -exec rm -rf {} +

# Frontend (Node)
rm -rf frontend/node_modules frontend/package-lock.json
npm install
```

## Performance Tips

1. **Data Caching** - Backend automatically caches market data. Repeated API calls are fast.
2. **Historical vs Live** - Use historical data (1 year) for faster analysis
3. **Reduce Symbols** - Fewer symbols = faster pair identification
4. **Browser Performance** - Close other tabs, increase browser memory allocation

## Security Notes

- ⚠️ No authentication - suitable for local/private use only
- ⚠️ Do NOT expose to public internet without authentication layer
- ⚠️ Consider adding API key validation for production

## Development Workflow

### Backend Development

1. Edit `backend/main.py`
2. Automatically reloads with `--reload` flag (add to uvicorn)
3. Test endpoints with curl or Postman

### Frontend Development

1. Edit components in `frontend/src/components/`
2. Hot Module Replacement (HMR) enabled - auto-refresh on save
3. Check browser console for errors

### Adding New Features

**Backend:**
1. Add endpoint to `main.py`
2. Call existing pairs_trading functions
3. Return JSON response

**Frontend:**
1. Create component in `frontend/src/components/`
2. Add route to `App.jsx` navigation
3. Use `fetch()` to call backend API

## Deployment

### Heroku Deployment

[Coming Soon - Procfile and configuration]

### AWS Deployment

[Coming Soon - CloudFormation templates]

### Docker Deployment

[Coming Soon - Multi-stage Dockerfile and docker-compose.yml]

## Support & Feedback

For issues or feature requests:
1. Check troubleshooting section
2. Review backend logs (port 8000)
3. Check browser console (F12)
4. Verify data is available for selected symbols

## License

Same as main pairs_trading framework

## Next Steps

- [ ] Add unit tests for API endpoints
- [ ] Implement WebSocket auto-reconnection
- [ ] Add user preferences/settings persistence
- [ ] Create additional chart types (candlesticks, heatmaps)
- [ ] Add portfolio-level risk aggregation
- [ ] Build live trading connector
- [ ] Add quantitative metrics dashboard
