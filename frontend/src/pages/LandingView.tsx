import React from 'react';
import { Shield, Activity, Search, AlertOctagon, ArrowRight, HeartPulse, Hospital, CheckCircle2 } from 'lucide-react';

interface LandingViewProps {
  onStartEmergency: () => void;
  onFindHospitals: () => void;
  onViewAdmin: () => void;
}

export const LandingView: React.FC<LandingViewProps> = ({
  onStartEmergency,
  onFindHospitals,
  onViewAdmin,
}) => {
  return (
    <div className="space-y-16 pb-16">
      
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-b from-navy-900 to-navy-950 border border-navy-800 p-8 sm:p-14 text-center">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-emergency-600/10 via-transparent to-transparent pointer-events-none" />
        
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-navy-800/80 border border-navy-700 text-xs font-semibold text-slate-300 mb-6">
          <Shield className="w-4 h-4 text-emergency-500" />
          <span>Safety-Oriented • Retrieval-Validated • Calibrated Triage</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight max-w-4xl mx-auto leading-tight sm:leading-none">
          Emergency assistance, <br className="hidden sm:inline" />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-emergency-500 via-rose-400 to-amber-300">
            when every second matters.
          </span>
        </h1>

        <p className="mt-6 text-base sm:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
          Immediate context-aware first-aid guidance, ML incident prioritization, and nearby trauma care with controlled escalation when reliable medical evidence is unavailable.
        </p>

        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            onClick={onStartEmergency}
            className="w-full sm:w-auto px-8 py-4 rounded-xl bg-gradient-to-r from-emergency-600 to-emergency-700 hover:from-emergency-500 hover:to-emergency-600 text-white font-bold text-base shadow-xl shadow-emergency-600/30 flex items-center justify-center gap-3 transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <Activity className="w-5 h-5 animate-pulse" />
            <span>Start Emergency Assessment</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <button
            onClick={onFindHospitals}
            className="w-full sm:w-auto px-6 py-4 rounded-xl bg-navy-800 hover:bg-navy-700 text-slate-200 border border-navy-700 font-semibold text-sm flex items-center justify-center gap-2 transition-all"
          >
            <Hospital className="w-4 h-4 text-medic-teal" />
            <span>Locate Nearby Hospitals</span>
          </button>
        </div>

        {/* Immediate Life-Threatening Warning Banner */}
        <div className="mt-10 max-w-2xl mx-auto p-4 rounded-xl bg-emergency-950/60 border border-emergency-500/40 text-left flex items-start gap-3">
          <AlertOctagon className="w-5 h-5 text-emergency-500 shrink-0 mt-0.5" />
          <p className="text-xs text-emergency-200 leading-relaxed font-medium">
            <span className="font-bold text-white">IMMEDIATE EMERGENCY RULE: </span>
            If a casualty is unresponsive, not breathing, choking silently, or experiencing severe bleeding, immediately call <strong className="text-white underline">911 / 112</strong>. Do not wait for AI processing.
          </p>
        </div>
      </section>

      {/* How It Works - The 4-Stage Architectural Pipeline */}
      <section className="space-y-8">
        <div className="text-center max-w-2xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">Engineered for Safety & Reliability</h2>
          <p className="text-sm text-slate-400 mt-2">Zero speculative hallucinations. Every protocol is grounded in official medical guidelines.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-navy-900 border border-navy-800 rounded-2xl p-6 relative overflow-hidden">
            <div className="w-10 h-10 rounded-xl bg-blue-600/20 text-blue-400 flex items-center justify-center font-bold text-lg mb-4">1</div>
            <h3 className="text-base font-bold text-white mb-2">Multimodal Intake</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Accepts free-form text, live voice dictation with transcription review, and validated image uploads.
            </p>
          </div>

          <div className="bg-navy-900 border border-navy-800 rounded-2xl p-6 relative overflow-hidden">
            <div className="w-10 h-10 rounded-xl bg-amber-600/20 text-amber-400 flex items-center justify-center font-bold text-lg mb-4">2</div>
            <h3 className="text-base font-bold text-white mb-2">ML Incident Prioritization</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Calibrated machine learning classifier categorizes priority into LOW, MODERATE, HIGH, and CRITICAL.
            </p>
          </div>

          <div className="bg-navy-900 border border-navy-800 rounded-2xl p-6 relative overflow-hidden">
            <div className="w-10 h-10 rounded-xl bg-medic-teal/20 text-medic-teal flex items-center justify-center font-bold text-lg mb-4">3</div>
            <h3 className="text-base font-bold text-white mb-2">Validated Medical RAG</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Retrieves from WHO, AHA, NHS guidelines. Evaluates relevance threshold and rejects unsupported queries.
            </p>
          </div>

          <div className="bg-navy-900 border border-navy-800 rounded-2xl p-6 relative overflow-hidden">
            <div className="w-10 h-10 rounded-xl bg-emergency-600/20 text-emergency-400 flex items-center justify-center font-bold text-lg mb-4">4</div>
            <h3 className="text-base font-bold text-white mb-2">Controlled Escalation</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Ambiguous inputs trigger clarification questions; conflicting or low-confidence cases escalate to human clinicians.
            </p>
          </div>
        </div>
      </section>

      {/* Clinical Disclaimer Section */}
      <section className="bg-navy-900/60 border border-navy-800 rounded-2xl p-6 text-xs text-slate-400 leading-relaxed flex items-start gap-4">
        <Shield className="w-6 h-6 text-slate-500 shrink-0 mt-0.5" />
        <div>
          <h4 className="font-bold text-slate-200 mb-1">Clinical Decision Support Disclaimer</h4>
          <p>
            AegisAid is an assistive technology platform intended for educational first-aid decision support and triage assistance. It is NOT an authorized diagnostic device or clinical provider. Neither the generative AI models nor the classifier should replace immediate professional in-person emergency care.
          </p>
        </div>
      </section>

    </div>
  );
};
