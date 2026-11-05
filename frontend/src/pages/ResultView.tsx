import React, { useState } from 'react';
import { EmergencyResponse, PriorityLevel } from '../types';
import { PriorityBadge } from '../components/PriorityBadge';
import { VisualGuide } from '../components/VisualGuide';
import { 
  AlertOctagon, PhoneCall, CheckCircle, AlertTriangle, ShieldCheck, 
  ExternalLink, HelpCircle, FileText, XCircle, ArrowLeft, Hospital, RefreshCw 
} from 'lucide-react';

interface ResultViewProps {
  response: EmergencyResponse;
  onNewEmergency: () => void;
  onFindHospitals: () => void;
}

export const ResultView: React.FC<ResultViewProps> = ({ response, onNewEmergency, onFindHospitals }) => {
  const [showSourcesModal, setShowSourcesModal] = useState(false);

  const isCritical = response.priority === 'CRITICAL' || response.is_critical_bypass;
  const outcome = response.outcome;
  const breakdown = response.confidence_breakdown;

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      
      {/* Top Navigation & Status */}
      <div className="flex items-center justify-between">
        <button
          onClick={onNewEmergency}
          className="text-xs font-semibold text-slate-400 hover:text-white flex items-center gap-1.5 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>New Emergency Assessment</span>
        </button>

        <div className="flex items-center gap-2">
          <PriorityBadge priority={response.priority} confidence={breakdown.classifier_confidence} />
        </div>
      </div>

      {/* Immediate Emergency Bypass Banner (If Critical) */}
      {isCritical && (
        <div className="p-5 rounded-2xl bg-emergency-950/80 border-2 border-emergency-500 shadow-2xl shadow-emergency-600/30 flex flex-col sm:flex-row items-center justify-between gap-4 animate-pulse">
          <div className="flex items-start gap-3">
            <AlertOctagon className="w-8 h-8 text-emergency-500 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-base font-extrabold text-white uppercase tracking-wider">
                CRITICAL EMERGENCY WARNING
              </h3>
              <p className="text-xs text-emergency-200 mt-1 leading-relaxed">
                {response.immediate_emergency_warning || 'High-risk life-threatening emergency detected. Immediately call emergency services.'}
              </p>
            </div>
          </div>

          <a
            href="tel:911"
            className="w-full sm:w-auto px-6 py-3 rounded-xl bg-emergency-600 hover:bg-emergency-500 text-white font-extrabold text-sm flex items-center justify-center gap-2 shadow-lg shadow-emergency-600/50 transition-all shrink-0"
          >
            <PhoneCall className="w-4 h-4" />
            <span>Call 911 / 112 Now</span>
          </a>
        </div>
      )}

      {/* Escalation / Low Relevance / Ambiguity Notice */}
      {outcome === 'LOW_RETRIEVAL_RELEVANCE' && (
        <div className="p-4 rounded-xl bg-amber-950/50 border border-amber-500/40 text-amber-200 text-xs flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-white block mb-0.5">Retrieved Knowledge Below Relevance Threshold:</span>
            <span>To uphold medical safety, speculative guidance has been withheld. Please seek in-person professional medical evaluation.</span>
          </div>
        </div>
      )}

      {outcome === 'AMBIGUOUS_INPUT' && (
        <div className="p-5 rounded-xl bg-blue-950/40 border border-blue-500/30 text-blue-200 space-y-3">
          <div className="flex items-center gap-2">
            <HelpCircle className="w-5 h-5 text-blue-400" />
            <h4 className="text-sm font-bold text-white">Clinical Clarification Required</h4>
          </div>
          <p className="text-xs text-slate-300">
            The emergency narrative lacks specific anatomical or symptomatic parameters for safe first-aid triage.
            Please consider:
          </p>
          <ul className="list-disc pl-5 text-xs text-blue-300 space-y-1">
            {response.clarification_questions.map((q, idx) => (
              <li key={idx}>{q}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Summary Box */}
      <div className="bg-navy-900 border border-navy-800 rounded-2xl p-6 shadow-lg">
        <h2 className="text-xs font-black uppercase text-slate-400 tracking-wider mb-2">Emergency Summary</h2>
        <p className="text-base text-slate-100 font-medium leading-relaxed">{response.summary}</p>
        
        {/* Confidence Breakdown Indicators */}
        <div className="mt-4 pt-4 border-t border-navy-800 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div>
            <span className="text-slate-500 block text-[10px] uppercase font-bold">Classifier Confidence</span>
            <span className="font-mono font-bold text-white">{(breakdown.classifier_confidence * 100).toFixed(1)}%</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] uppercase font-bold">Retrieval Relevance</span>
            <span className="font-mono font-bold text-medic-teal">{(breakdown.retrieval_relevance_score * 100).toFixed(1)}%</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] uppercase font-bold">Validation Status</span>
            <span className={`font-bold ${breakdown.relevance_status === 'VALID' ? 'text-emerald-400' : 'text-amber-400'}`}>
              {breakdown.relevance_status}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] uppercase font-bold">Evidence Grounding</span>
            <span className="font-mono font-bold text-slate-300">{(breakdown.faithfulness_score * 100).toFixed(0)}%</span>
          </div>
        </div>
      </div>

      {/* Step-by-Step First Aid Guidance */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-extrabold text-white tracking-tight flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-medic-teal" />
            <span>Recommended First-Aid Actions</span>
          </h2>
          <span className="text-xs text-slate-400">Step-by-step verified procedures</span>
        </div>

        <div className="space-y-4">
          {response.first_aid_steps.map((step) => (
            <div key={step.step_number} className="bg-navy-900 border border-navy-800 rounded-2xl p-6 shadow-md space-y-3">
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-xl bg-emergency-600/20 text-emergency-400 font-extrabold flex items-center justify-center shrink-0 border border-emergency-500/20">
                  {step.step_number}
                </div>
                <div className="flex-1">
                  <h3 className="text-base font-bold text-white mb-1">{step.action}</h3>
                  <p className="text-sm text-slate-300 leading-relaxed">{step.details}</p>
                  
                  {step.caution && (
                    <div className="mt-2 text-xs text-amber-300 font-medium flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 shrink-0 text-amber-400" />
                      <span>{step.caution}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Visual Procedure Illustration if applicable */}
              {step.visual_guide_key && (
                <VisualGuide guideKey={step.visual_guide_key} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Precautions & What to Avoid Side-by-Side */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Important Precautions */}
        <div className="bg-navy-900 border border-navy-800 rounded-2xl p-6 space-y-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Important Precautions</span>
          </h3>
          <ul className="space-y-2 text-xs text-slate-300">
            {response.precautions.map((prec, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                <span>{prec}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* What to Avoid (Do NOT do) */}
        <div className="bg-navy-900 border border-navy-800 rounded-2xl p-6 space-y-3">
          <h3 className="text-sm font-bold text-emergency-400 flex items-center gap-2">
            <XCircle className="w-4 h-4 text-emergency-500" />
            <span>What to Avoid (Contraindications)</span>
          </h3>
          <ul className="space-y-2 text-xs text-slate-300">
            {response.what_to_avoid.map((avoid, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emergency-500 mt-1.5 shrink-0" />
                <span>{avoid}</span>
              </li>
            ))}
          </ul>
        </div>

      </div>

      {/* When to Seek Immediate Care */}
      <div className="p-4 rounded-xl bg-navy-900 border border-navy-800 text-xs text-slate-300 space-y-1">
        <span className="font-bold text-white block">When to Seek Immediate Hospitalization:</span>
        <p>{response.when_to_seek_immediate_care}</p>
      </div>

      {/* Provenance & Medical Sources */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-xl bg-navy-950 border border-navy-800 text-xs">
        <div className="flex items-center gap-2 text-slate-400">
          <FileText className="w-4 h-4 text-medic-teal" />
          <span>Grounded in {response.sources.length} verified medical protocol references</span>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowSourcesModal(true)}
            className="text-xs text-medic-teal hover:underline font-bold flex items-center gap-1"
          >
            <span>View Medical Citations</span>
            <ExternalLink className="w-3 h-3" />
          </button>

          <button
            onClick={onFindHospitals}
            className="px-4 py-2 rounded-lg bg-navy-800 hover:bg-navy-700 text-white font-bold text-xs flex items-center gap-1.5 border border-navy-700 transition-colors"
          >
            <Hospital className="w-3.5 h-3.5 text-medic-teal" />
            <span>Find Nearby Trauma Centers</span>
          </button>
        </div>
      </div>

      {/* Medical Citations Modal */}
      {showSourcesModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="bg-navy-900 border border-navy-700 rounded-2xl max-w-2xl w-full p-6 space-y-4 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-navy-800 pb-3">
              <h3 className="text-base font-bold text-white">Retrieved Evidence Provenance</h3>
              <button
                onClick={() => setShowSourcesModal(false)}
                className="text-slate-400 hover:text-white text-sm font-bold"
              >
                ✕ Close
              </button>
            </div>

            <div className="space-y-3">
              {response.sources.map((s, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-navy-950 border border-navy-800 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white">{s.document_title}</span>
                    <span className="font-mono text-medic-teal">Score: {(s.relevance_score * 100).toFixed(1)}%</span>
                  </div>
                  <p className="text-slate-400">Source: <strong className="text-slate-300">{s.source_name}</strong> | Section: {s.section}</p>
                  {s.source_url && (
                    <a
                      href={s.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-medic-teal hover:underline flex items-center gap-1 mt-1 text-[11px]"
                    >
                      <span>Official Protocol URL</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Safety Disclaimer Footer */}
      <p className="text-[11px] text-slate-500 text-center leading-relaxed max-w-2xl mx-auto">
        {response.disclaimer}
      </p>

    </div>
  );
};
