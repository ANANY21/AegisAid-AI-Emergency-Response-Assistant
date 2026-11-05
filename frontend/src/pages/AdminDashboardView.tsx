import React, { useState, useEffect } from 'react';
import { BenchmarkReport } from '../types';
import { getBenchmarkReport } from '../services/api';
import { 
  BarChart3, ShieldCheck, CheckCircle2, AlertTriangle, Database, 
  Cpu, FileCheck, Layers, RefreshCw, Activity 
} from 'lucide-react';

export const AdminDashboardView: React.FC = () => {
  const [report, setReport] = useState<BenchmarkReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchReport = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const data = await getBenchmarkReport();
      setReport(data);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load benchmarks');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, []);

  if (isLoading && !report) {
    return (
      <div className="text-center py-20">
        <div className="w-10 h-10 border-2 border-medic-teal/20 border-t-medic-teal rounded-full animate-spin mx-auto" />
        <p className="text-xs text-slate-400 mt-3 font-semibold">Loading system evaluation metrics...</p>
      </div>
    );
  }

  const cls = report?.classification_metrics;
  const ret = report?.retrieval_metrics;
  const esc = report?.safety_escalation_metrics;
  const kb = report?.knowledge_base_stats;

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-16">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <BarChart3 className="w-6 h-6 text-medic-teal" />
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">Clinical Evaluation & System Benchmarks</h1>
          </div>
          <p className="text-xs text-slate-400">
            Real-time validation metrics for incident classification, RAG retrieval relevance, and controlled safety escalation.
          </p>
        </div>

        <button
          onClick={fetchReport}
          className="px-4 py-2 rounded-xl bg-navy-800 hover:bg-navy-700 text-slate-200 border border-navy-700 text-xs font-bold flex items-center gap-2 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-medic-teal' : ''}`} />
          <span>Refresh Benchmarks</span>
        </button>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-emergency-950/40 border border-emergency-500/40 text-emergency-400 text-xs">
          {errorMsg}
        </div>
      )}

      {/* Top Level KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Critical Recall */}
        <div className="bg-navy-900 border border-emergency-500/30 rounded-2xl p-5 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-bold uppercase text-emergency-400 tracking-wider">Critical Class Recall</span>
            <AlertTriangle className="w-4 h-4 text-emergency-500" />
          </div>
          <div className="text-3xl font-black font-mono text-white mb-1">
            {cls ? (cls.critical_class_recall * 100).toFixed(1) : '--'}%
          </div>
          <span className="text-[11px] text-slate-400">Target ≥ 95% on life-threatening cases</span>
        </div>

        {/* Retrieval MRR */}
        <div className="bg-navy-900 border border-medic-teal/30 rounded-2xl p-5 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-bold uppercase text-medic-teal tracking-wider">Retrieval MRR</span>
            <Database className="w-4 h-4 text-medic-teal" />
          </div>
          <div className="text-3xl font-black font-mono text-white mb-1">
            {ret ? (ret.mrr * 100).toFixed(1) : '--'}%
          </div>
          <span className="text-[11px] text-slate-400">Mean Reciprocal Rank (Top-1 alignment)</span>
        </div>

        {/* Rejection Rate */}
        <div className="bg-navy-900 border border-amber-500/30 rounded-2xl p-5 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-bold uppercase text-amber-400 tracking-wider">Relevance Rejection</span>
            <ShieldCheck className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-black font-mono text-white mb-1">
            {ret ? (ret.relevance_threshold_rejection_rate * 100).toFixed(1) : '--'}%
          </div>
          <span className="text-[11px] text-slate-400">Unsupported queries safely rejected</span>
        </div>

        {/* Grounding Faithfulness */}
        <div className="bg-navy-900 border border-blue-500/30 rounded-2xl p-5 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-bold uppercase text-blue-400 tracking-wider">Faithfulness Score</span>
            <CheckCircle2 className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-3xl font-black font-mono text-white mb-1">
            {esc ? (esc.faithfulness_mean_score * 100).toFixed(1) : '--'}%
          </div>
          <span className="text-[11px] text-slate-400">Grounded response consistency</span>
        </div>

      </div>

      {/* Classification Detailed Breakdown & Confusion Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* ML Incident Classifier Metrics */}
        <div className="bg-navy-900 border border-navy-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-navy-800 pb-3">
            <div className="flex items-center gap-2">
              <Cpu className="w-5 h-5 text-emergency-500" />
              <h3 className="text-sm font-bold text-white">ML Incident Prioritization Model</h3>
            </div>
            <span className="text-[10px] font-mono text-slate-400 px-2 py-0.5 rounded bg-navy-950 border border-navy-800">
              Random Forest Calibrated
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
            <div className="bg-navy-950 p-3 rounded-xl border border-navy-800">
              <span className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Accuracy</span>
              <span className="text-lg font-black font-mono text-white">{cls ? (cls.accuracy * 100).toFixed(1) : '--'}%</span>
            </div>
            <div className="bg-navy-950 p-3 rounded-xl border border-navy-800">
              <span className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Precision</span>
              <span className="text-lg font-black font-mono text-white">{cls ? (cls.precision_macro * 100).toFixed(1) : '--'}%</span>
            </div>
            <div className="bg-navy-950 p-3 rounded-xl border border-navy-800">
              <span className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Recall</span>
              <span className="text-lg font-black font-mono text-white">{cls ? (cls.recall_macro * 100).toFixed(1) : '--'}%</span>
            </div>
            <div className="bg-navy-950 p-3 rounded-xl border border-navy-800">
              <span className="text-[10px] text-slate-400 uppercase font-bold block mb-1">F1-Score</span>
              <span className="text-lg font-black font-mono text-white">{cls ? (cls.f1_macro * 100).toFixed(1) : '--'}%</span>
            </div>
          </div>

          {/* Confusion Matrix Table */}
          {cls?.confusion_matrix && (
            <div>
              <span className="text-xs font-bold text-slate-300 block mb-2">Confusion Matrix (Cross-Validation):</span>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-center border-collapse">
                  <thead>
                    <tr className="border-b border-navy-800 text-[10px] text-slate-400">
                      <th className="py-2 text-left">True \ Pred</th>
                      {cls.classes.map((c) => (
                        <th key={c} className="py-2 px-3">{c}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {cls.confusion_matrix.map((row, rIdx) => (
                      <tr key={rIdx} className="border-b border-navy-950">
                        <td className="py-2 text-left font-bold text-slate-300 text-[11px]">{cls.classes[rIdx]}</td>
                        {row.map((val, cIdx) => (
                          <td 
                            key={cIdx} 
                            className={`py-2 px-3 font-mono font-bold ${
                              rIdx === cIdx ? 'text-emerald-400 bg-emerald-950/20' : val > 0 ? 'text-slate-400' : 'text-slate-700'
                            }`}
                          >
                            {val}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Retrieval Validation & Safety Metrics */}
        <div className="bg-navy-900 border border-navy-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-navy-800 pb-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-medic-teal" />
              <h3 className="text-sm font-bold text-white">Retrieval Validation (Industry Requirement)</h3>
            </div>
            <span className="text-[10px] font-mono text-slate-400 px-2 py-0.5 rounded bg-navy-950 border border-navy-800">
              Cosine + Threshold (0.52)
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-3 rounded-xl bg-navy-950 border border-navy-800">
              <span className="text-slate-300 font-medium">Precision@K (Top-4 Evidence):</span>
              <span className="font-mono font-bold text-white">{ret ? (ret.precision_at_k * 100).toFixed(1) : '--'}%</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl bg-navy-950 border border-navy-800">
              <span className="text-slate-300 font-medium">Recall@K (Relevant Protocols):</span>
              <span className="font-mono font-bold text-white">{ret ? (ret.recall_at_k * 100).toFixed(1) : '--'}%</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl bg-navy-950 border border-navy-800">
              <span className="text-slate-300 font-medium">NDCG@K (Ranking Quality):</span>
              <span className="font-mono font-bold text-white">{ret ? (ret.ndcg_at_k * 100).toFixed(1) : '--'}%</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl bg-navy-950 border border-navy-800">
              <span className="text-slate-300 font-medium">Relevance Rejection Rate:</span>
              <span className="font-mono font-bold text-amber-400">{ret ? (ret.relevance_threshold_rejection_rate * 100).toFixed(1) : '--'}%</span>
            </div>
          </div>

          {/* Escalation Event Breakdown */}
          <div className="pt-2 border-t border-navy-800">
            <span className="text-xs font-bold text-slate-300 block mb-2">Escalation Events Handled:</span>
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div className="p-2.5 rounded-lg bg-navy-950 border border-navy-800">
                <span className="text-slate-400 block">Critical Bypass:</span>
                <span className="font-bold text-emergency-500 font-mono text-sm">{esc?.critical_bypass_count || 0} incidents</span>
              </div>
              <div className="p-2.5 rounded-lg bg-navy-950 border border-navy-800">
                <span className="text-slate-400 block">Low Relevance Rejections:</span>
                <span className="font-bold text-amber-400 font-mono text-sm">{esc?.low_relevance_escalations || 0} withheld</span>
              </div>
              <div className="p-2.5 rounded-lg bg-navy-950 border border-navy-800">
                <span className="text-slate-400 block">Clarification Triggers:</span>
                <span className="font-bold text-blue-400 font-mono text-sm">{esc?.ambiguous_input_clarifications || 0} prompted</span>
              </div>
              <div className="p-2.5 rounded-lg bg-navy-950 border border-navy-800">
                <span className="text-slate-400 block">Grounded Responses:</span>
                <span className="font-bold text-emerald-400 font-mono text-sm">{esc?.grounded_responses_count || 0} verified</span>
              </div>
            </div>
          </div>
        </div>

      </div>

      {/* Knowledge Base Status & Source Provenance */}
      <div className="bg-navy-900 border border-navy-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-navy-800 pb-3">
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5 text-medic-teal" />
            <h3 className="text-sm font-bold text-white">Medical Knowledge Base Ingestion Status</h3>
          </div>
          <span className="text-xs text-emerald-400 font-bold flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            {kb?.indexed_chunks || 0} Chunks Indexed
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div>
            <span className="text-slate-400 font-bold block mb-1.5 uppercase text-[10px]">Verified Healthcare Sources:</span>
            <div className="flex flex-wrap gap-1.5">
              {(kb?.active_sources || []).map((src, i) => (
                <span key={i} className="px-2.5 py-1 rounded-lg bg-navy-950 border border-navy-800 text-slate-300 font-medium">
                  {src}
                </span>
              ))}
            </div>
          </div>

          <div>
            <span className="text-slate-400 font-bold block mb-1.5 uppercase text-[10px]">Emergency Clinical Categories:</span>
            <div className="flex flex-wrap gap-1.5">
              {(kb?.categories || []).map((cat, i) => (
                <span key={i} className="px-2.5 py-1 rounded-lg bg-navy-950 border border-navy-800 text-medic-teal font-medium">
                  {cat}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

    </div>
  );
};
