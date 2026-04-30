import React, { useState, useEffect } from 'react';
import Navigation from './components/Navigation';
import DataStreaming from './components/DataStreaming';
import PairIdentification from './components/PairIdentification';
import SignalGeneration from './components/SignalGeneration';
import Backtester from './components/Backtester';
import PairAnalyzer from './components/PairAnalyzer';
import LivePairTester from './components/LivePairTester';

export default function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [apiHealth, setApiHealth] = useState(null);
  const [globalPair, setGlobalPair] = useState({ x: 'AAPL', y: 'GOOGL' });

  useEffect(() => {
    // Check API health
    fetch('http://localhost:8000/api/health')
      .then(res => res.json())
      .then(data => setApiHealth(data))
      .catch(err => console.error('API unavailable:', err));
  }, []);

  const renderView = () => {
    switch (currentView) {
      case 'streaming':
        return <DataStreaming />;
      case 'pair-finder':
        return <PairIdentification setCurrentView={setCurrentView} setGlobalSymbols={setGlobalPair} />;
      case 'signals':
        return <SignalGeneration symbols={globalPair} setSymbols={setGlobalPair} />;
      case 'backtest':
        return <Backtester symbols={globalPair} setSymbols={setGlobalPair} />;
      case 'live-test':
        return <LivePairTester symbols={globalPair} setSymbols={setGlobalPair} />;
      case 'analyzer':
        return <PairAnalyzer />;
      default:
        return <Dashboard setCurrentView={setCurrentView} />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-gray-100 font-mono">
      {/* Header */}
      <div className="bg-slate-900 border-b border-slate-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <h1 className="text-2xl font-bold text-emerald-400">⚡ PAIRS TRADING TERMINAL</h1>
          </div>
          <div className="text-xs text-gray-400">
            {apiHealth ? (
              <span className="text-green-400">● API ONLINE</span>
            ) : (
              <span className="text-red-400">● API OFFLINE</span>
            )}
          </div>
        </div>
      </div>

      <Navigation currentView={currentView} setCurrentView={setCurrentView} />

      <main className="p-6">
        {renderView()}
      </main>
    </div>
  );
}

function Dashboard({ setCurrentView }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {/* Quick Stats */}
      <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
        <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">LIVE FEATURES</div>
        <div className="text-2xl font-bold text-emerald-400 mb-2">6</div>
        <ul className="text-sm text-gray-400 space-y-1">
          <li>✓ Live Data Streaming</li>
          <li>✓ Pair Identification</li>
          <li>✓ Signal Generation</li>
          <li>✓ Backtesting Engine</li>
          <li>✓ Live Pair Testing</li>
          <li>✓ Risk Management</li>
        </ul>
      </div>

      <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
        <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">QUICK ACTIONS</div>
        <div className="space-y-2 mt-4">
          <button
            onClick={() => setCurrentView('pair-finder')}
            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-2 rounded text-sm font-bold"
          >
            FIND PAIRS
          </button>
          <button
            onClick={() => setCurrentView('streaming')}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded text-sm font-bold"
          >
            STREAM LIVE
          </button>
          <button
            onClick={() => setCurrentView('live-test')}
            className="w-full bg-amber-600 hover:bg-amber-700 text-white py-2 rounded text-sm font-bold"
          >
            LIVE PAIR TEST
          </button>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
        <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">STATUS</div>
        <div className="mt-4 space-y-2">
          <div className="flex justify-between text-sm">
            <span>API</span>
            <span className="text-green-400">READY</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Cache</span>
            <span className="text-green-400">ACTIVE</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>WebSocket</span>
            <span className="text-yellow-400">STANDBY</span>
          </div>
        </div>
      </div>
    </div>
  );
}
