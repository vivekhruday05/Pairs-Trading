# Pairs Trading Terminal - API Reference & Component Guide

Complete documentation for backend APIs, frontend components, and integration points.

## Table of Contents
1. [Backend API Reference](#backend-api-reference)
2. [Frontend Components](#frontend-components)
3. [Data Flow](#data-flow)
4. [Integration Examples](#integration-examples)

---

## Backend API Reference

All endpoints run on `http://localhost:8000`

### Health & Config

#### `GET /api/health`
Check if backend is online.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

#### `GET /api/config/defaults`
Get default parameters for all operations.

**Response:**
```json
{
  "signals": {
    "entry_threshold": 2.0,
    "exit_threshold": 0.5,
    "target_gross_exposure": 1.0
  },
  "risk": {
    "stop_loss_fraction": 0.03,
    "max_holding_period": 20,
    "var_window": 20,
    "var_confidence": 0.05
  },
  "backtest": {
    "transaction_cost_rate": 0.001,
    "initial_capital": 100000.0
  },
  "pair_identification": {
    "min_correlation": 0.8,
    "correlation_lag": 1
  }
}
```

---

### Data Endpoints

#### `POST /api/data/download`
Download market data for multiple symbols.

**Parameters:**
- `symbols` (array): List of ticker symbols
- `start` (string, optional): Start date in YYYY-MM-DD format. Default: 2024-01-01
- `end` (string, optional): End date in YYYY-MM-DD format. Default: Today

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/data/download \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "start": "2023-01-01",
    "end": "2024-01-01"
  }'
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "AAPL": {
      "dates": ["2023-01-01", "2023-01-02", ...],
      "closes": [150.2, 151.5, ...],
      "volumes": [52000000, 48000000, ...],
      "rows": 252
    }
  }
}
```

#### `GET /api/data/latest/{symbol}`
Get latest price snapshot for a symbol.

**Example Request:**
```bash
curl http://localhost:8000/api/data/latest/AAPL
```

**Response:**
```json
{
  "symbol": "AAPL",
  "date": "2024-01-15",
  "close": 185.42,
  "volume": 52000000,
  "change": 2.3
}
```

---

### Pair Identification

#### `POST /api/pairs/identify`
Identify cointegrated pairs using correlation and Engle-Granger test.

**Parameters:**
- `symbols` (array): List of symbols to analyze
- `start` (string, optional): Start date. Default: 2024-01-01
- `end` (string, optional): End date. Default: Today
- `min_correlation` (number, optional): Minimum correlation threshold. Default: 0.8
- `correlation_lag` (number, optional): Lag for correlation. Default: 1
- `max_results` (number, optional): Maximum pairs to return. Default: 10

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/pairs/identify \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
    "start": "2023-01-01",
    "end": "2024-01-01",
    "min_correlation": 0.8,
    "max_results": 5
  }'
```

**Response:**
```json
{
  "status": "success",
  "total_analyzed": 10,
  "pairs": [
    {
      "symbol_x": "AAPL",
      "symbol_y": "MSFT",
      "correlation": 0.847,
      "coint_pvalue": 0.0234,
      "adf_pvalue": 0.0156,
      "granger_pvalue": 0.0891,
      "half_life": 12.5,
      "zscore": -0.34
    }
  ],
  "count": 1
}
```

---

### Signal Generation

#### `POST /api/signals/generate`
Generate z-score trading signals for a pair.

**Parameters:**
- `symbol_x` (string): First symbol in pair
- `symbol_y` (string): Second symbol in pair
- `start` (string, optional): Start date. Default: 2024-01-01
- `end` (string, optional): End date. Default: Today
- `entry_threshold` (number, optional): Entry z-score. Default: 2.0
- `exit_threshold` (number, optional): Exit z-score. Default: 0.5
- `target_gross_exposure` (number, optional): Target exposure. Default: 1.0

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/signals/generate \
  -H "Content-Type: application/json" \
  -d '{
    "symbol_x": "AAPL",
    "symbol_y": "MSFT",
    "start": "2023-01-01",
    "end": "2024-01-01",
    "entry_threshold": 2.0,
    "exit_threshold": 0.5,
    "target_gross_exposure": 1.0
  }'
```

**Response:**
```json
{
  "status": "success",
  "pair": "AAPL/MSFT",
  "signals": {
    "dates": ["2023-01-01", "2023-01-02", ...],
    "spread": [0.12, -0.05, ...],
    "zscore": [0.45, -0.15, ...],
    "position": [0, 0, 1, 1, 0, ...],
    "weight_x": [0, 0, 0.5, 0.5, 0, ...],
    "weight_y": [0, 0, -0.5, -0.5, 0, ...],
    "gross_exposure": [0, 0, 1.0, 1.0, 0, ...]
  },
  "rows": 252
}
```

---

### Backtesting

#### `POST /api/backtest/run`
Run full backtest with signal generation, risk controls, and P&L accounting.

**Parameters:**
- `symbol_x` (string): First symbol
- `symbol_y` (string): Second symbol
- `start` (string, optional): Start date. Default: 2024-01-01
- `end` (string, optional): End date. Default: Today
- `entry_threshold` (number, optional): Entry z-score. Default: 2.0
- `exit_threshold` (number, optional): Exit z-score. Default: 0.5
- `target_gross_exposure` (number, optional): Target exposure. Default: 1.0
- `stop_loss_fraction` (number, optional): Stop loss %. Default: 0.03
- `max_holding_period` (number, optional): Max days to hold. Default: 20
- `transaction_cost_rate` (number, optional): Cost per turnover. Default: 0.001
- `initial_capital` (number, optional): Starting capital. Default: 100000

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/backtest/run \
  -H "Content-Type: application/json" \
  -d '{
    "symbol_x": "AAPL",
    "symbol_y": "MSFT",
    "start": "2023-01-01",
    "end": "2024-01-01",
    "stop_loss_fraction": 0.03,
    "max_holding_period": 20,
    "transaction_cost_rate": 0.001,
    "initial_capital": 100000
  }'
```

**Response:**
```json
{
  "status": "success",
  "pair": "AAPL/MSFT",
  "summary": {
    "total_return": 3.21,
    "gross_pnl": 3239.76,
    "net_pnl": 3210.81,
    "total_costs": 28.95,
    "max_drawdown": -3.72,
    "ending_equity": 100003.21,
    "sharpe_ratio": 1.234
  },
  "backtest": {
    "dates": ["2023-01-01", "2023-01-02", ...],
    "gross_pnl": [0, 5.2, -2.1, ...],
    "net_pnl": [0, 5.0, -2.3, ...],
    "equity_curve": [100000, 100005, 100002.7, ...],
    "position": [0, 1, 1, 0, ...],
    "transaction_cost": [0, 0.2, 0.2, 0, ...]
  },
  "rows": 252
}
```

---

### WebSocket Streams

#### `WS /ws/live-stream/{symbol}`
Real-time price updates for a symbol (every 5 seconds).

**Connect:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/live-stream/AAPL');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`${data.symbol}: $${data.price} (${data.change}%)`);
};
```

**Message Format:**
```json
{
  "type": "price_update",
  "symbol": "AAPL",
  "date": "2024-01-15T10:30:00",
  "price": 185.42,
  "volume": 52000000,
  "change": 2.3,
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

#### `WS /ws/pair-stream/{symbol_x}/{symbol_y}`
Real-time pair z-score and spread updates (every 10 seconds).

**Connect:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/pair-stream/AAPL/MSFT');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`${data.pair} Z-Score: ${data.data.zscore[-1]}`);
};
```

**Message Format:**
```json
{
  "type": "pair_update",
  "pair": "AAPL/MSFT",
  "data": {
    "dates": ["2024-01-12", "2024-01-13", ...],
    "zscore": [0.45, -0.15, ...],
    "spread": [0.12, -0.05, ...],
    "position": [0, 0, 1, 1, ...]
  },
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

---

## Frontend Components

### Navigation.jsx
Top navigation with tabs for different views.

**Props:**
- `currentView` (string): Current active view ID
- `setCurrentView` (function): Callback to change view

**Views:**
- `dashboard` - Overview
- `streaming` - Live data
- `pair-finder` - Pair identification
- `signals` - Signal generation
- `analyzer` - Pair analysis
- `backtest` - Backtesting

---

### DataStreaming.jsx
Real-time price updates for selected symbols.

**Features:**
- Add/remove symbols dynamically
- Live price grid with changes
- Auto-refresh every 10 seconds
- Price action chart

**Key Functions:**
- `addSymbol()` - Add ticker to watch list
- `removeSymbol(sym)` - Remove ticker
- `fetchLatestData()` - Refresh prices

---

### PairIdentification.jsx
Automated pair discovery using cointegration analysis.

**Features:**
- Configurable date range
- Correlation threshold adjustment
- Results show statistical metrics
- Top pairs ranked by cointegration p-value

**Key Functions:**
- `identifyPairs()` - Run analysis
- Works with 2+ symbols

---

### SignalGeneration.jsx
Z-score signal generation for manual pair selection.

**Features:**
- Interactive charts for spread/z-score/position
- Tunable entry/exit thresholds
- Exposure visualization
- Real-time parameter adjustment

**Charts:**
- Z-Score & Spread (bar + line)
- Position & Exposure (bar + line)

---

### Backtester.jsx
Full pipeline execution with risk controls.

**Features:**
- All parameters configurable
- Risk controls included by default
- Summary metrics display
- Multiple charts (equity, P&L, positions)
- Downloadable report

**Output Metrics:**
- Total return, Net/Gross P&L
- Transaction costs, Max drawdown
- Sharpe ratio, Ending equity

---

### PairAnalyzer.jsx
Dual-mode pair analysis (manual or auto).

**Modes:**
1. **Manual**: Enter symbols directly
2. **Auto**: System suggests cointegrated pairs

**Features:**
- Historical or live data mode
- Full performance visualization
- Real-time pair ranking

---

## Data Flow

```
┌─────────────────┐
│  Frontend UI    │
│  (React/Vite)   │
└────────┬────────┘
         │ HTTP/JSON
         ▼
┌─────────────────────┐
│  FastAPI Backend    │
│  (main.py)          │
└────────┬────────────┘
         │ Python
         ▼
┌──────────────────────────┐
│  Pairs Trading Core      │
│  (src/pairs_trading/)    │
│                          │
│  - DataDownloader        │
│  - PairIdentificationEngine
│  - PairSignalEngine      │
│  - PairRiskEngine        │
│  - PairBacktestEngine    │
└──────────────────────────┘
         │
         ▼
┌──────────────────────────┐
│  External Data Providers │
│                          │
│  - Yahoo Finance         │
│  - Stooq                 │
└──────────────────────────┘
```

---

## Integration Examples

### Example 1: Fetch Pairs & Generate Signals (Frontend)

```javascript
// Get all cointegrated pairs
const response = await fetch('http://localhost:8000/api/pairs/identify', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    symbols: ['AAPL', 'MSFT', 'GOOGL'],
    min_correlation: 0.8
  })
});

const pairs = await response.json();
console.log('Found pairs:', pairs.count);

// Generate signals for top pair
const topPair = pairs.pairs[0];
const signals = await fetch('http://localhost:8000/api/signals/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    symbol_x: topPair.symbol_x,
    symbol_y: topPair.symbol_y,
    entry_threshold: 2.0
  })
});

const signalData = await signals.json();
console.log('Signals generated:', signalData.rows);
```

### Example 2: Run Backtest & Display Results (Frontend)

```javascript
const backtest = await fetch('http://localhost:8000/api/backtest/run', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    symbol_x: 'AAPL',
    symbol_y: 'MSFT',
    start: '2023-01-01',
    end: '2024-01-01',
    initial_capital: 100000,
    stop_loss_fraction: 0.03
  })
});

const result = await backtest.json();

// Display summary
console.log(`Net P&L: $${result.summary.net_pnl.toFixed(2)}`);
console.log(`Return: ${result.summary.total_return.toFixed(2)}%`);
console.log(`Max Drawdown: ${result.summary.max_drawdown.toFixed(2)}%`);

// Chart equity curve
const chartData = result.backtest.dates.map((date, i) => ({
  date,
  equity: result.backtest.equity_curve[i]
}));
// Pass chartData to LineChart component
```

### Example 3: Stream Live Pair Updates (Frontend)

```javascript
function StreamPairData(symbolX, symbolY) {
  const ws = new WebSocket(
    `ws://localhost:8000/ws/pair-stream/${symbolX}/${symbolY}`
  );

  ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    const lastZscore = update.data.zscore[update.data.zscore.length - 1];
    
    if (lastZscore > 2.0) {
      console.log(`BUY SIGNAL: ${update.pair} Z-Score = ${lastZscore}`);
    } else if (lastZscore < -2.0) {
      console.log(`SELL SIGNAL: ${update.pair} Z-Score = ${lastZscore}`);
    }
  };

  return ws;
}
```

---

## Error Handling

All endpoints return errors in this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common Errors:**

| Status | Message | Solution |
|--------|---------|----------|
| 400 | "Failed to identify pairs" | Check symbols and date range |
| 400 | "No data available" | Symbol not found or date too old |
| 500 | "Internal server error" | Backend crashed - restart it |
| Connection refused | Backend not running | Start backend on port 8000 |

---

## Performance Considerations

1. **Caching** - Market data is cached disk-based. First call is slow, subsequent calls fast.
2. **Pair Analysis** - With N symbols, analyzes N*(N-1)/2 pairs. More symbols = slower.
3. **Charts** - Rendering 1000+ data points may lag. Use data windowing.
4. **Backtest** - Full 10- years of data can take 30+ seconds.

**Optimization Tips:**
- Use recent data ranges (1-2 years)
- Limit symbols to 5-10 for pair finding
- Reduce max results for pair identification
- Use browser DevTools Performance tab

---

## Authentication & Security

Currently no authentication. For production:

1. Add API key validation
2. Rate limiting per IP
3. HTTPS/WSS only
4. CORS restrictions
5. Input validation

See `backend/main.py` for CORS configuration.

---

## Monitoring & Debugging

### Backend Logs

Look for:
```
INFO:     Started server process
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Frontend Logs

Check browser console (F12):
- Network tab for API calls
- Console tab for JavaScript errors
- Application tab for WebSocket connections

### Test Endpoints

```bash
# API health
curl http://localhost:8000/api/health

# Config
curl http://localhost:8000/api/config/defaults

# Data download (single symbol)
curl -X POST http://localhost:8000/api/data/download \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL"]}'
```

---

## What's Next?

- [ ] Add WebSocket auto-reconnection
- [ ] Implement user authentication
- [ ] Portfolio-level risk aggregation
- [ ] Paper trading mode
- [ ] Live order execution
- [ ] Advanced charting (candlesticks, heatmaps)
- [ ] Mobile app (React Native)
- [ ] Docker deployment
