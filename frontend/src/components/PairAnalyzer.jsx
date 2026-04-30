import React, { useState } from 'react';
import { LineChart, Line, ComposedChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Play, AlertCircle, RefreshCw } from 'lucide-react';

export default function PairAnalyzer() {
  const [mode, setMode] = useState('manual'); // 'manual' or 'auto'
  const [symbols, setSymbols] = useState({ x: 'AAPL', y: 'MSFT' });
  const [durationMonths, setDurationMonths] = useState(12);
  const [selectedPair, setSelectedPair] = useState(null);
  const [autoAnalyzingText, setAutoAnalyzingText] = useState('AAPL, GOOGL, MSFT, AMZN, TSLA');

  const [analysisResult, setAnalysisResult] = useState(null);
  const [suggestedPairs, setSuggestedPairs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const runAutoAnalysis = async () => {
    setLoading(true);
    setError('');
    setSuggestedPairs([]);

    try {
      const res = await fetch('http://localhost:8000/api/pairs/identify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbols: autoAnalyzingText.split(',').map(s => s.trim().toUpperCase()).filter(Boolean),
          start: '2024-01-01',
          end: new Date().toISOString().split('T')[0],
          min_correlation: 0.8,
          max_results: 5,
        }),
      });

      if (!res.ok) throw new Error('Failed to analyze pairs');
      
      const result = await res.json();
      if (result.status === 'success') {
        setSuggestedPairs(result.pairs);
      } else {
        setError(result.detail || 'Unknown error');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const selectPairFromAuto = (pair) => {
    setSymbols({ x: pair.symbol_x, y: pair.symbol_y });
    setSelectedPair(pair);
    runAnalysis(pair.symbol_x, pair.symbol_y);
  };

  const runAnalysis = async (symbolX, symbolY) => {
    setLoading(true);
    setError('');
    setAnalysisResult(null);

    try {
      const startDate = new Date();
      startDate.setMonth(startDate.getMonth() - durationMonths);

      const res = await fetch('http://localhost:8000/api/backtest/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol_x: symbolX,
          symbol_y: symbolY,
          start: startDate.toISOString().split('T')[0],
          end: new Date().toISOString().split('T')[0],
          entry_threshold: 2.0,
          exit_threshold: 0.5,
          target_gross_exposure: 1.0,
          stop_loss_fraction: 0.03,
          max_holding_period: 20,
          transaction_cost_rate: 0.001,
          initial_capital: 100000,
        }),
      });

      if (!res.ok) throw new Error('Failed to run analysis');
      
      const result = await res.json();
      if (result.status === 'success') {
        const chartData = result.backtest.dates.map((date, idx) => ({
          date: new Date(date).toLocaleDateString(),
          zscore: result.backtest.position[idx], // For visualization
          net_pnl: result.backtest.net_pnl[idx],
          equity_curve: result.backtest.equity_curve[idx],
        }));
        setAnalysisResult({ ...result, chartData });
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
      {/* Mode Selector */}
      <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
        <h3 className="text-sm font-bold text-emerald-400 mb-4">ANALYSIS MODE</h3>

        <div className="flex gap-4 mb-6">
          <button
            onClick={() => setMode('manual')}
            className={`flex-1 py-3 rounded font-bold transition ${
              mode === 'manual'
                ? 'bg-emerald-600 text-white'
                : 'bg-slate-800 text-gray-300 hover:bg-slate-700'
            }`}
          >
            MANUAL SELECT
          </button>
          <button
            onClick={() => setMode('auto')}
            className={`flex-1 py-3 rounded font-bold transition ${
              mode === 'auto'
                ? 'bg-emerald-600 text-white'
                : 'bg-slate-800 text-gray-300 hover:bg-slate-700'
            }`}
          >
            AUTO FINDER
          </button>
        </div>

        {/* Duration Selector */}
        <div className="flex gap-4">
          <div className="flex-1">
            <label className="text-xs text-gray-500 uppercase mb-2 block">ANALYSIS DURATION</label>
            <select
              value={durationMonths}
              onChange={(e) => setDurationMonths(parseInt(e.target.value))}
              className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            >
              <option value={1}>1 Month</option>
              <option value={3}>3 Months</option>
              <option value={6}>6 Months</option>
              <option value={12}>1 Year</option>
              <option value={24}>2 Years</option>
              <option value={60}>5 Years</option>
            </select>
          </div>
        </div>
      </div>

      {/* Manual Mode */}
      {mode === 'manual' && (
        <div className="space-y-4">
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
            <h3 className="text-sm font-bold text-emerald-400 mb-4">SELECT PAIR</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="text-xs text-gray-500 uppercase mb-2 block">SYMBOL X</label>
                <input
                  type="text"
                  value={symbols.x}
                  onChange={(e) => setSymbols({ ...symbols, x: e.target.value.toUpperCase() })}
                  className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <label className="text-xs text-gray-500 uppercase mb-2 block">SYMBOL Y</label>
                <input
                  type="text"
                  value={symbols.y}
                  onChange={(e) => setSymbols({ ...symbols, y: e.target.value.toUpperCase() })}
                  className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <button
              onClick={() => runAnalysis(symbols.x, symbols.y)}
              disabled={loading}
              className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white py-3 rounded font-bold flex items-center justify-center gap-2"
            >
              <Play size={20} />
              {loading ? 'ANALYZING...' : 'RUN ANALYSIS'}
            </button>
          </div>
        </div>
      )}

      {/* Auto Mode */}
      {mode === 'auto' && (
        <div className="space-y-4">
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
            <h3 className="text-sm font-bold text-emerald-400 mb-4">AUTO PAIR FINDER</h3>

            <div className="mb-4">
              <label className="text-xs text-gray-500 uppercase mb-2 block">SYMBOLS TO ANALYZE</label>
              <textarea
                value={autoAnalyzingText}
                onChange={(e) => setAutoAnalyzingText(e.target.value)}
                className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                rows="3"
              />
            </div>

            <button
              onClick={runAutoAnalysis}
              disabled={loading}
              className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white py-3 rounded font-bold flex items-center justify-center gap-2"
            >
              <RefreshCw size={20} />
              {loading ? 'FINDING PAIRS...' : 'FIND COINTEGRATED PAIRS'}
            </button>
          </div>

          {/* Suggested Pairs */}
          {suggestedPairs.length > 0 && (
            <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
              <h3 className="text-sm font-bold text-emerald-400 mb-4">
                RECOMMENDED PAIRS ({suggestedPairs.length})
              </h3>

              <div className="space-y-2">
                {suggestedPairs.map((pair, idx) => (
                  <button
                    key={idx}
                    onClick={() => selectPairFromAuto(pair)}
                    className="w-full text-left bg-slate-800 hover:bg-slate-700 border border-slate-600 hover:border-emerald-500 rounded p-4 transition"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-lg font-bold text-white">
                        {pair.symbol_x} / {pair.symbol_y}
                      </div>
                      <div className="text-xs bg-emerald-600 px-2 py-1 rounded">COINTEGRATED</div>
                    </div>
                    <div className="grid grid-cols-4 gap-2 text-xs">
                      <div>
                        <span className="text-gray-500">Corr</span>
                        <div className="text-emerald-400 font-bold">{pair.correlation.toFixed(3)}</div>
                      </div>
                      <div>
                        <span className="text-gray-500">ADF</span>
                        <div className="text-emerald-400 font-bold">{pair.adf_pvalue.toFixed(4)}</div>
                      </div>
                      <div>
                        <span className="text-gray-500">Coint</span>
                        <div className="text-emerald-400 font-bold">{pair.coint_pvalue.toFixed(4)}</div>
                      </div>
                      <div>
                        <span className="text-gray-500">Half-life</span>
                        <div className="text-emerald-400 font-bold">
                          {pair.half_life ? pair.half_life.toFixed(0) + 'd' : 'N/A'}
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-900/20 border border-red-700 rounded-lg p-4 flex gap-3">
          <AlertCircle className="text-red-400 flex-shrink-0" size={20} />
          <div>
            <div className="text-red-400 font-bold text-sm">Error</div>
            <div className="text-red-300 text-sm">{error}</div>
          </div>
        </div>
      )}

      {/* Analysis Results */}
      {analysisResult && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
              <div className="text-xs text-gray-500 uppercase mb-1">NET PROFIT</div>
              <div className={`text-3xl font-bold ${analysisResult.summary.net_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                ${analysisResult.summary.net_pnl.toFixed(2)}
              </div>
              <div className="text-xs text-gray-500 mt-1">{analysisResult.summary.total_return.toFixed(2)}% returned</div>
            </div>

            <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
              <div className="text-xs text-gray-500 uppercase mb-1">MAX DRAWDOWN</div>
              <div className="text-3xl font-bold text-red-400">
                {analysisResult.summary.max_drawdown.toFixed(2)}%
              </div>
              <div className="text-xs text-gray-500 mt-1">Peak-to-trough decline</div>
            </div>

            <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
              <div className="text-xs text-gray-500 uppercase mb-1">FINAL EQUITY</div>
              <div className="text-3xl font-bold text-blue-400">
                ${analysisResult.summary.ending_equity.toFixed(0)}
              </div>
              <div className="text-xs text-gray-500 mt-1">From $100,000 initial</div>
            </div>
          </div>

          {/* Equity Curve */}
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
            <h3 className="text-sm font-bold text-emerald-400 mb-4">PORTFOLIO PERFORMANCE</h3>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={analysisResult.chartData}>
                <CartesianGrid stroke="#404854" />
                <XAxis stroke="#9CA3AF" dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis stroke="#9CA3AF" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1E293B',
                    border: '1px solid #475569',
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="equity_curve"
                  stroke="#10B981"
                  strokeWidth={2}
                  dot={false}
                  name="Portfolio Value"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* P&L Over Time */}
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
            <h3 className="text-sm font-bold text-emerald-400 mb-4">P&L PROGRESSION</h3>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={analysisResult.chartData.slice(-60)}>
                <CartesianGrid stroke="#404854" />
                <XAxis stroke="#9CA3AF" dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis stroke="#9CA3AF" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1E293B',
                    border: '1px solid #475569',
                  }}
                />
                <Bar dataKey="net_pnl" fill="#10B981" opacity={0.6} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
