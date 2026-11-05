import React from 'react';
import { Activity, CheckCircle2, Clock, AlertTriangle, ShieldCheck, Database, FileCheck } from 'lucide-react';

interface ProcessingViewProps {
  currentStage: number; // 0 to 6
  isBypassingDelays?: boolean;
}

const STAGES = [
  { label: 'Understanding emergency context & sanitizing input', icon: Activity },
  { label: 'Extracting clinical symptoms & affected anatomy', icon: FileCheck },
  { label: 'ML incident prioritization (Calibrated Triage Classifier)', icon: AlertTriangle },
  { label: 'Retrieving official medical guidelines (WHO / AHA / NHS)', icon: Database },
  { label: 'Validating retrieval relevance threshold & conflicts', icon: ShieldCheck },
  { label: 'Confidence and safety escalation evaluation', icon: ShieldCheck },
  { label: 'Preparing grounded step-by-step guidance', icon: CheckCircle2 }
];

export const ProcessingView: React.FC<ProcessingViewProps> = ({ currentStage, isBypassingDelays }) => {
  return (
    <div className="max-w-2xl mx-auto py-12 px-4 text-center space-y-8">
      
      {/* Central Spinner / Pulse */}
      <div className="relative w-24 h-24 mx-auto flex items-center justify-center">
        <div className="absolute inset-0 rounded-full border-4 border-emergency-500/20 animate-ping" />
        <div className="w-20 h-20 rounded-full bg-emergency-600/10 border-2 border-emergency-500 flex items-center justify-center">
          <Activity className="w-10 h-10 text-emergency-500 animate-pulse" />
        </div>
      </div>

      <div>
        <h2 className="text-2xl font-extrabold text-white tracking-tight">
          {isBypassingDelays ? 'Critical Emergency Bypass Engaged' : 'Analyzing Medical Emergency'}
        </h2>
        <p className="text-sm text-slate-400 mt-2">
          {isBypassingDelays
            ? 'Bypassing non-essential delays to deliver immediate life-saving protocol.'
            : 'Executing deterministic safety checks, medical RAG, and retrieval validation.'}
        </p>
      </div>

      {/* Meaningful Pipeline Stages */}
      <div className="bg-navy-900 border border-navy-800 rounded-2xl p-6 text-left space-y-4 shadow-xl">
        {STAGES.map((st, idx) => {
          const isDone = idx < currentStage;
          const isCurrent = idx === currentStage;
          const Icon = st.icon;

          return (
            <div
              key={idx}
              className={`flex items-center gap-3.5 p-3 rounded-xl transition-all ${
                isCurrent 
                  ? 'bg-navy-800 border border-emergency-500/40 text-white shadow-sm' 
                  : isDone
                  ? 'text-slate-300 opacity-90'
                  : 'text-slate-500 opacity-40'
              }`}
            >
              <div className="shrink-0">
                {isDone ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                ) : isCurrent ? (
                  <div className="w-5 h-5 border-2 border-emergency-500/30 border-t-emergency-500 rounded-full animate-spin" />
                ) : (
                  <Clock className="w-5 h-5 text-slate-600" />
                )}
              </div>

              <div className="flex-1">
                <span className="text-xs font-semibold">{st.label}</span>
              </div>

              {isCurrent && (
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-emergency-600/20 text-emergency-400 font-bold border border-emergency-500/20">
                  Active
                </span>
              )}
            </div>
          );
        })}
      </div>

      <p className="text-xs text-slate-500 italic">
        "Never wait for AI computation if the casualty is in cardiac arrest or catastrophic bleeding — call 911 immediately."
      </p>

    </div>
  );
};
