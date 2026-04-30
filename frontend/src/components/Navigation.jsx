import React from 'react';
import { TrendingUp, Activity, BarChart3, Zap, Search, Cpu } from 'lucide-react';

export default function Navigation({ currentView, setCurrentView }) {
  const navItems = [
    { id: 'dashboard', label: 'DASHBOARD', icon: Cpu },
    { id: 'streaming', label: 'LIVE STREAM', icon: Activity },
    { id: 'pair-finder', label: 'PAIR FINDER', icon: Search },
    { id: 'signals', label: 'SIGNALS', icon: Zap },
    { id: 'live-test', label: 'LIVE TEST', icon: Activity },
    { id: 'analyzer', label: 'ANALYZER', icon: TrendingUp },
    { id: 'backtest', label: 'BACKTEST', icon: BarChart3 },
  ];

  return (
    <nav className="bg-slate-900 border-b border-slate-700 px-6 py-3">
      <div className="flex gap-1 overflow-x-auto">
        {navItems.map(item => {
          const Icon = item.icon;
          const isActive = currentView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setCurrentView(item.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded transition-colors whitespace-nowrap text-sm font-bold ${
                isActive
                  ? 'bg-emerald-600 text-white'
                  : 'bg-slate-800 text-gray-300 hover:bg-slate-700'
              }`}
            >
              <Icon size={16} />
              {item.label}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
