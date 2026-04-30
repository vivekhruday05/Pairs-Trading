# Deployment & Extension Guide

Guide for deploying the Pairs Trading Terminal to production and extending it with custom features.

## Table of Contents
1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment](#cloud-deployment)
4. [Extending the System](#extending-the-system)
5. [Performance Optimization](#performance-optimization)
6. [Security Hardening](#security-hardening)

---

## Local Development

### Development Mode with Hot Reload

**Backend with Auto-Reload:**
```bash
cd backend
pip install -r requirements.txt
pip install python-dotenv
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend with Hot Module Replacement (HMR):**
```bash
cd frontend
npm install
npm run dev
```

Both services now auto-reload on file changes.

### Debug Mode

**Backend Debug Logging:**
```python
# In backend/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Frontend Debug Mode:**
```bash
cd frontend
npm run dev -- --debug
```

---

## Docker Deployment

### Build Single Container

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.11-slim as backend
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

FROM node:18-alpine as frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend . .
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY --from=backend /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=frontend-build /app/frontend/dist ./frontend/dist
COPY backend/ ./backend/
COPY src/ ./src/

ENV PYTHONPATH=/app/src
EXPOSE 8000

CMD ["python", "backend/main.py"]
```

**Build and Run:**
```bash
docker build -t pairs-trading-terminal .
docker run -p 8000:8000 -p 3000:3000 pairs-trading-terminal
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - .cache:/app/.cache
    command: python main.py

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - VITE_API_URL=http://backend:8000

volumes:
  cache:
```

**Run:**
```bash
docker-compose up
```

---

## Cloud Deployment

### Heroku Deployment

**1. Create Procfile:**
```
web: python backend/main.py
```

**2. Create heroku.yml:**
```yaml
build:
  docker:
    web: Dockerfile
run:
  web: python backend/main.py
```

**3. Deploy:**
```bash
heroku create pairs-trading-terminal
git push heroku main
```

### AWS Deployment

**1. Create EC2 Instance:**
```bash
# Ubuntu 22.04 LTS
ssh ubuntu@your-instance-ip

# Install dependencies
sudo apt update
sudo apt install python3-pip nodejs npm git

# Clone repo
git clone https://your-repo-url
cd Pairs-Trading

# Install
pip install -r backend/requirements.txt
cd frontend && npm install && npm run build
```

**2. Configure Nginx:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /app/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**3. Run Services:**
```bash
# Backend (daemonize)
nohup python backend/main.py > backend.log 2>&1 &

# Frontend is served by Nginx from dist/
```

### Google Cloud Run

**1. Create app.yaml:**
```yaml
runtime: python311
env: flex

env_variables:
  PYTHONUNBUFFERED: "1"

handlers:
  - url: /.*
    script: auto
```

**2. Deploy:**
```bash
gcloud app deploy
```

---

## Extending the System

### Adding New API Endpoints

**1. Backend Extension (main.py):**

```python
@app.post("/api/strategy/backtest-multiple")
async def backtest_multiple_pairs(
    pairs: List[dict],
    start: str,
    end: str,
    initial_capital: float = 100000
):
    """Run backtest on multiple pairs and compare results"""
    results = []
    
    for pair in pairs:
        result = await run_backtest(
            symbol_x=pair['x'],
            symbol_y=pair['y'],
            start=start,
            end=end,
            initial_capital=initial_capital
        )
        results.append(result)
    
    return {
        "status": "success",
        "results": results,
        "best_pair": max(results, key=lambda x: x['summary']['net_pnl'])
    }
```

**2. Frontend Component (PairComparison.jsx):**

```jsx
export default function PairComparison() {
  const [pairs, setPairs] = useState([
    { x: 'AAPL', y: 'MSFT' },
    { x: 'AAPL', y: 'GOOGL' }
  ]);
  const [results, setResults] = useState([]);

  const runComparison = async () => {
    const res = await fetch('http://localhost:8000/api/strategy/backtest-multiple', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pairs,
        start: '2023-01-01',
        end: '2024-01-01'
      })
    });
    const data = await res.json();
    setResults(data.results);
  };

  return (
    <div className="...">
      <button onClick={runComparison}>COMPARE PAIRS</button>
      {results.map(r => (
        <div key={r.pair}>
          {r.pair}: $({r.summary.net_pnl.toFixed(2)} {result.summary.total_return.toFixed(2)}%)
        </div>
      ))}
    </div>
  );
}
```

### Adding WebSocket Features

**Live Trading Recommendations:**

```python
@app.websocket("/ws/recommendations")
async def websocket_recommendations(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(60)  # Check every minute
            
            # Analyze all pairs
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']
            recommendations = []
            
            for i, sym_x in enumerate(symbols):
                for sym_y in symbols[i+1:]:
                    pair_data = await analyze_pair(sym_x, sym_y)
                    if pair_data['signal'] != 'FLAT':
                        recommendations.append(pair_data)
            
            await websocket.send_json({
                "type": "recommendations",
                "data": recommendations,
                "timestamp": datetime.now().isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

### Adding Database Persistence

**Using SQLite:**

```bash
pip install sqlalchemy sqlite
```

**models.py:**

```python
from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
engine = create_engine('sqlite:///backtest_results.db')

class BacktestRecord(Base):
    __tablename__ = "backtests"
    
    id = Column(String, primary_key=True)
    symbol_x = Column(String)
    symbol_y = Column(String)
    net_pnl = Column(Float)
    total_return = Column(Float)
    max_drawdown = Column(Float)
    timestamp = Column(DateTime, default=datetime.now)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
```

**Save Results:**

```python
@app.post("/api/backtest/run")
async def run_backtest(...):
    # ... run backtest ...
    
    # Save to DB
    session = Session()
    record = BacktestRecord(
        id=f"{symbol_x}_{symbol_y}_{datetime.now().timestamp()}",
        symbol_x=symbol_x,
        symbol_y=symbol_y,
        net_pnl=result.summary.net_pnl,
        total_return=result.summary.total_return,
        max_drawdown=result.summary.max_drawdown
    )
    session.add(record)
    session.commit()
    
    return result
```

### Adding Authentication

```bash
pip install python-jose python-dotenv
```

**auth.py:**

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException
import os

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Use in endpoints
@app.post("/api/backtest/run")
async def run_backtest(..., current_user: dict = Depends(verify_token)):
    # Only authenticated users can run backtests
    ...
```

---

## Performance Optimization

### 1. Caching Strategy

**Add Redis Cache:**

```bash
pip install redis
```

```python
import redis
cache = redis.Redis(host='localhost', port=6379, db=0)

@app.get("/api/data/latest/{symbol}")
async def get_latest_price(symbol: str):
    # Check cache first
    cached = cache.get(f"price:{symbol}")
    if cached:
        return json.loads(cached)
    
    # Fetch and cache
    price = fetch_price(symbol)
    cache.setex(f"price:{symbol}", 300, json.dumps(price))  # 5 min TTL
    return price
```

### 2. Database Indexing

```python
# For large backtest result tables
engine.execute("""
CREATE INDEX idx_pair ON backtests(symbol_x, symbol_y);
CREATE INDEX idx_date ON backtests(timestamp);
""")
```

### 3. Async Queries

```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine("sqlite+aiosqlite:///data.db")

@app.get("/api/backtest/results")
async def get_results():
    async with AsyncSession(engine) as session:
        results = await session.execute(
            select(BacktestRecord).limit(100)
        )
        return results.scalars().all()
```

### 4. Frontend Optimization

**Code Splitting:**

```javascript
// App.jsx
const Dashboard = React.lazy(() => import('./components/Dashboard'));
const Backtest = React.lazy(() => import('./components/Backtester'));

export default function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/backtest" element={<Backtest />} />
      </Routes>
    </Suspense>
  );
}
```

**Image Optimization:**

```bash
npm install sharp
# Compress images before deployment
```

---

## Security Hardening

### 1. API Rate Limiting

```bash
pip install slowapi
```

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/backtest/run")
@limiter.limit("10/minute")
async def run_backtest(request: Request, ...):
    # Limited to 10 calls per minute
    ...
```

### 2. Input Validation

```python
from pydantic import BaseModel, validator

class BacktestRequest(BaseModel):
    symbol_x: str
    symbol_y: str
    initial_capital: float
    
    @validator('symbol_x', 'symbol_y')
    def validate_symbol(cls, v):
        if len(v) > 5 or len(v) < 1:
            raise ValueError('Invalid symbol')
        return v.upper()
    
    @validator('initial_capital')
    def validate_capital(cls, v):
        if v < 1000 or v > 10_000_000:
            raise ValueError('Capital must be 1k-10m')
        return v
```

### 3. HTTPS/TLS

**Using Let's Encrypt:**

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com
```

**Nginx Config:**

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # ... rest of config ...
}
```

### 4. Environment Variables

```bash
# Create .env
API_KEY=your-secret-key
DB_URL=postgresql://user:pass@localhost/pairs_trading
CORS_ORIGINS=https://yourdomain.com
```

```python
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ORIGINS", "*")],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5. SQL Injection Prevention

Always use parameterized queries:

```python
# Good
session.query(BacktestRecord).filter_by(symbol_x=symbol_x).all()

# Bad - DO NOT DO THIS
query = f"SELECT * FROM backtests WHERE symbol_x = '{symbol_x}'"
session.execute(query)
```

---

## Monitoring & Logging

### 1. Application Monitoring

```bash
pip install prometheus-client
```

```python
from prometheus_client import Counter, Histogram

request_count = Counter('api_requests', 'Total API requests')
request_duration = Histogram('api_request_duration', 'Request duration')

@app.post("/api/backtest/run")
@request_duration.time()
async def run_backtest(...):
    request_count.inc()
    # ...
```

### 2. Structured Logging

```bash
pip install python-json-logger
```

```python
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)

# Usage
logger.info("Backtest started", extra={"pair": "AAPL/MSFT"})
```

---

## Maintenance & Updates

### 1. Dependencies Update

```bash
# Check for outdated packages
pip list --outdated

# Update pip
pip install --upgrade pip

# Update specific package
pip install --upgrade fastapi

# Update all (use caution!)
pip install --upgrade -r requirements.txt
```

### 2. Database Backups

```bash
# SQLite backup
cp backtest_results.db backtest_results.backup.db

# PostgreSQL backup
pg_dump pairs_trading > backup.sql

# Restore
psql pairs_trading < backup.sql
```

### 3. Monitoring Health

```bash
# Check backend health
curl http://localhost:8000/api/health

# Monitor logs
tail -f backend.log

# Check resource usage
watch -n 1 'ps aux | grep python'
```

---

## Troubleshooting Deployment

### Common Issues

| Issue | Solution |
|-------|----------|
| Port 8000 in use | `sudo lsof -i :8000 && kill -9 <PID>` |
| CORS errors | Check `CORS_ORIGINS` in .env |
| Database locked | Restart backend |
| Out of memory | Reduce data window or scale up instance |
| SSL certificate error | Run `certbot renew` |

---

## Next Steps

1. **Production Deploy** - Choose cloud provider (AWS/GCP/Heroku)
2. **Add Authentication** - Implement user login
3. **Database** - Switch to PostgreSQL for production
4. **Monitoring** - Setup Prometheus + Grafana
5. **CI/CD** - Automate testing and deployment with GitHub Actions
6. **Live Trading** - Add real broker integration

---

## Support

For deployment questions:
- Check cloud provider documentation
- Review Python/Node.js best practices
- Test locally before deploying
- Use application monitoring to catch issues
