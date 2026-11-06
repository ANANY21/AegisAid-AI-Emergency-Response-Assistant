import React, { useState } from 'react';
import { EmergencyResponse, PriorityLevel } from '../types';
import { PriorityBadge } from '../components/PriorityBadge';
import { VisualGuide } from '../components/VisualGuide';
import { ExplainabilityModal } from '../components/ExplainabilityModal';
import { 
  AlertOctagon, PhoneCall, CheckCircle, AlertTriangle, ShieldCheck, 
  ExternalLink, HelpCircle, FileText, XCircle, ArrowLeft, Hospital, 
  Brain, BookOpen, FileCheck, Clock, ShieldAlert, Sparkles, Bookmark,
  Navigation, Phone, MapPin
} from 'lucide-react';

interface ResultViewProps {
  response: EmergencyResponse;
  onNewEmergency: () => void;
  onFindHospitals: () => void;
}

export const ResultView: React.FC<ResultViewProps> = ({ response, onNewEmergency, onFindHospitals }) => {
  const [showExplainModal, setShowExplainModal] = useState(false);
  const [highlightedSource, setHighlightedSource] = useState<number | null>(null);

  const isCritical = response.priority === 'CRITICAL' || response.is_critical_bypass;
  const outcome = response.outcome;
  const breakdown = response.confidence_breakdown;
  const citations = response.citations || [];
  const unsupportedClaims = response.unsupported_claims || [];
  const evidenceVer = response.evidence_verification;

  const scrollToSource = (index: number) => {
    setHighlightedSource(index);
    const elem = document.getElementById(`source-card-${index}`);
    if (elem) {
      elem.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    setTimeout(() => {
      setHighlightedSource(null);
    }, 2500);
  };

  // Helper to render text with interactive [1], [2] citation chips
  const renderTextWithCitations = (text: string) => {
    const parts = text.split(/(\[\d+\])/g);
    return parts.map((part, i) => {
      const match = part.match(/\[(\d+)\]/);
      if (match) {
        const idx = parseInt(match[1], 10);
        return (
          <button
            key={i}
            onClick={() => scrollToSource(idx)}
            className="inline-flex items-center px-1.5 py-0.2 mx-0.5 rounded text-[11px] font-mono font-bold bg-medic-teal/20 text-medic-teal hover:bg-medic-teal hover:text-navy-950 transition-colors border border-medic-teal/30 align-baseline cursor-pointer"
            title={`Jump to Source [${idx}]`}
          >
            [{idx}]
          </button>
        );
      }
      return part;
    });
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      
      {/* Top Navigation & Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <button
          onClick={onNewEmergency}
          className="text-xs font-semibold text-slate-400 hover:text-white flex items-center gap-1.5 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>New Emergency Assessment</span>
        </button>

        <div className="flex items-center gap-2.5">
          {/* Explain Prediction (SHAP) Action Button */}
          <button
            onClick={() => setShowExplainModal(true)}
            className="px-3 py-1.5 rounded-xl bg-navy-800 hover:bg-navy-700 text-medic-teal font-extrabold text-xs flex items-center gap-1.5 border border-medic-teal/30 hover:border-medic-teal/60 transition-all shadow-md"
            title="Inspect real SHAP TreeExplainer feature attributions"
          >
            <Brain className="w-4 h-4 text-medic-teal" />
            <span>Explain Decision (SHAP)</span>
          </button>

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

      {/* Nearest Hospitals via GPS Banner & Cards */}
      {response.nearby_facilities && response.nearby_facilities.length > 0 && (
        <div className="bg-navy-900 border border-emerald-500/40 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-navy-800">
            <div className="flex items-center gap-2.5">
              <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                <Hospital className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-extrabold text-white flex items-center gap-2">
                  <span>Nearest Hospitals (via GPS)</span>
                  <span className="px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800/60 text-[10px] font-mono font-bold flex items-center gap-1">
                    <MapPin className="w-2.5 h-2.5 text-emerald-400" />
                    <span>GPS Active</span>
                  </span>
                </h3>
                <p className="text-xs text-slate-400">
                  {response.user_location_label
                    ? `Nearest verified emergency facilities to ${response.user_location_label}`
                    : 'Closest verified medical facilities identified with live GPS coordinates'}
                </p>
              </div>
            </div>

            <button
              onClick={onFindHospitals}
              className="px-3.5 py-2 rounded-xl bg-navy-800 hover:bg-navy-750 text-medic-teal text-xs font-bold border border-navy-700 flex items-center gap-1.5 transition-all shadow-sm cursor-pointer"
            >
              <Navigation className="w-3.5 h-3.5" />
              <span>Full Interactive Map</span>
            </button>
          </div>

          {/* Hospital Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
            {response.nearby_facilities.slice(0, 4).map((fac, idx) => (
              <div
                key={fac.id || idx}
                className="p-4 rounded-xl bg-navy-950 border border-navy-800 hover:border-emerald-500/40 transition-all space-y-2.5"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="w-5 h-5 rounded-full bg-emerald-600/20 text-emerald-400 font-bold text-xs flex items-center justify-center shrink-0">
                        {idx + 1}
                      </span>
                      <h4 className="font-extrabold text-white text-sm truncate">{fac.name}</h4>
                    </div>
                    <p className="text-xs text-slate-400 mt-1 line-clamp-1">{fac.address}</p>
                  </div>

                  <span className="text-xs font-mono font-black text-medic-teal bg-navy-900 px-2 py-1 rounded-lg border border-navy-800 shrink-0">
                    {fac.distance_km} km
                  </span>
                </div>

                <div className="flex items-center gap-2 text-xs">
                  {fac.has_emergency_room && (
                    <span className="px-2 py-0.5 rounded-md bg-emergency-950 text-emergency-400 border border-emergency-800/50 text-[10px] font-bold">
                      24/7 ER
                    </span>
                  )}
                  {fac.driving_duration_text && (
                    <span className="text-slate-400 text-[11px]">
                      &bull; {fac.driving_duration_text}
                    </span>
                  )}
                  {fac.phone && (
                    <span className="font-mono text-emerald-300 text-[11px] truncate">
                      &bull; {fac.phone}
                    </span>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 pt-1 border-t border-navy-900">
                  {fac.phone ? (
                    <a
                      href={`tel:${fac.phone}`}
                      className="flex-1 py-1.5 px-2.5 rounded-lg bg-emergency-600/20 hover:bg-emergency-600/30 text-emergency-400 border border-emergency-500/30 text-xs font-bold flex items-center justify-center gap-1 transition-colors"
                    >
                      <Phone className="w-3 h-3" />
                      <span>Call</span>
                    </a>
                  ) : (
                    <a
                      href="tel:112"
                      className="flex-1 py-1.5 px-2.5 rounded-lg bg-navy-900 hover:bg-navy-800 text-slate-400 border border-navy-800 text-xs font-bold flex items-center justify-center gap-1 transition-colors"
                    >
                      <Phone className="w-3 h-3 text-emergency-500" />
                      <span>112</span>
                    </a>
                  )}

                  {fac.osm_directions_url && (
                    <a
                      href={fac.osm_directions_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="py-1.5 px-2.5 rounded-lg bg-emerald-950/70 hover:bg-emerald-900/80 text-emerald-300 border border-emerald-600/40 text-xs font-bold flex items-center justify-center gap-1 transition-colors"
                      title="Open in OpenStreetMap"
                    >
                      <ExternalLink className="w-3 h-3 text-emerald-400" />
                      <span>OSM Route</span>
                    </a>
                  )}

                  <a
                    href={fac.directions_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 py-1.5 px-2.5 rounded-lg bg-medic-teal hover:bg-medic-teal-light text-navy-950 text-xs font-black flex items-center justify-center gap-1 transition-colors"
                  >
                    <Navigation className="w-3 h-3" />
                    <span>Navigate</span>
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Summary Box */}
      <div className="bg-navy-900 border border-navy-800 rounded-2xl p-6 shadow-lg space-y-4">
        <div>
          <h2 className="text-xs font-black uppercase text-slate-400 tracking-wider mb-2">Emergency Summary</h2>
          <p className="text-base text-slate-100 font-medium leading-relaxed">
            {renderTextWithCitations(response.summary)}
          </p>
        </div>
        
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
                  <p className="text-sm text-slate-300 leading-relaxed">
                    {renderTextWithCitations(step.details)}
                  </p>
                  
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
                <span>{renderTextWithCitations(prec)}</span>
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
                <span>{renderTextWithCitations(avoid)}</span>
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

      {/* Unsupported Claims Alert (if detected by claim-level verification) */}
      {unsupportedClaims.length > 0 && (
        <div className="p-4 rounded-xl bg-amber-950/60 border border-amber-500/40 text-amber-200 text-xs space-y-2">
          <div className="flex items-center gap-2 font-bold text-amber-300">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span>Evidentiary Support Notice (Claim-Level Verification Alert)</span>
          </div>
          <ul className="list-disc pl-5 space-y-1 text-slate-300 text-[11px]">
            {unsupportedClaims.map((claim, idx) => (
              <li key={idx}>{claim}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Dedicated Section: Medical Evidence & Sources */}
      <div id="medical-sources" className="space-y-4 pt-4 border-t border-navy-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-lg font-extrabold text-white tracking-tight flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-medic-teal" />
              <span>Medical Evidence & Sources</span>
            </h2>
            <p className="text-xs text-slate-400">
              Validated clinical guidelines and protocols grounding the above first-aid instructions
            </p>
          </div>

          {/* Verification Status Pill */}
          {evidenceVer && (
            <div className="flex items-center gap-2 text-xs">
              <span className={`px-2.5 py-1 rounded-lg font-bold border flex items-center gap-1.5 ${
                evidenceVer.verification_passed 
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' 
                  : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
              }`}>
                <FileCheck className="w-3.5 h-3.5" />
                <span>{evidenceVer.verification_passed ? '100% Evidence Grounded' : 'Partial Evidence'}</span>
              </span>
              <span className="font-mono text-slate-400 text-[11px]">
                Grounding: {(evidenceVer.mean_grounding_score * 100).toFixed(0)}%
              </span>
            </div>
          )}
        </div>

        {/* Source Cards Grid */}
        <div className="grid grid-cols-1 gap-4">
          {citations.length > 0 ? (
            citations.map((c) => (
              <div 
                key={c.citation_index}
                id={`source-card-${c.citation_index}`}
                className={`p-5 rounded-2xl bg-navy-900 border transition-all duration-300 space-y-3 ${
                  highlightedSource === c.citation_index
                    ? 'border-medic-teal ring-2 ring-medic-teal/40 bg-navy-850 shadow-xl'
                    : 'border-navy-800 hover:border-navy-700'
                }`}
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded-md text-xs font-mono font-black bg-medic-teal text-navy-950">
                        {c.citation_tag}
                      </span>
                      <h3 className="text-sm font-bold text-white">{c.document_title}</h3>
                    </div>
                    <p className="text-xs text-slate-400">
                      Organization: <strong className="text-slate-300">{c.publishing_organization}</strong>
                      {c.page_number && <span> &bull; {c.page_number}</span>}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                      c.review_status === 'Verified' 
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        : c.review_status === 'Pending Review'
                        ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                        : 'bg-emergency-500/10 text-emergency-400 border-emergency-500/30'
                    }`}>
                      {c.review_status}
                    </span>

                    <span className="text-[11px] font-mono text-medic-teal bg-navy-950 px-2 py-0.5 rounded border border-navy-800">
                      Support: {(c.claim_support_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                {/* Section & Cited Excerpt */}
                <div className="p-3 rounded-xl bg-navy-950 border border-navy-800 text-xs space-y-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                    Section: {c.section}
                  </span>
                  <p className="text-slate-300 italic leading-relaxed">
                    &ldquo;{c.cited_excerpt}&rdquo;
                  </p>
                </div>

                {/* Footer Link & Doc ID */}
                <div className="flex items-center justify-between text-xs pt-1">
                  <span className="font-mono text-[10px] text-slate-500">
                    ID: {c.document_id} &bull; Type: {c.document_type}
                  </span>

                  {c.source_url && (
                    <a
                      href={c.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs font-bold text-medic-teal hover:underline flex items-center gap-1"
                    >
                      <span>View Official Guideline</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  )}
                </div>
              </div>
            ))
          ) : (
            /* Fallback to basic sources if citations array empty */
            response.sources.map((s, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-navy-900 border border-navy-800 text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white">[{idx+1}] {s.document_title}</span>
                  <span className="font-mono text-medic-teal">Relevance: {(s.relevance_score * 100).toFixed(1)}%</span>
                </div>
                <p className="text-slate-400">Publishing Org: {s.source_name} | Section: {s.section}</p>
                {s.source_url && (
                  <a
                    href={s.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-medic-teal hover:underline flex items-center gap-1 text-[11px]"
                  >
                    <span>Official Protocol URL</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            ))
          )}
        </div>

        {/* Trauma Center Locator CTA Banner */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-navy-900 via-navy-850 to-navy-900 border border-navy-700 shadow-lg">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-medic-teal/10 border border-medic-teal/30 text-medic-teal">
              <Hospital className="w-6 h-6" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-white">Need Hospitalization or Trauma Care?</h4>
              <p className="text-xs text-slate-400">Locate certified emergency departments, trauma centers, and ICU beds nearby.</p>
            </div>
          </div>

          <button
            onClick={onFindHospitals}
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-medic-teal hover:bg-medic-teal-light text-navy-950 font-black text-xs flex items-center justify-center gap-2 shadow-lg transition-all shrink-0"
          >
            <Hospital className="w-4 h-4" />
            <span>Find Nearby Trauma Centers</span>
          </button>
        </div>

      </div>

      {/* Safety Disclaimer Footer */}
      <p className="text-[11px] text-slate-500 text-center leading-relaxed max-w-2xl mx-auto pt-4 border-t border-navy-900">
        {response.disclaimer}
      </p>

      {/* Explainable AI (SHAP) Modal */}
      <ExplainabilityModal
        isOpen={showExplainModal}
        onClose={() => setShowExplainModal(false)}
        initialExplanation={response.shap_summary}
        emergencyText={response.summary}
      />

    </div>
  );
};
