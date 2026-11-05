import React, { useState, useEffect } from 'react';
import { HistorySession } from '../types';
import { getHistory, deleteHistorySession, clearAllHistory } from '../services/api';
import { PriorityBadge } from '../components/PriorityBadge';
import { History, Trash2, Shield, Calendar, AlertCircle, RefreshCw } from 'lucide-react';

export const HistoryView: React.FC = () => {
  const [sessions, setSessions] = useState<HistorySession[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchHistory = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const data = await getHistory();
      setSessions(data);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load history');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      await deleteHistorySession(id);
      setSessions((prev) => prev.filter((s) => s.session_id !== id));
    } catch (err) {
      alert('Failed to delete session record.');
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm('Are you sure you want to delete all stored emergency session logs? This action is irreversible.')) {
      return;
    }
    try {
      await clearAllHistory();
      setSessions([]);
    } catch (err) {
      alert('Failed to clear history.');
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <History className="w-6 h-6 text-medic-teal" />
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">Emergency Session History</h1>
          </div>
          <p className="text-xs text-slate-400">
            Audit past emergency triage assessments and clinical guidance records.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchHistory}
            className="p-2 rounded-xl bg-navy-800 hover:bg-navy-700 text-slate-300 border border-navy-700 text-xs font-bold transition-colors"
            title="Refresh history"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>

          {sessions.length > 0 && (
            <button
              onClick={handleClearAll}
              className="px-3.5 py-2 rounded-xl bg-emergency-600/20 hover:bg-emergency-600/30 text-emergency-400 border border-emergency-500/30 text-xs font-bold flex items-center gap-1.5 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear All History</span>
            </button>
          )}
        </div>
      </div>

      {/* Privacy Notice */}
      <div className="p-4 rounded-xl bg-navy-900 border border-navy-800 text-xs text-slate-400 flex items-start gap-3">
        <Shield className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-slate-200 block mb-0.5">Data Minimization & User Rights:</span>
          <span>
            You have full control over your session logs. You can permanently erase individual records or purge all historical sessions at any time.
          </span>
        </div>
      </div>

      {/* List */}
      {isLoading ? (
        <div className="text-center py-16">
          <div className="w-8 h-8 border-2 border-medic-teal/20 border-t-medic-teal rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400 mt-2 font-medium">Loading session history...</p>
        </div>
      ) : errorMsg ? (
        <div className="p-6 rounded-2xl bg-emergency-950/40 border border-emergency-500/30 text-center text-xs text-emergency-400">
          {errorMsg}
        </div>
      ) : sessions.length === 0 ? (
        <div className="p-12 text-center text-xs text-slate-500 bg-navy-900 border border-navy-800 rounded-2xl">
          No past emergency assessments recorded yet.
        </div>
      ) : (
        <div className="space-y-4">
          {sessions.map((s) => (
            <div key={s.session_id} className="bg-navy-900 border border-navy-800 rounded-2xl p-5 shadow-sm hover:border-navy-700 transition-all space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-navy-800 pb-3">
                <div className="flex items-center gap-3">
                  <PriorityBadge priority={s.priority} />
                  <span className="text-xs text-slate-400 font-mono flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5 text-slate-500" />
                    {new Date(s.created_at).toLocaleString()}
                  </span>
                </div>

                <button
                  onClick={() => handleDelete(s.session_id)}
                  className="self-end sm:self-auto p-1.5 text-slate-500 hover:text-emergency-400 transition-colors"
                  title="Delete record"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              <div>
                <span className="text-[10px] font-bold uppercase text-slate-500 tracking-wider block mb-0.5">Reported Emergency:</span>
                <p className="text-xs text-slate-200 line-clamp-2 italic">"{s.raw_description}"</p>
              </div>

              <div>
                <span className="text-[10px] font-bold uppercase text-slate-500 tracking-wider block mb-0.5">Summary & Guidance:</span>
                <p className="text-xs text-slate-300 line-clamp-2">{s.summary}</p>
              </div>

              {s.extracted_symptoms.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {s.extracted_symptoms.map((sym, idx) => (
                    <span key={idx} className="text-[10px] font-medium px-2 py-0.5 rounded bg-navy-950 text-slate-400 border border-navy-800">
                      {sym}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

    </div>
  );
};
