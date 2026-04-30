import React, { useState } from 'react';
import { Search, AlertCircle, CheckCircle2 } from 'lucide-react';

const DEFAULT_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX'];

export default function PairIdentification({ setCurrentView, setGlobalSymbols }) {
  const [symbols, setSymbols] = useState(DEFAULT_SYMBOLS);
  const [newSymbol, setNewSymbol] = useState('');
  const [params, setParams] = useState({
    start: '2023-01-01',
    end: new Date().toISOString().split('T')[0],
    min_correlation: 0.8,
    max_results: 10,
  });
  const [pairs, setPairs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const addSymbol = () => {
    if (newSymbol && !symbols.includes(newSymbol.toUpperCase())) {
      setSymbols([...symbols, newSymbol.toUpperCase()]);
      setNewSymbol('');
    }
  };

  const removeSymbol = (sym) => {
    setSymbols(symbols.filter(s => s !== sym));
  };

  const identifyPairs = async () => {
    setLoading(true);
    setError('');
    setPairs([]);

    try {
      const res = await fetch('http://localhost:8000/api/pairs/identify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbols, ...params }),
      });

      if (!res.ok) throw new Error('Failed to identify pairs');
      
      const result = await res.json();
      if (result.status === 'success') {
        setPairs(result.pairs);
      } else {
        setError(result.detail || 'Unknown error');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Configuration */}
      <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
        <h3 className="text-sm font-bold text-emerald-400 mb-4">CONFIGURATION</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label className="text-xs text-gray-500 uppercase mb-2 block">START DATE</label>
            <input
              type="date"
              value={params.start}
              onChange={(e) => setParams({ ...params, start: e.target.value })}
              className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 uppercase mb-2 block">END DATE</label>
            <input
              type="date"
              value={params.end}
              onChange={(e) => setParams({ ...params, end: e.target.value })}
              className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="text-xs text-gray-500 uppercase mb-2 block">MIN CORRELATION</label>
            <input
              type="number"
              step="0.01"
              min="0"
              max="1"
              value={params.min_correlation}
              onChange={(e) => setParams({ ...params, min_correlation: parseFloat(e.target.value) })}
              className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="text-xs text-gray-500 uppercase mb-2 block">MAX RESULTS</label>
            <input
              type="number"
              min="1"
              max="100"
              value={params.max_results}
              onChange={(e) => setParams({ ...params, max_results: parseInt(e.target.value) })}
              className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            />
          </div>
        </div>

        {/* Symbol Selector */}
        <div>
          <label className="text-xs text-gray-500 uppercase mb-2 block">SYMBOLS</label>
          <div className="flex gap-2 mb-4">
            <input
              type="text"
              value={newSymbol}
              onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
              onKeyPress={(e) => e.key === 'Enter' && addSymbol()}
              placeholder="Add symbol"
              className="flex-1 bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500"
            />
            <button
              onClick={addSymbol}
              className="bg-emerald-600 hover:bg-emerald-700 px-4 py-2 rounded text-sm font-bold"
            >
              ADD
            </button>
          </div>

          <div className="flex flex-wrap gap-2">
            {symbols.map(sym => (
              <div
                key={sym}
                className="bg-slate-800 border border-slate-600 rounded px-3 py-1 text-sm flex items-center gap-2"
              >
                {sym}
                <button
                  onClick={() => removeSymbol(sym)}
                  className="text-gray-400 hover:text-red-400 text-xs font-bold"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Action Button */}
      <button
        onClick={identifyPairs}
        disabled={loading || symbols.length < 2}
        className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed text-white py-3 rounded font-bold flex items-center justify-center gap-2 text-lg"
      >
        <Search size={20} />
        {loading ? 'ANALYZING...' : 'FIND COINTEGRATED PAIRS'}
      </button>

      {/* Error Message */}
      {error && (
        <div className="bg-red-900/20 border border-red-700 rounded-lg p-4 flex gap-3">
          <AlertCircle className="text-red-400 flex-shrink-0" size={20} />
          <div>
            <div className="text-red-400 font-bold text-sm">Error</div>
            <div className="text-red-300 text-sm">{error}</div>
          </div>
        </div>
      )}

      {/* Results */}
      {pairs.length > 0 && (
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
          <h3 className="text-sm font-bold text-emerald-400 mb-4">
            TOP PAIRS ({pairs.length})
          </h3>

          <div className="space-y-3 max-h-96 overflow-y-auto">
            {pairs.map((pair, idx) => (
              <div
                key={idx}
                className="bg-slate-800 border border-slate-600 rounded p-4 hover:border-emerald-500 transition cursor-pointer"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="text-lg font-bold text-white">
                    {pair.symbol_x} / {pair.symbol_y}
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1 text-green-400 text-sm">
                      <CheckCircle2 size={16} /> COINTEGRATED
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setGlobalSymbols({ x: pair.symbol_x, y: pair.symbol_y });
                        setCurrentView('live-test');
                      }}
                      className="bg-blue-600 hover:bg-blue-700 text-white text-xs px-3 py-1 rounded font-bold"
                    >
                      TEST IN LIVE
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-2 text-xs">
                  <div>
                    <span className="text-gray-500">Correlation</span>
                    <div className="text-emerald-400 font-bold">
                      {pair.correlation.toFixed(3)}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-500">ADF p-value</span>
                    <div className="text-emerald-400 font-bold">
                      {pair.adf_pvalue.toFixed(4)}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-500">Coint p-value</span>
                    <div className="text-emerald-400 font-bold">
                      {pair.coint_pvalue.toFixed(4)}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-500">Half-Life</span>
                    <div className="text-emerald-400 font-bold">
                      {pair.half_life ? pair.half_life.toFixed(1) + 'd' : 'N/A'}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && pairs.length === 0 && !error && (
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-12 text-center">
          <div className="text-gray-500 text-sm">Click "FIND COINTEGRATED PAIRS" to analyze</div>
        </div>
      )}
    </div>
  );
}
