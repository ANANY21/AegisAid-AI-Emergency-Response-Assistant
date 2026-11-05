import React from 'react';
import { Shield, Activity, MapPin, History, BarChart3, PhoneCall, AlertTriangle } from 'lucide-react';

interface NavbarProps {
  currentTab: 'landing' | 'emergency' | 'hospitals' | 'history' | 'admin';
  setCurrentTab: (tab: 'landing' | 'emergency' | 'hospitals' | 'history' | 'admin') => void;
  systemHealthy: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, setCurrentTab, systemHealthy }) => {
  return (
    <header className="sticky top-0 z-50 bg-navy-950/80 backdrop-blur-md border-b border-navy-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo & Clinical Brand */}
          <div 
            onClick={() => setCurrentTab('landing')}
            className="flex items-center gap-3 cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emergency-600 to-navy-800 flex items-center justify-center shadow-lg shadow-emergency-600/20 group-hover:scale-105 transition-transform">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-lg text-white tracking-tight">Aegis<span className="text-medic-teal">Aid</span></span>
                <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-navy-800 text-slate-300 border border-navy-700">Clinical AI</span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">Validated Emergency Decision Support</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1">
            <button
              onClick={() => setCurrentTab('emergency')}
              className={`px-3.5 py-2 rounded-lg text-sm font-semibold transition-all flex items-center gap-2 ${
                currentTab === 'emergency'
                  ? 'bg-emergency-600/20 text-emergency-500 border border-emergency-500/30'
                  : 'text-slate-300 hover:text-white hover:bg-navy-900'
              }`}
            >
              <Activity className="w-4 h-4" />
              Emergency Assistant
            </button>

            <button
              onClick={() => setCurrentTab('hospitals')}
              className={`px-3.5 py-2 rounded-lg text-sm font-semibold transition-all flex items-center gap-2 ${
                currentTab === 'hospitals'
                  ? 'bg-medic-teal/20 text-medic-teal border border-medic-teal/30'
                  : 'text-slate-300 hover:text-white hover:bg-navy-900'
              }`}
            >
              <MapPin className="w-4 h-4" />
              Find Facilities
            </button>

            <button
              onClick={() => setCurrentTab('history')}
              className={`px-3.5 py-2 rounded-lg text-sm font-semibold transition-all flex items-center gap-2 ${
                currentTab === 'history'
                  ? 'bg-navy-800 text-white border border-navy-700'
                  : 'text-slate-300 hover:text-white hover:bg-navy-900'
              }`}
            >
              <History className="w-4 h-4" />
              Session Log
            </button>

            <button
              onClick={() => setCurrentTab('admin')}
              className={`px-3.5 py-2 rounded-lg text-sm font-semibold transition-all flex items-center gap-2 ${
                currentTab === 'admin'
                  ? 'bg-navy-800 text-white border border-navy-700'
                  : 'text-slate-300 hover:text-white hover:bg-navy-900'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              Evaluation Benchmark
            </button>
          </nav>

          {/* System Status & Direct Dispatch Hotline */}
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full bg-navy-900 border border-navy-800 text-xs">
              <span className={`w-2 h-2 rounded-full ${systemHealthy ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
              <span className="text-slate-300 font-medium">{systemHealthy ? 'RAG Validated' : 'Offline Mode'}</span>
            </div>

            <a
              href="tel:911"
              className="px-3.5 py-1.5 rounded-lg bg-emergency-600 hover:bg-emergency-700 text-white text-xs font-bold transition-all shadow-md shadow-emergency-600/30 flex items-center gap-1.5 animate-pulse"
            >
              <PhoneCall className="w-3.5 h-3.5" />
              Call 911 / 112
            </a>
          </div>

        </div>
      </div>
    </header>
  );
};
