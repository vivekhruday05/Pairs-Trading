"""
FastAPI backend for Pairs Trading Terminal
Exposes all pairs-trading functionality via REST and WebSocket APIs
"""

import asyncio
import math
from datetime import datetime, timedelta
from typing import List, Optional
from enum import Enum

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import pandas as pd
import json

# Add parent directory to path to import pairs_trading
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pairs_trading.data import DataDownloader
from pairs_trading.data.models import Instrument
from pairs_trading import (
    PairIdentificationEngine,
    PairSignalEngine,
    PairBacktestEngine,
    SignalParameters,
    BacktestParameters,
    RiskParameters
)

# ============================================================================
# Pydantic Models for Request Bodies
# ============================================================================

class DownloadRequest(BaseModel):
    symbols: List[str]
    start: str = "2024-01-01"
    end: Optional[str] = None

class PairIdentifyRequest(BaseModel):
    symbols: List[str]
    start: str = "2024-01-01"
    end: Optional[str] = None
    min_correlation: float = 0.8
    correlation_lag: int = 1
    max_results: int = 10

class SignalGenerateRequest(BaseModel):
    symbol_x: str
    symbol_y: str
    start: str = "2024-01-01"
    end: Optional[str] = None
    entry_threshold: float = 2.0
    exit_threshold: float = 0.5
    target_gross_exposure: float = 1.0

class BacktestRequest(BaseModel):
    symbol_x: str
    symbol_y: str
    start: str = "2024-01-01"
    end: Optional[str] = None
    entry_threshold: float = 2.0
    exit_threshold: float = 0.5
    target_gross_exposure: float = 1.0
    stop_loss_fraction: float = 0.03
    max_holding_period: int = 20
    transaction_cost_rate: float = 0.001
    initial_capital: float = 100000.0

# Initialize FastAPI app
app = FastAPI(title="Pairs Trading Terminal API", version="1.0.0")

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()


def _clean_numeric_series(series: pd.Series) -> list:
    """Convert pandas series to JSON-safe values (replace NaN/inf with None)."""
    cleaned = []
    for value in series.tolist():
        if pd.isna(value):
            cleaned.append(None)
        else:
            numeric_value = float(value)
            if not math.isfinite(numeric_value):
                cleaned.append(None)
            else:
                cleaned.append(numeric_value)
    return cleaned

# ============================================================================
# DATA ENDPOINTS
# ============================================================================

@app.post("/api/data/download")
async def download_data(request: DownloadRequest):
    """Download market data for symbols"""
    try:
        end_dt = datetime.strptime(request.end, "%Y-%m-%d") if request.end else datetime.now()
        start_dt = datetime.strptime(request.start, "%Y-%m-%d")
        
        downloader = DataDownloader()
        data = {}
        
        for symbol in request.symbols:
            try:
                instrument = Instrument(symbol=symbol)
                snapshot = downloader.fetch(
                    instrument=instrument,
                    start=start_dt,
                    end=end_dt
                )
                df = snapshot.data
                
                # Handle MultiIndex columns (e.g., ('close', 'AAPL'))
                if isinstance(df.columns, pd.MultiIndex):
                    close_col = ('close', symbol)
                    volume_col = ('volume', symbol)
                    close_data = df[close_col] if close_col in df.columns else None
                    volume_data = df[volume_col] if volume_col in df.columns else None
                else:
                    close_col = 'Close' if 'Close' in df.columns else 'close'
                    close_data = df[close_col]
                    volume_col = 'Volume' if 'Volume' in df.columns else 'volume'
                    volume_data = df[volume_col] if volume_col in df.columns else None
                
                dates = [d.strftime("%Y-%m-%d") if hasattr(d, 'strftime') else str(d) for d in df.index]
                
                data[symbol] = {
                    "dates": dates,
                    "closes": close_data.tolist() if close_data is not None else [],
                    "volumes": volume_data.tolist() if volume_data is not None else [],
                    "rows": len(df)
                }
            except Exception as e:
                data[symbol] = {"error": str(e)}
        
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/data/latest/{symbol}")
async def get_latest_price(symbol: str):
    """Get latest price snapshot"""
    try:
        downloader = DataDownloader()
        end = datetime.now()
        start = end - timedelta(days=5)
        
        instrument = Instrument(symbol=symbol)
        snapshot = downloader.fetch(
            instrument=instrument,
            start=start,
            end=end
        )
        df = snapshot.data
        
        # Handle MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            close_col = ('close', symbol)
            volume_col = ('volume', symbol)
            close_val = float(df[close_col].iloc[-1]) if close_col in df.columns else 0
            close_first = float(df[close_col].iloc[0]) if close_col in df.columns else 0
            volume_val = float(df[volume_col].iloc[-1]) if volume_col in df.columns else 0
        else:
            close_col = 'Close' if 'Close' in df.columns else 'close'
            volume_col = 'Volume' if 'Volume' in df.columns else 'volume'
            close_val = float(df[close_col].iloc[-1])
            close_first = float(df[close_col].iloc[0])
            volume_val = float(df[volume_col].iloc[-1]) if volume_col in df.columns else 0
        
        change = float((close_val - close_first) / close_first * 100)
        
        return {
            "symbol": symbol,
            "date": str(df.index[-1].date()),
            "close": close_val,
            "volume": volume_val,
            "change": change
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# PAIR IDENTIFICATION ENDPOINTS
# ============================================================================

@app.post("/api/pairs/identify")
async def identify_pairs(request: PairIdentifyRequest):
    """Identify cointegrated pairs using correlation + Engle-Granger"""
    try:
        end_dt = datetime.strptime(request.end, "%Y-%m-%d") if request.end else datetime.now()
        start_dt = datetime.strptime(request.start, "%Y-%m-%d")
        
        # Create Instrument objects from symbols
        instruments = [Instrument(symbol=symbol) for symbol in request.symbols]
        
        # Run pair identification  
        engine = PairIdentificationEngine()
        report = engine.identify_pairs(
            instruments=instruments,
            start=start_dt,
            end=end_dt,
            min_correlation=request.min_correlation,
            granger_max_lag=request.correlation_lag
        )
        
        # Format results
        pairs = []
        for pair in report.analyzed_pairs[:request.max_results]:
            pairs.append({
                "symbol_x": pair.symbol_x,
                "symbol_y": pair.symbol_y,
                "correlation": float(pair.correlation),
                "half_life": float(pair.half_life) if pair.half_life == pair.half_life else None,
                "coint_pvalue": float(pair.engle_granger_pvalue),
                "adf_pvalue": float(pair.adf_pvalue),
                "granger_pvalue": float(pair.strongest_granger_pvalue),
                "observations": int(pair.observations),
            })
        
        return {
            "status": "success",
            "total_analyzed": len(report.analyzed_pairs),
            "pairs": pairs,
            "count": len(pairs)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# SIGNAL GENERATION ENDPOINTS
# ============================================================================

@app.post("/api/signals/generate")
async def generate_signals(request: SignalGenerateRequest):
    """Generate z-score signals for a pair"""
    try:
        end_dt = datetime.strptime(request.end, "%Y-%m-%d") if request.end else datetime.now()
        start_dt = datetime.strptime(request.start, "%Y-%m-%d")
        
        # Create Instrument objects for the pair
        instrument_x = Instrument(symbol=request.symbol_x)
        instrument_y = Instrument(symbol=request.symbol_y)
        
        # Download data (combine into a single price frame)
        downloader = DataDownloader()
        snapshot_x = downloader.fetch(instrument=instrument_x, start=start_dt, end=end_dt)
        snapshot_y = downloader.fetch(instrument=instrument_y, start=start_dt, end=end_dt)
        
        # Create price frame with both symbols
        df_x = snapshot_x.data
        df_y = snapshot_y.data
        
        # Extract close prices  
        if isinstance(df_x.columns, pd.MultiIndex):
            x_col = ('close', request.symbol_x)
            x_prices = df_x[x_col] if x_col in df_x.columns else df_x.iloc[:, 0]
        else:
            x_col = 'Close' if 'Close' in df_x.columns else 'close'
            x_prices = df_x[x_col]
        
        if isinstance(df_y.columns, pd.MultiIndex):
            y_col = ('close', request.symbol_y)
            y_prices = df_y[y_col] if y_col in df_y.columns else df_y.iloc[:, 0]
        else:
            y_col = 'Close' if 'Close' in df_y.columns else 'close'
            y_prices = df_y[y_col]
        
        # Align indices and create price frame
        x_prices.name = request.symbol_x
        y_prices.name = request.symbol_y
        price_frame = pd.concat([x_prices, y_prices], axis=1)
        price_frame = price_frame.dropna()
        
        # Generate signals using the correct API
        engine = PairSignalEngine()
        signal_params = SignalParameters(
            entry_threshold=request.entry_threshold,
            exit_threshold=request.exit_threshold,
            target_gross_exposure=request.target_gross_exposure
        )
        signal_result = engine.generate_for_pair(
            price_frame=price_frame,
            symbol_x=request.symbol_x,
            symbol_y=request.symbol_y,
            parameters=signal_params
        )
        
        # Format result
        df = signal_result.to_frame()
        return {
            "status": "success",
            "pair": f"{request.symbol_x}/{request.symbol_y}",
            "signals": {
                "dates": [d.strftime("%Y-%m-%d") if hasattr(d, 'strftime') else str(d) for d in df.index],
                "spread": _clean_numeric_series(df['spread']),
                "zscore": _clean_numeric_series(df['zscore']),
                "position": _clean_numeric_series(df['position']),
                "weight_x": _clean_numeric_series(df['weight_x']),
                "weight_y": _clean_numeric_series(df['weight_y']),
                "gross_exposure": _clean_numeric_series(df['gross_exposure']),
            },
            "rows": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# BACKTEST ENDPOINTS
# ============================================================================

@app.post("/api/backtest/run")
async def run_backtest(request: BacktestRequest):
    """Run full backtest pipeline"""
    try:
        end_dt = datetime.strptime(request.end, "%Y-%m-%d") if request.end else datetime.now()
        start_dt = datetime.strptime(request.start, "%Y-%m-%d")
        
        # Download data for both symbols
        downloader = DataDownloader()
        instrument_x = Instrument(symbol=request.symbol_x)
        instrument_y = Instrument(symbol=request.symbol_y)
        
        snapshot_x = downloader.fetch(instrument=instrument_x, start=start_dt, end=end_dt)
        snapshot_y = downloader.fetch(instrument=instrument_y, start=start_dt, end=end_dt)
        
        df_x = snapshot_x.data
        df_y = snapshot_y.data
        
        # Extract close prices
        if isinstance(df_x.columns, pd.MultiIndex):
            x_col = ('close', request.symbol_x)
            x_prices = df_x[x_col] if x_col in df_x.columns else df_x.iloc[:, 0]
        else:
            x_col = 'Close' if 'Close' in df_x.columns else 'close'
            x_prices = df_x[x_col]
        
        if isinstance(df_y.columns, pd.MultiIndex):
            y_col = ('close', request.symbol_y)
            y_prices = df_y[y_col] if y_col in df_y.columns else df_y.iloc[:, 0]
        else:
            y_col = 'Close' if 'Close' in df_y.columns else 'close'
            y_prices = df_y[y_col]
        
        # Align indices and create price frame
        x_prices.name = request.symbol_x
        y_prices.name = request.symbol_y
        price_frame = pd.concat([x_prices, y_prices], axis=1)
        price_frame = price_frame.dropna()
        
        # Generate signals
        signal_engine = PairSignalEngine()
        signal_params = SignalParameters(
            entry_threshold=request.entry_threshold,
            exit_threshold=request.exit_threshold,
            target_gross_exposure=request.target_gross_exposure
        )
        signal_result = signal_engine.generate_for_pair(
            price_frame=price_frame,
            symbol_x=request.symbol_x,
            symbol_y=request.symbol_y,
            parameters=signal_params
        )
        
        # Run backtest with risk controls
        risk_params = RiskParameters(
            stop_loss_fraction=request.stop_loss_fraction,
            max_holding_period=request.max_holding_period
        )
        backtest_params = BacktestParameters(
            transaction_cost_rate=request.transaction_cost_rate,
            initial_capital=request.initial_capital
        )
        backtest_engine = PairBacktestEngine()
        backtest_result = backtest_engine.run(
            signal_result=signal_result,
            risk_parameters=risk_params,
            backtest_parameters=backtest_params
        )
        
        # Format result
        df = backtest_result.to_frame()
        summary = backtest_result.summary()
        
        return {
            "status": "success",
            "pair": f"{request.symbol_x}/{request.symbol_y}",
            "summary": {
                "total_return": float(summary['cumulative_net_pnl'] / request.initial_capital * 100),
                "gross_pnl": float(summary['cumulative_gross_pnl']),
                "net_pnl": float(summary['cumulative_net_pnl']),
                "total_costs": float(summary['total_costs']),
                "max_drawdown": float(summary['max_drawdown']),
                "ending_equity": float(summary['ending_equity']),
                "sharpe_ratio": float(backtest_result.sharpe_ratio) if hasattr(backtest_result, 'sharpe_ratio') else 0.0
            },
            "backtest": {
                "dates": [d.strftime("%Y-%m-%d") if hasattr(d, 'strftime') else str(d) for d in df.index],
                "gross_pnl": df['gross_pnl'].tolist() if 'gross_pnl' in df.columns else [],
                "net_pnl": df['net_pnl'].tolist() if 'net_pnl' in df.columns else [],
                "equity_curve": df['equity_curve'].tolist() if 'equity_curve' in df.columns else [],
                "position": df['risk_position'].tolist() if 'risk_position' in df.columns else (df['position'].tolist() if 'position' in df.columns else []),
                "transaction_cost": df['transaction_cost'].tolist() if 'transaction_cost' in df.columns else [],
            },
            "rows": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# WEBSOCKET ENDPOINTS - Live Streaming
# ============================================================================

@app.websocket("/ws/live-stream/{symbol}")
async def websocket_live_stream(websocket: WebSocket, symbol: str):
    """WebSocket for live price updates"""
    await manager.connect(websocket)
    try:
        downloader = DataDownloader()
        
        while True:
            try:
                # Fetch latest data every 5 seconds
                await asyncio.sleep(5)
                
                end = datetime.now()
                start = end - timedelta(days=30)
                
                instrument = Instrument(symbol=symbol)
                snapshot = downloader.fetch(
                    instrument=instrument,
                    start=start,
                    end=end
                )
                df = snapshot.data
                
                if df is not None and len(df) > 0:
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else latest
                    
                    # Handle MultiIndex columns
                    if isinstance(df.columns, pd.MultiIndex):
                        close_col = ('close', symbol)
                        volume_col = ('volume', symbol)
                        close_price = float(df[close_col].iloc[-1]) if close_col in df.columns else 0
                        close_prev = float(df[close_col].iloc[-2]) if close_col in df.columns and len(df) > 1 else close_price
                        volume_val = float(df[volume_col].iloc[-1]) if volume_col in df.columns else 0
                    else:
                        close_col = 'Close' if 'Close' in df.columns else 'close'
                        volume_col = 'Volume' if 'Volume' in df.columns else 'volume'
                        close_price = float(df[close_col].iloc[-1])
                        close_prev = float(df[close_col].iloc[-2]) if len(df) > 1 else close_price
                        volume_val = float(df[volume_col].iloc[-1]) if volume_col in df.columns else 0
                    
                    change = float((close_price - close_prev) / close_prev * 100) if close_prev != 0 else 0
                    
                    await websocket.send_json({
                        "type": "price_update",
                        "symbol": symbol,
                        "date": str(df.index[-1]),
                        "price": close_price,
                        "volume": volume_val,
                        "change": change,
                        "timestamp": datetime.now().isoformat()
                    })
            except Exception as e:
                await websocket.send_json({"error": str(e)})
                break
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.websocket("/ws/pair-stream/{symbol_x}/{symbol_y}")
async def websocket_pair_stream(websocket: WebSocket, symbol_x: str, symbol_y: str):
    """WebSocket for live pair z-score updates"""
    await manager.connect(websocket)
    try:
        downloader = DataDownloader()
        signal_engine = PairSignalEngine()
        
        prev_spread = None
        prev_position = 0.0
        cumulative_live_pnl = 0.0

        while True:
            try:
                await asyncio.sleep(10)  # Update every 10 seconds
                
                # Fetch latest data
                end = datetime.now()
                start = end - timedelta(days=60)
                
                instrument_x = Instrument(symbol=symbol_x)
                instrument_y = Instrument(symbol=symbol_y)
                
                snapshot_x = downloader.fetch(instrument=instrument_x, start=start, end=end)
                snapshot_y = downloader.fetch(instrument=instrument_y, start=start, end=end)
                
                df_x = snapshot_x.data
                df_y = snapshot_y.data
                
                # Extract close prices
                if isinstance(df_x.columns, pd.MultiIndex):
                    x_col = ('close', symbol_x)
                    x_prices = df_x[x_col] if x_col in df_x.columns else df_x.iloc[:, 0]
                else:
                    x_col = 'Close' if 'Close' in df_x.columns else 'close'
                    x_prices = df_x[x_col]
                
                if isinstance(df_y.columns, pd.MultiIndex):
                    y_col = ('close', symbol_y)
                    y_prices = df_y[y_col] if y_col in df_y.columns else df_y.iloc[:, 0]
                else:
                    y_col = 'Close' if 'Close' in df_y.columns else 'close'
                    y_prices = df_y[y_col]
                
                # Create price frame
                x_prices.name = symbol_x
                y_prices.name = symbol_y
                price_frame = pd.concat([x_prices, y_prices], axis=1)
                price_frame = price_frame.dropna()
                
                # Generate signals
                signal_result = signal_engine.generate_for_pair(
                    price_frame=price_frame,
                    symbol_x=symbol_x,
                    symbol_y=symbol_y
                )
                
                signal_df = signal_result.to_frame()
                df = signal_df.iloc[-5:]  # Last 5 rows

                latest_spread = float(df['spread'].iloc[-1])
                latest_position = float(df['position'].iloc[-1])

                incremental_pnl = 0.0
                if prev_spread is not None:
                    incremental_pnl = prev_position * (latest_spread - prev_spread)
                    cumulative_live_pnl += incremental_pnl

                prev_spread = latest_spread
                prev_position = latest_position
                
                await websocket.send_json({
                    "type": "pair_update",
                    "pair": f"{symbol_x}/{symbol_y}",
                    "data": {
                        "dates": [d.strftime("%Y-%m-%d") if hasattr(d, 'strftime') else str(d) for d in df.index],
                        "zscore": df['zscore'].tolist(),
                        "spread": df['spread'].tolist(),
                        "position": df['position'].tolist(),
                        "incremental_pnl": incremental_pnl,
                        "cumulative_live_pnl": cumulative_live_pnl,
                    },
                    "timestamp": datetime.now().isoformat()
                })
            except WebSocketDisconnect:
                raise
            except Exception as e:
                try:
                    await websocket.send_json({"error": str(e)})
                except RuntimeError:
                    break
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ============================================================================
# HEALTH & INFO ENDPOINTS
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/config/defaults")
async def get_default_config():
    """Get default configuration values"""
    return {
        "signals": {
            "entry_threshold": 2.0,
            "exit_threshold": 0.5,
            "target_gross_exposure": 1.0,
        },
        "risk": {
            "stop_loss_fraction": 0.03,
            "max_holding_period": 20,
            "var_window": 20,
            "var_confidence": 0.05,
        },
        "backtest": {
            "transaction_cost_rate": 0.001,
            "initial_capital": 100000.0,
        },
        "pair_identification": {
            "min_correlation": 0.8,
            "correlation_lag": 1,
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
