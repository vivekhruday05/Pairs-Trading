import React, { useState } from 'react';
import { LineChart, Line, ComposedChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { TrendingUp, AlertCircle, Download } from 'lucide-react';

export default function Backtester({ symbols, setSymbols }) {
  const [params, setParams] = useState({
    start: '2023-01-01',
    end: new Date().toISOString().split('T')[0],
    entry_threshold: 2.0,
    exit_threshold: 0.5,
    target_gross_exposure: 1.0,
    stop_loss_fraction: 0.03,
    max_holding_period: 20,
    transaction_cost_rate: 0.001,
    initial_capital: 100000,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const runBacktest = async () => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const res = await fetch('http://localhost:8000/api/backtest/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol_x: symbols.x,
          symbol_y: symbols.y,
          ...params,
        }),
      });

      if (!res.ok) throw new Error('Failed to run backtest');
      
      const data = await res.json();
      if (data.status === 'success') {
        // Prepare chart data
        const chartData = data.backtest.dates.map((date, idx) => ({
          date: new Date(date).toLocaleDateString(),
          gross_pnl: data.backtest.gross_pnl[idx],
          net_pnl: data.backtest.net_pnl[idx],
          equity_curve: data.backtest.equity_curve[idx],
          position: data.backtest.position[idx],
          cost: data.backtest.transaction_cost[idx],
        }));
        setResult({ ...data, chartData });
      } else {
        setError(data.detail || 'Unknown error');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = () => {
    if (!result) return;
    
    const report = `
PAIRS TRADING BACKTEST REPORT
============================
Pair: ${symbols.x} / ${symbols.y}
Period: ${params.start} to ${params.end}

PERFORMANCE METRICS
===================
Total Return: ${result.summary.total_return.toFixed(2)}%
Net P&L: $${result.summary.net_pnl.toFixed(2)}
Gross P&L: $${result.summary.gross_pnl.toFixed(2)}
Transaction Costs: $${result.summary.total_costs.toFixed(2)}
Max Drawdown: ${result.summary.max_drawdown.toFixed(2)}%
Ending Equity: $${result.summary.ending_equity.toFixed(2)}
Sharpe Ratio: ${result.summary.sharpe_ratio.toFixed(3)}

PARAMETERS
==========
Entry Threshold: ${params.entry_threshold}σ
Exit Threshold: ${params.exit_threshold}σ
Stop Loss: ${params.stop_loss_fraction * 100}%
Max Holding Period: ${params.max_holding_period} days
Transaction Cost Rate: ${params.transaction_cost_rate * 100}%
Initial Capital: $${params.initial_capital.toFixed(2)}

Generated: ${new Date().toISOString()}
    `;
    
    const blob = new Blob([report], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `backtest_${symbols.x}_${symbols.y}_${new Date().getTime()}.txt`;
    a.click();
  };

  return (
    <div className="space-y-6">
      {/* Configuration */}
      <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
        <h3 className="text-sm font-bold text-emerald-400 mb-4">BACKTEST CONFIGURATION</h3>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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
        </div>

        <div className="mt-4 pt-4 border-t border-slate-600 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className="text-xs text-gray-500 uppercase mb-2 block">ENTRY THRESHOLD</label>
            <input
              type="number"
              step="0.1"
              value={params.entry_threshold}
              onChange={(e) => setParams({ ...params, entry_threshold: parseFloat(e.target.value) })}
              className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 uppercase mb-2 block">STOP LOSS %</label>
            <input
              type="number"
              step="0.01"
              min="0"
              max="1"
              value={params.stop_loss_fraction}
              onChange={(e) => setParams({ ...params, stop_loss_fraction: parseFloat(e.target.value) })}
              className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 uppercase mb-2 block">MAX HOLD (DAYS)</label>
            <input
              type="number"
              min="1"
              value={params.max_holding_period}
              onChange={(e) => setParams({ ...params, max_holding_period: parseInt(e.target.value) })}
              className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 uppercase mb-2 block">TRANSACTION COST %</label>
            <input
              type="number"
              step="0.0001"
              min="0"
              value={params.transaction_cost_rate}
              onChange={(e) => setParams({ ...params, transaction_cost_rate: parseFloat(e.target.value) })}
              className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            />
          </div>
        </div>

        <div className="mt-4">
          <label className="text-xs text-gray-500 uppercase mb-2 block">INITIAL CAPITAL</label>
          <div className="relative">
            <span className="absolute left-3 top-2 text-gray-500 text-sm">$</span>
            <input
              type="number"
              value={params.initial_capital}
              onChange={(e) => setParams({ ...params, initial_capital: parseFloat(e.target.value) })}
              className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm text-white pl-7 focus:outline-none focus:border-emerald-500"
            />
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={runBacktest}
          disabled={loading || !symbols.x || !symbols.y}
          className="flex-1 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed text-white py-3 rounded font-bold flex items-center justify-center gap-2 text-lg"
        >
          <TrendingUp size={20} />
          {loading ? 'RUNNING...' : 'RUN BACKTEST'}
        </button>
        {result && (
          <button
            onClick={downloadReport}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded font-bold flex items-center gap-2"
          >
            <Download size={20} />
            REPORT
          </button>
        )}
      </div>

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
      {result && (
        <div className="space-y-6">
          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
              <div className="text-xs text-gray-500 uppercase mb-1">NET P&L</div>
              <div className={`text-2xl font-bold ${result.summary.net_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                ${result.summary.net_pnl.toFixed(2)}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {result.summary.total_return.toFixed(2)}% return
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
              <div className="text-xs text-gray-500 uppercase mb-1">TOTAL COSTS</div>
              <div className="text-2xl font-bold text-orange-400">
                ${result.summary.total_costs.toFixed(2)}
              </div>
              <div className="text-xs text-gray-500 mt-1">Transaction fees</div>
            </div>

            <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
              <div className="text-xs text-gray-500 uppercase mb-1">MAX DRAWDOWN</div>
              <div className="text-2xl font-bold text-red-400">
                {result.summary.max_drawdown.toFixed(2)}%
              </div>
              <div className="text-xs text-gray-500 mt-1">Peak-to-trough</div>
            </div>

            <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
              <div className="text-xs text-gray-500 uppercase mb-1">ENDING EQUITY</div>
              <div className="text-2xl font-bold text-blue-400">
                ${result.summary.ending_equity.toFixed(0)}
              </div>
              <div className="text-xs text-gray-500 mt-1">From ${params.initial_capital.toFixed(0)}</div>
            </div>
          </div>

          {/* Equity Curve */}
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
            <h3 className="text-sm font-bold text-emerald-400 mb-4">EQUITY CURVE</h3>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={result.chartData}>
                <CartesianGrid stroke="#404854" />
                <XAxis stroke="#9CA3AF" dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis stroke="#9CA3AF" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1E293B',
                    border: '1px solid #475569',
                  }}
                />
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

          {/* P&L Breakdown */}
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
            <h3 className="text-sm font-bold text-emerald-400 mb-4">P&L BREAKDOWN</h3>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={result.chartData.slice(-100)}>
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
                <Bar yAxisId="left" dataKey="gross_pnl" fill="#10B981" opacity={0.6} name="Gross P&L" />
                <Bar yAxisId="left" dataKey="cost" fill="#EF4444" opacity={0.6} name="Transaction Cost" />
                <Line yAxisId="right" type="monotone" dataKey="net_pnl" stroke="#F59E0B" strokeWidth={2} name="Net P&L" />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Position Chart */}
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
            <h3 className="text-sm font-bold text-emerald-400 mb-4">POSITIONS OVER TIME</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={result.chartData.slice(-100)}>
                <CartesianGrid stroke="#404854" />
                <XAxis stroke="#9CA3AF" dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis stroke="#9CA3AF" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1E293B',
                    border: '1px solid #475569',
                  }}
                />
                <Bar dataKey="position" fill="#8B5CF6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}

function BarChart(props) {
  return <ComposedChart {...props} />;
}
