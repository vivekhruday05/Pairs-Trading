import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Activity, Play, Square, AlertCircle, Search } from 'lucide-react';
import { LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const DEFAULT_AUTO_SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META'];

export default function LivePairTester({ symbols, setSymbols }) {
  const [mode, setMode] = useState('manual');
  const [autoSymbols, setAutoSymbols] = useState(DEFAULT_AUTO_SYMBOLS);
  const [candidatePairs, setCandidatePairs] = useState([]);
  const [selectedPair, setSelectedPair] = useState(null);

  const [streaming, setStreaming] = useState(false);
  const [streamData, setStreamData] = useState([]);
  const [latest, setLatest] = useState(null);
  const [loadingPairs, setLoadingPairs] = useState(false);
  const [error, setError] = useState('');

  const wsRef = useRef(null);

  const pairLabel = useMemo(() => `${symbols.x}/${symbols.y}`, [symbols.x, symbols.y]);

  const findAutoPairs = async () => {
    setLoadingPairs(true);
    setError('');
    setCandidatePairs([]);

    try {
      const res = await fetch('http://localhost:8000/api/pairs/identify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbols: autoSymbols,
          start: '2024-01-01',
          end: new Date().toISOString().split('T')[0],
          min_correlation: 0.8,
          max_results: 8,
        }),
      });

      const result = await res.json();
      if (!res.ok) throw new Error(result.detail || 'Failed to find pairs');

      setCandidatePairs(result.pairs || []);
    } catch (err) {
      setError(err.message || 'Failed to find pairs');
    } finally {
      setLoadingPairs(false);
    }
  };

  const stopStreaming = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setStreaming(false);
  };

  const startStreaming = () => {
    setError('');
    setStreamData([]);
    setLatest(null);

    const wsUrl = `ws://localhost:8000/ws/pair-stream/${symbols.x}/${symbols.y}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setStreaming(true);
    };

    ws.onmessage = (event) => {
      const payload = JSON.parse(event.data);

      if (payload.error) {
        setError(payload.error);
        stopStreaming();
        return;
      }

      const incoming = {
        timestamp: new Date(payload.timestamp).toLocaleTimeString(),
        zscore: payload.data.zscore[payload.data.zscore.length - 1],
        spread: payload.data.spread[payload.data.spread.length - 1],
        position: payload.data.position[payload.data.position.length - 1],
        incremental_pnl: payload.data.incremental_pnl || 0,
        cumulative_live_pnl: payload.data.cumulative_live_pnl || 0,
      };

      setLatest(incoming);
      setStreamData((prev) => {
        const merged = [...prev, incoming];
        return merged.slice(-60);
      });
    };

    ws.onerror = () => {
      setError('Live stream connection failed');
      stopStreaming();
    };

    ws.onclose = () => {
      setStreaming(false);
    };
  };

  useEffect(() => {
    return () => stopStreaming();
  }, []);

  const applyCandidate = (pair) => {
    setSelectedPair(pair);
    setSymbols({ x: pair.symbol_x, y: pair.symbol_y });
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
        <h3 className="text-sm font-bold text-emerald-400 mb-4">LIVE PAIR TESTER</h3>

        <div className="flex gap-3 mb-4">
          <button
            onClick={() => setMode('manual')}
            className={`px-4 py-2 rounded text-sm font-bold ${mode === 'manual' ? 'bg-emerald-600 text-white' : 'bg-slate-800 text-gray-300'}`}
          >
            MANUAL
          </button>
          <button
            onClick={() => setMode('auto')}
            className={`px-4 py-2 rounded text-sm font-bold ${mode === 'auto' ? 'bg-emerald-600 text-white' : 'bg-slate-800 text-gray-300'}`}
          >
            AUTO
          </button>
        </div>

        {mode === 'manual' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-500 uppercase mb-2 block">SYMBOL X</label>
              <input
                value={symbols.x}
                onChange={(e) => setSymbols({ ...symbols, x: e.target.value.toUpperCase() })}
                className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 uppercase mb-2 block">SYMBOL Y</label>
              <input
                value={symbols.y}
                onChange={(e) => setSymbols({ ...symbols, y: e.target.value.toUpperCase() })}
                className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white"
              />
            </div>
          </div>
        )}

        {mode === 'auto' && (
          <div className="space-y-4">
            <div>
              <label className="text-xs text-gray-500 uppercase mb-2 block">UNIVERSE</label>
              <textarea
                value={autoSymbols.join(', ')}
                onChange={(e) => setAutoSymbols(e.target.value.split(',').map(s => s.trim().toUpperCase()).filter(Boolean))}
                rows={3}
                className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white"
              />
            </div>
            <button
              onClick={findAutoPairs}
              disabled={loadingPairs}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded text-sm font-bold flex items-center gap-2"
            >
              <Search size={16} />
              {loadingPairs ? 'FINDING...' : 'FIND PAIRS'}
            </button>

            {candidatePairs.length > 0 && (
              <div className="space-y-2 max-h-52 overflow-y-auto">
                {candidatePairs.map((pair, idx) => (
                  <button
                    key={`${pair.symbol_x}-${pair.symbol_y}-${idx}`}
                    onClick={() => applyCandidate(pair)}
                    className={`w-full text-left p-3 rounded border ${selectedPair?.symbol_x === pair.symbol_x && selectedPair?.symbol_y === pair.symbol_y ? 'border-emerald-500 bg-slate-800' : 'border-slate-600 bg-slate-800'} hover:border-emerald-500`}
                  >
                    <div className="text-white font-bold">{pair.symbol_x} / {pair.symbol_y}</div>
                    <div className="text-xs text-gray-400">corr {pair.correlation.toFixed(3)} | coint p {pair.coint_pvalue.toFixed(4)}</div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="flex gap-3 mt-6">
          <button
            onClick={startStreaming}
            disabled={streaming || !symbols.x || !symbols.y}
            className="flex-1 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white py-3 rounded font-bold flex items-center justify-center gap-2"
          >
            <Play size={18} />
            START LIVE TEST ({pairLabel})
          </button>
          <button
            onClick={stopStreaming}
            disabled={!streaming}
            className="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white py-3 px-5 rounded font-bold flex items-center gap-2"
          >
            <Square size={18} /> STOP
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-700 rounded-lg p-4 flex gap-3">
          <AlertCircle className="text-red-400 flex-shrink-0" size={20} />
          <div className="text-red-300 text-sm">{error}</div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Metric title="STREAM" value={streaming ? 'LIVE' : 'OFF'} valueClass={streaming ? 'text-green-400' : 'text-gray-400'} />
        <Metric title="LAST Z-SCORE" value={latest ? latest.zscore.toFixed(2) : '--'} valueClass="text-blue-400" />
        <Metric title="POSITION" value={latest ? latest.position.toFixed(0) : '--'} valueClass="text-purple-400" />
        <Metric title="LIVE PNL" value={latest ? latest.cumulative_live_pnl.toFixed(4) : '--'} valueClass={latest && latest.cumulative_live_pnl >= 0 ? 'text-green-400' : 'text-red-400'} />
      </div>

      <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
        <h3 className="text-sm font-bold text-emerald-400 mb-4 flex items-center gap-2">
          <Activity size={16} /> LIVE SIGNAL + PNL TRACK
        </h3>
        <ResponsiveContainer width="100%" height={360}>
          <LineChart data={streamData}>
            <CartesianGrid stroke="#404854" />
            <XAxis stroke="#9CA3AF" dataKey="timestamp" tick={{ fontSize: 12 }} />
            <YAxis stroke="#9CA3AF" yAxisId="left" />
            <YAxis stroke="#9CA3AF" yAxisId="right" orientation="right" />
            <Tooltip contentStyle={{ backgroundColor: '#1E293B', border: '1px solid #475569' }} />
            <Legend />
            <Line yAxisId="left" type="monotone" dataKey="zscore" stroke="#10B981" dot={false} name="Z-Score" />
            <Line yAxisId="left" type="monotone" dataKey="position" stroke="#F59E0B" dot={false} name="Position" />
            <Line yAxisId="right" type="monotone" dataKey="cumulative_live_pnl" stroke="#60A5FA" dot={false} name="Live PnL" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function Metric({ title, value, valueClass }) {
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
      <div className="text-xs text-gray-500 uppercase mb-1">{title}</div>
      <div className={`text-2xl font-bold ${valueClass}`}>{value}</div>
    </div>
  );
}
