## ⚡ Pairs Trading Terminal - QUICK OVERVIEW

You now have a **professional Bloomberg Terminal-style interface** for your pairs trading framework!

### 📦 What Was Built

**Backend (FastAPI)**
- `backend/main.py` - REST API with 15+ endpoints
- WebSocket support for live streaming
- Full integration with your pairs trading core
- Built-in CORS for frontend communication

**Frontend (React + Vite)**
- `frontend/` - Production-ready React application
- Professional dark theme (Bloomberg Terminal style)
- Interactive charts using Recharts
- Real-time data updates and visualizations

**Documentation**
- `QUICK_START.md` - 3-minute setup guide
- `TERMINAL_README.md` - Comprehensive documentation
- `API_REFERENCE.md` - Complete API and component reference
- `start_terminal.sh` - One-command startup script

---

### 🚀 Get Started in 60 Seconds

**Option 1: Automatic (Recommended)**
```bash
cd /home/vivek/test/gitrepo/Pairs-Trading
chmod +x start_terminal.sh
./start_terminal.sh
# Opens http://localhost:3000 automatically
```

**Option 2: Manual**
```bash
# Terminal 1 - Backend
cd backend && pip install -r requirements.txt && python main.py

# Terminal 2 - Frontend
cd frontend && npm install && npm run dev
```

Then open **http://localhost:3000** in your browser.

---

### 📊 Features You Can Use Right Now

1. **Live Stream** - Watch real-time prices for multiple symbols
2. **Pair Finder** - Automatically discover cointegrated pairs
3. **Signals** - Generate z-score trading signals with charts
4. **Analyzer** - Manual or automatic pair analysis
5. **Backtest** - Full pipeline with risk controls and P&L

---

### 🏗️ Architecture

```
🌐 Frontend (React)         ↔️ HTTP/WebSocket ↔️ 🔧 Backend (FastAPI)
├ Dashboard                                        ├ /api/data/
├ Live Stream               ↔️ Real-time data      ├ /api/pairs/
├ Pair Finder                                      ├ /api/signals/
├ Signals                                          ├ /api/backtest/
├ Analyzer                                         └ /ws/ streams
└ Backtest                                                   ↓
                                                  📚 Pairs Trading Core
                                                  ├ Data Download
                                                  ├ Pair Identification
                                                  ├ Signal Generation
                                                  ├ Risk Management
                                                  └ Backtesting
```

---

### 📝 File Structure

```
Pairs-Trading/
├── backend/
│   ├── main.py                          # FastAPI server (Port 8000)
│   └── requirements.txt                 # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx                     # Main React app
│   │   ├── components/
│   │   │   ├── Navigation.jsx          # Tab navigation
│   │   │   ├── DataStreaming.jsx       # Live prices
│   │   │   ├── PairIdentification.jsx  # Pair finder
│   │   │   ├── SignalGeneration.jsx    # Signals
│   │   │   ├── Backtester.jsx          # Full backtest
│   │   │   └── PairAnalyzer.jsx        # Analyzer
│   │   └── index.css                   # Styling
│   ├── package.json                    # Node dependencies
│   ├── tailwind.config.js              # Tailwind config
│   └── vite.config.js                  # Vite config
├── QUICK_START.md                      # 3-minute setup
├── TERMINAL_README.md                  # Full documentation
├── API_REFERENCE.md                    # API + components
├── start_terminal.sh                   # One-click startup
└── stop_terminal.sh                    # Shutdown script
```

---

### 🔗 API Endpoints (All Running on: http://localhost:8000)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Check if API is online |
| `/api/config/defaults` | GET | Get default parameters |
| `/api/data/download` | POST | Download market data |
| `/api/data/latest/{symbol}` | GET | Get latest price |
| `/api/pairs/identify` | POST | Find cointegrated pairs |
| `/api/signals/generate` | POST | Generate z-score signals |
| `/api/backtest/run` | POST | Run full backtest |
| `/ws/live-stream/{symbol}` | WS | Live price stream |
| `/ws/pair-stream/{x}/{y}` | WS | Live pair stream |

See `API_REFERENCE.md` for complete documentation with examples.

---

### 🎯 Example Workflows

**Workflow 1: Find & Test a Pair**
1. Go to **PAIR FINDER** tab
2. Add your symbols (AAPL, MSFT, GOOGL, etc.)
3. Click **FIND COINTEGRATED PAIRS**
4. See results with statistical metrics
5. Click on a pair to analyze

**Workflow 2: Manual Analysis**
1. Go to **ANALYZER** tab
2. Click **MANUAL SELECT** mode
3. Enter symbols (e.g., AAPL / MSFT)
4. Click **RUN ANALYSIS**
5. View live portfolio performance chart

**Workflow 3: Full Backtest with Risk Controls**
1. Go to **BACKTEST** tab
2. Enter pair: AAPL / MSFT
3. Set date range: 2023-01-01 to 2024-01-01
4. Configure: stop loss 3%, max hold 20 days
5. Click **RUN BACKTEST**
6. Download report with metrics

---

### 💡 Pro Tips

- **Faster Analysis** - Use recent data (1-2 years) instead of 10 years
- **Pair Finding** - Works best with 5-10 symbols
- **Live Updates** - Charts auto-refresh when new data arrives
- **Export** - Download backtest reports as text files
- **Performance** - First API call caches data; subsequent calls are fast

---

### 🛠️ Troubleshooting

**"Cannot connect to backend"**
- Ensure backend started: `python backend/main.py`
- Check port 8000 is not in use

**"No data available"**
- Try different symbols (AAPL, MSFT, GOOGL work best)
- Verify date range is valid
- Check internet connection

**"Blank frontend page"**
- Clear browser cache: Ctrl+Shift+Delete
- Restart frontend: `npm run dev` in frontend folder
- Check browser console (F12) for errors

**Full troubleshooting in `TERMINAL_README.md`**

---

### 📚 Documentation

- **`QUICK_START.md`** ← Start here! 3-minute setup
- **`TERMINAL_README.md`** ← Complete feature guide
- **`API_REFERENCE.md`** ← All endpoints and components
- **`README.md`** ← Framework documentation

---

### 🎨 UI Features

✨ **Professional Design**
- Bloomberg Terminal-inspired dark theme
- Clean typography with monospace font
- Responsive layout (desktop/tablet/mobile)
- Color-coded metrics (green for profit, red for loss)
- Smooth animations and transitions

📊 **Interactive Charts**
- Recharts for professional visualizations
- Line charts for equity curves
- Bar charts for P&L breakdown
- Combo charts for multi-metric display
- Tooltips and legends on hover

🎮 **Intuitive Controls**
- Tab-based navigation
- Real-time parameter adjustment
- One-click analysis & backtest
- Report downloads
- Live data streaming

---

### ✅ What's Working

- ✅ Live data streaming for multiple symbols
- ✅ Automated pair identification (correlation + cointegration)
- ✅ Z-score signal generation with visualization
- ✅ Full backtesting with transaction costs
- ✅ Risk controls (stop-loss, time-stop, VaR)
- ✅ P&L accounting and equity curves
- ✅ Manual & automatic pair selection
- ✅ Interactive charts and dashboards
- ✅ Professional Bloomberg Terminal styling
- ✅ One-command startup

---

### 🚀 Next Steps

1. **Run it** - Execute `./start_terminal.sh`
2. **Explore** - Click through all tabs
3. **Test** - Run a backtest on your favorite pair
4. **Customize** - Adjust parameters in the UI
5. **Share** - Show colleagues/friends!

---

### 📞 Support

**For Issues:**
1. Check `TERMINAL_README.md` troubleshooting section
2. Review `API_REFERENCE.md` for endpoint details
3. Check browser console (F12) for errors
4. Verify backend is running: `curl http://localhost:8000/api/health`

**For Development:**
- Modify frontend components in `frontend/src/components/`
- Add API endpoints in `backend/main.py`
- Use existing pairs trading core functions
- Changes auto-reload with HMR (Hot Module Replacement)

---

### 📄 License

Same as main pairs_trading framework

---

## 🎉 You're All Set!

Your professional pairs trading terminal is ready to use. 

**Start now:**
```bash
cd /home/vivek/test/gitrepo/Pairs-Trading
./start_terminal.sh
```

**Then visit:** http://localhost:3000

Enjoy! 🚀
