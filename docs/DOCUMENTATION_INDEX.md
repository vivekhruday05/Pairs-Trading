# 📚 Documentation Index

Complete guide to the Pairs Trading Terminal. Start here!

## 🚀 Getting Started (Pick One)

| Document | Time | Purpose |
|----------|------|---------|
| [BUILD_SUMMARY.md](BUILD_SUMMARY.md) | 2 min | Overview of what was built ⭐ **START HERE** |
| [QUICK_START.md](QUICK_START.md) | 3 min | Get it running in 60 seconds |
| [TERMINAL_README.md](TERMINAL_README.md) | 10 min | Complete feature walkthrough |

## 📖 Detailed Guides

| Document | Purpose | For |
|----------|---------|-----|
| [README.md](README.md) | Framework documentation | Data scientists |
| [API_REFERENCE.md](API_REFERENCE.md) | Complete API endpoints & components | Developers |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Production deployment & extensions | DevOps/Architects |

---

## 📋 Quick Reference

### Installation

**Fastest (One Command):**
```bash
cd /home/vivek/test/gitrepo/Pairs-Trading
./start_terminal.sh
```

**Manual:**
```bash
# Terminal 1
cd backend && pip install -r requirements.txt && python main.py

# Terminal 2
cd frontend && npm install && npm run dev
```

### URLs

- Frontend: **http://localhost:3000**
- Backend: **http://localhost:8000**
- API Docs: **http://localhost:3000** (see sidebar)

### Key Files

```
Pairs-Trading/
├── backend/main.py              # FastAPI server
├── frontend/src/components/     # React components
├── start_terminal.sh            # One-click startup
├── QUICK_START.md              # 3-minute guide ⭐
├── TERMINAL_README.md          # Full docs
├── API_REFERENCE.md            # Endpoints & components
├── DEPLOYMENT_GUIDE.md         # Production setup
└── BUILD_SUMMARY.md            # What was built
```

---

## 🎯 By Use Case

### "I just want to run it"
1. Read [QUICK_START.md](QUICK_START.md)
2. Run: `./start_terminal.sh`
3. Open http://localhost:3000

### "I want to understand the architecture"
1. Read [BUILD_SUMMARY.md](BUILD_SUMMARY.md) for overview
2. Read [TERMINAL_README.md](TERMINAL_README.md) for features
3. Read [API_REFERENCE.md](API_REFERENCE.md) for technical details

### "I want to integrate with my system"
1. Read [API_REFERENCE.md](API_REFERENCE.md) for endpoints
2. Review example requests (curl/JavaScript)
3. Test endpoints with curl or Postman

### "I want to deploy to production"
1. Read [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. Choose deployment target (Docker/AWS/Heroku)
3. Follow setup steps for your platform

### "I want to extend it with custom features"
1. Read [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) "Extending" section
2. Review component structure in [API_REFERENCE.md](API_REFERENCE.md)
3. Add endpoints/components following existing patterns

---

## 🔍 Documentation Structure

```
📚 Documentation
│
├─ 🚀 Getting Started
│  ├─ BUILD_SUMMARY.md .......... What was built (overview)
│  ├─ QUICK_START.md ........... 3-minute setup ⭐
│  └─ TERMINAL_README.md ....... Features & troubleshooting
│
├─ 📖 Reference
│  ├─ API_REFERENCE.md ......... All endpoints + components
│  ├─ README.md ............... Framework docs
│  └─ DEPLOYMENT_GUIDE.md ...... Production setup
│
└─ 💾 Code
   ├─ backend/main.py ......... FastAPI server
   ├─ frontend/src/ ........... React application
   └─ src/pairs_trading/ ...... Trading core
```

---

## ✨ Feature Overview

### Terminal Tabs

| Tab | Description | Use Case |
|-----|------------|----------|
| **Dashboard** | Status overview | Quick health check |
| **Live Stream** | Real-time prices | Monitor symbols |
| **Pair Finder** | Auto pair discovery | Find tradeable pairs |
| **Signals** | Z-score signals | Generate trades |
| **Analyzer** | Live analysis | Manual testing |
| **Backtest** | Full P&L test | Strategy validation |

### Backend Endpoints

| Category | Endpoints |
|----------|-----------|
| **Data** | Download, latest price |
| **Pairs** | Identify cointegrated pairs |
| **Signals** | Generate z-score signals |
| **Backtest** | Run full strategy test |
| **Stream** | WebSocket live updates |

See [API_REFERENCE.md](API_REFERENCE.md) for complete list.

---

## 🛠️ Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Port in use | See TERMINAL_README.md "Troubleshooting" |
| No data | Try different symbols (AAPL, MSFT, GOOGL) |
| Blank page | Clear cache, restart frontend |
| API error | Check backend logs: `tail /tmp/backend.log` |

### Where to Find Help

1. **Setup Issues** → [QUICK_START.md](QUICK_START.md)
2. **Feature Questions** → [TERMINAL_README.md](TERMINAL_README.md)
3. **API/Component Questions** → [API_REFERENCE.md](API_REFERENCE.md)
4. **Deployment Issues** → [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

## 📊 System Requirements

- Python 3.11+
- Node.js 16+
- 4GB RAM (8GB recommended)
- Intel i5+ or equivalent
- 500MB disk space

---

## 🚀 Quick Start Commands

```bash
# One-liner to start everything
cd /home/vivek/test/gitrepo/Pairs-Trading && ./start_terminal.sh

# Stop everything
./stop_terminal.sh

# Backend only
cd backend && python main.py

# Frontend only  
cd frontend && npm run dev

# Test API health
curl http://localhost:8000/api/health

# Build for production
cd frontend && npm run build
```

---

## 🎓 Learning Path

**Beginner:**
1. Read [BUILD_SUMMARY.md](BUILD_SUMMARY.md)
2. Follow [QUICK_START.md](QUICK_START.md)
3. Click through all tabs
4. Run one backtest

**Intermediate:**
1. Read [TERMINAL_README.md](TERMINAL_README.md) features
2. Review [API_REFERENCE.md](API_REFERENCE.md)
3. Test API endpoints with curl
4. Try different parameter combinations

**Advanced:**
1. Read [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. Study backend code: `backend/main.py`
3. Study frontend components: `frontend/src/components/`
4. Add custom endpoints/features

---

## 📞 Support & Resources

### Documentation
- **Quick Setup** → [QUICK_START.md](QUICK_START.md)
- **Full Features** → [TERMINAL_README.md](TERMINAL_README.md)
- **API Details** → [API_REFERENCE.md](API_REFERENCE.md)
- **Production** → [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

### External Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev)
- [Recharts Examples](https://recharts.org/)
- [Tailwind CSS Docs](https://tailwindcss.com/)

### Code repositories
- Frontend: `frontend/src/components/`
- Backend: `backend/main.py`
- Core: `src/pairs_trading/`

---

## ✅ Checklist

- [ ] Read BUILD_SUMMARY.md
- [ ] Run start_terminal.sh 
- [ ] Access http://localhost:3000
- [ ] Try Live Stream tab
- [ ] Try Pair Finder tab
- [ ] Run a Backtest
- [ ] Read TERMINAL_README.md for advanced features
- [ ] Deploy to production (optional)

---

## 🎉 You're Ready!

Everything is documented and ready to use.

**Next step:** Choose an option above and get started! 🚀

---

**Version:** 1.0.0  
**Last Updated:** 2024  
**Status:** Production Ready ✅
