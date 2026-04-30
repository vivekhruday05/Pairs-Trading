import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Plus, Trash2, RefreshCw } from 'lucide-react';

const DEFAULT_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'];

export default function DataStreaming() {
  const [symbols, setSymbols] = useState(DEFAULT_SYMBOLS);
  const [newSymbol, setNewSymbol] = useState('');
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(false);

  const addSymbol = () => {
    if (newSymbol && !symbols.includes(newSymbol.toUpperCase())) {
      setSymbols([...symbols, newSymbol.toUpperCase()]);
      setNewSymbol('');
    }
  };

  const removeSymbol = (sym) => {
    setSymbols(symbols.filter(s => s !== sym));
    const newData = { ...data };
    delete newData[sym];
    setData(newData);
  };

  const fetchLatestData = async () => {
    setLoading(true);
    const newData = {};
    
    for (const symbol of symbols) {
      try {
        const res = await fetch(`http://localhost:8000/api/data/latest/${symbol}`);
        const result = await res.json();
        newData[symbol] = result;
      } catch (err) {
        console.error(`Error fetching ${symbol}:`, err);
      }
    }
    
    setData(newData);
    setLoading(false);
  };

  useEffect(() => {
    fetchLatestData();
    const interval = setInterval(fetchLatestData, 10000); // Update every 10s
    return () => clearInterval(interval);
  }, [symbols]);

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
        <h3 className="text-sm font-bold text-emerald-400 mb-4">ADD SYMBOLS</h3>
        <div className="flex gap-2">
          <input
            type="text"
            value={newSymbol}
            onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
            onKeyPress={(e) => e.key === 'Enter' && addSymbol()}
            placeholder="Enter symbol (e.g., AAPL)"
            className="flex-1 bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500"
          />
          <button
            onClick={addSymbol}
            className="bg-emerald-600 hover:bg-emerald-700 px-4 py-2 rounded text-sm font-bold flex items-center gap-2"
          >
            <Plus size={16} /> ADD
          </button>
          <button
            onClick={fetchLatestData}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded text-sm font-bold flex items-center gap-2 disabled:opacity-50"
          >
            <RefreshCw size={16} /> REFRESH
          </button>
        </div>
      </div>

      {/* Price Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {symbols.map(symbol => {
          const info = data[symbol];
          const change = info?.change || 0;
          const isPositive = change >= 0;

          return (
            <div
              key={symbol}
              className="bg-slate-900 border border-slate-700 rounded-lg p-4 relative"
            >
              <button
                onClick={() => removeSymbol(symbol)}
                className="absolute top-2 right-2 text-gray-500 hover:text-red-400 transition"
              >
                <Trash2 size={16} />
              </button>

              <div className="text-xs text-gray-500 uppercase mb-1">SYMBOL</div>
              <h3 className="text-lg font-bold text-white mb-3">{symbol}</h3>

              {info && !info.error ? (
                <>
                  <div className="mb-2">
                    <div className="text-2xl font-bold text-emerald-400">
                      ${info.close?.toFixed(2) || 'N/A'}
                    </div>
                    <div className={`text-sm ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                      {isPositive ? '↑' : '↓'} {Math.abs(change).toFixed(2)}%
                    </div>
                  </div>
                  <div className="text-xs text-gray-500">
                    Vol: {(info.volume / 1e6)?.toFixed(2)}M • Date: {info.date}
                  </div>
                </>
              ) : (
                <div className="text-red-400 text-sm">
                  {info?.error || 'Loading...'}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Time Series Chart */}
      {Object.keys(data).length > 0 && (
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
          <h3 className="text-sm font-bold text-emerald-400 mb-4">PRICE ACTION</h3>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={Object.values(data).slice(0, 1)}>
              <CartesianGrid stroke="#404854" />
              <XAxis stroke="#9CA3AF" dataKey="date" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1E293B',
                  border: '1px solid #475569',
                  borderRadius: '4px',
                }}
              />
              <Line type="monotone" dataKey="close" stroke="#10B981" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
