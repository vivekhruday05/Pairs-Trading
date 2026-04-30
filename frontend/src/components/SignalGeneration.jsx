import React, { useState } from 'react';
import { LineChart, Line, ComposedChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Zap, AlertCircle } from 'lucide-react';

export default function SignalGeneration({ symbols, setSymbols }) {
  const [params, setParams] = useState({
    startMonths: 12,
    start: '2023-01-01',
    end: new Date().toISOString().split('T')[0],
    entry_threshold: 2.0,
    exit_threshold: 0.5,
    target_gross_exposure: 1.0,
  });
  const [signals, setSignals] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const generateSignals = async () => {
    setLoading(true);
    setError('');
    setSignals(null);

    try {
      const res = await fetch('http://localhost:8000/api/signals/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol_x: symbols.x,
          symbol_y: symbols.y,
          ...params,
        }),
      });
      const result = await res.json();
      if (!res.ok) throw new Error(result.detail || 'Failed to generate signals');

      if (result.status === 'success') {
        // Prepare data for charting
        const chartData = result.signals.dates.map((date, idx) => ({
          date: new Date(date).toLocaleDateString(),
          spread: result.signals.spread[idx],
          zscore: result.signals.zscore[idx],
          position: result.signals.position[idx],
          exposure: result.signals.gross_exposure[idx],
        }));
        setSignals({ ...result, chartData });
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
        <h3 className="text-sm font-bold text-emerald-400 mb-4">SIGNAL PARAMETERS</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
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
          <div>
            <label className="text-xs text-gray-500 uppercase mb-2 block">DATE RANGE</label>
            <select
              value={params.startMonths}
              onChange={(e) => {
                const months = parseInt(e.target.value);
                const start = new Date();
                start.setMonth(start.getMonth() - months);
                setParams({
                  ...params,
                  startMonths: months,
                  start: start.toISOString().split('T')[0],
                });
              }}
              className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            >
              <option value="1">1 Month</option>
              <option value="3">3 Months</option>
              <option value="6">6 Months</option>
              <option value="12">1 Year</option>
              <option value="24">2 Years</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-xs text-gray-500 uppercase mb-2 block">ENTRY THRESHOLD (σ)</label>
            <input
              type="number"
              step="0.1"
              value={params.entry_threshold}
              onChange={(e) => setParams({ ...params, entry_threshold: parseFloat(e.target.value) })}
              className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 uppercase mb-2 block">EXIT THRESHOLD (σ)</label>
            <input
              type="number"
              step="0.1"
              value={params.exit_threshold}
              onChange={(e) => setParams({ ...params, exit_threshold: parseFloat(e.target.value) })}
              className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 uppercase mb-2 block">TARGET EXPOSURE</label>
            <input
              type="number"
              step="0.1"
              min="0"
              value={params.target_gross_exposure}
              onChange={(e) => setParams({ ...params, target_gross_exposure: parseFloat(e.target.value) })}
              className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            />
          </div>
        </div>
      </div>

      {/* Action Button */}
      <button
        onClick={generateSignals}
        disabled={loading || !symbols.x || !symbols.y}
        className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed text-white py-3 rounded font-bold flex items-center justify-center gap-2 text-lg"
      >
        <Zap size={20} />
        {loading ? 'GENERATING...' : 'GENERATE SIGNALS'}
      </button>

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

      {/* Results */}
      {signals && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
            <h3 className="text-sm font-bold text-emerald-400 mb-4">Z-SCORE & SPREAD</h3>
            <ResponsiveContainer width="100%" height={400}>
              <ComposedChart data={signals.chartData.slice(-100)}>
                <CartesianGrid stroke="#404854" />
                <XAxis stroke="#9CA3AF" dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis stroke="#9CA3AF" yAxisId="left" />
                <YAxis stroke="#9CA3AF" yAxisId="right" orientation="right" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1E293B',
                    border: '1px solid #475569',
                  }}
                />
                <Legend />
                <Bar yAxisId="left" dataKey="spread" fill="#8B5CF6" opacity={0.3} />
                <Line yAxisId="right" type="monotone" dataKey="zscore" stroke="#10B981" strokeWidth={2} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
            <h3 className="text-sm font-bold text-emerald-400 mb-4">POSITION & EXPOSURE</h3>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={signals.chartData.slice(-100)}>
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
                <Bar dataKey="position" fill="#10B981" />
                <Line type="monotone" dataKey="exposure" stroke="#F59E0B" strokeWidth={2} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-800 border border-slate-600 rounded p-4">
              <div className="text-xs text-gray-500 mb-1">TOTAL SIGNALS</div>
              <div className="text-2xl font-bold text-emerald-400">{signals.rows}</div>
            </div>
            <div className="bg-slate-800 border border-slate-600 rounded p-4">
              <div className="text-xs text-gray-500 mb-1">LAST Z-SCORE</div>
              <div className="text-2xl font-bold text-blue-400">
                {signals.signals.zscore[signals.signals.zscore.length - 1] != null ? signals.signals.zscore[signals.signals.zscore.length - 1].toFixed(2) : '--'}
              </div>
            </div>
            <div className="bg-slate-800 border border-slate-600 rounded p-4">
              <div className="text-xs text-gray-500 mb-1">LAST POSITION</div>
              <div className="text-2xl font-bold text-purple-400">
                {signals.signals.position[signals.signals.position.length - 1] != null ? signals.signals.position[signals.signals.position.length - 1].toFixed(0) : '--'}
              </div>
            </div>
            <div className="bg-slate-800 border border-slate-600 rounded p-4">
              <div className="text-xs text-gray-500 mb-1">CURRENT EXPOSURE</div>
              <div className="text-2xl font-bold text-amber-400">
                {signals.signals.gross_exposure[signals.signals.gross_exposure.length - 1] != null ? signals.signals.gross_exposure[signals.signals.gross_exposure.length - 1].toFixed(2) : '--'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
