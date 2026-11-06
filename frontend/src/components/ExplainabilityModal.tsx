import React, { useState, useEffect } from 'react';
import { 
  SHAPExplanationResponse, SHAPFeatureContribution, PriorityLevel 
} from '../types';
import { explainIncidentPrediction } from '../services/api';
import { 
  Brain, TrendingUp, TrendingDown, AlertCircle, BarChart3, 
  HelpCircle, RefreshCw, X, ShieldAlert, ArrowRight, Layers
} from 'lucide-react';

interface ExplainabilityModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialExplanation?: SHAPExplanationResponse | null;
  emergencyText: string;
  patientAge?: number;
  duration?: string;
}

export const ExplainabilityModal: React.FC<ExplainabilityModalProps> = ({
  isOpen,
  onClose,
  initialExplanation,
  emergencyText,
  patientAge = 35,
}) => {
  const [explanation, setExplanation] = useState<SHAPExplanationResponse | null>(initialExplanation || null);
  const [selectedClass, setSelectedClass] = useState<PriorityLevel>(initialExplanation?.predicted_class || 'CRITICAL');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'waterfall' | 'features' | 'multiclass'>('waterfall');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialExplanation) {
      setExplanation(initialExplanation);
      setSelectedClass(initialExplanation.predicted_class);
    }
  }, [initialExplanation]);

  if (!isOpen) return null;

  const handleClassChange = async (targetClass: PriorityLevel) => {
    setSelectedClass(targetClass);
    setLoading(true);
    setError(null);
    try {
      const updated = await explainIncidentPrediction({
        text: emergencyText,
        age: patientAge,
        target_class: targetClass
      });
      setExplanation(updated);
    } catch (err: any) {
      setError(err.message || 'Failed to calculate class-specific SHAP explanation');
    } finally {
      setLoading(false);
    }
  };

  const currentFeatures = explanation?.feature_contributions || [];
  const baseVal = explanation?.base_value ?? 0.25;
  const outputVal = explanation?.model_output_value ?? 0.85;

  // Compute waterfall running steps
  let runningVal = baseVal;
  const waterfallSteps = currentFeatures.slice(0, 8).map((feat) => {
    const start = runningVal;
    runningVal += feat.shap_value;
    const end = runningVal;
    return {
      ...feat,
      start,
      end,
    };
  });

  const getPriorityColor = (p: PriorityLevel) => {
    switch (p) {
      case 'CRITICAL': return 'bg-emergency-500/20 text-emergency-400 border-emergency-500/30';
      case 'HIGH': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'MODERATE': return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30';
      case 'LOW': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/80 backdrop-blur-md overflow-y-auto">
      <div className="bg-navy-950 border border-navy-700 rounded-3xl max-w-4xl w-full p-6 sm:p-8 space-y-6 shadow-2xl relative my-auto max-h-[92vh] overflow-y-auto text-slate-200">
        
        {/* Header */}
        <div className="flex items-start justify-between border-b border-navy-800 pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-medic-teal/10 border border-medic-teal/30 text-medic-teal">
                <Brain className="w-5 h-5" />
              </div>
              <h2 className="text-xl font-extrabold text-white tracking-tight">
                Explainable AI – Incident Decision Analysis
              </h2>
            </div>
            <p className="text-xs text-slate-400">
              SHAP TreeExplainer feature attributions for calibrated triage pipeline ({explanation?.model_version || 'rf-cost-calibrated-triage-v2.0'})
            </p>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-navy-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Prediction Summary KPI Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3.5 rounded-2xl bg-navy-900 border border-navy-800">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              Predicted Priority
            </span>
            <span className={`inline-block px-2.5 py-0.5 rounded-md text-xs font-black border ${getPriorityColor(explanation?.predicted_class || 'CRITICAL')}`}>
              {explanation?.predicted_class}
            </span>
          </div>

          <div className="p-3.5 rounded-2xl bg-navy-900 border border-navy-800">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              Base Value E[f(x)]
            </span>
            <span className="text-base font-mono font-bold text-slate-300">
              {baseVal.toFixed(3)}
            </span>
          </div>

          <div className="p-3.5 rounded-2xl bg-navy-900 border border-navy-800">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              Model Output f(x)
            </span>
            <span className="text-base font-mono font-bold text-medic-teal">
              {outputVal.toFixed(3)}
            </span>
          </div>

          <div className="p-3.5 rounded-2xl bg-navy-900 border border-navy-800">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              Safety Threshold &tau;<sub>crit</sub>
            </span>
            <span className="text-base font-mono font-bold text-emergency-400">
              {(explanation?.threshold_applied || 0.20).toFixed(2)}
            </span>
          </div>
        </div>

        {/* Multiclass Class Focus Selector Tabs */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-2xl bg-navy-900/60 border border-navy-800">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-slate-400" />
            <span className="text-xs font-bold text-slate-300">Explain Attribution For Class:</span>
          </div>

          <div className="flex items-center gap-1.5">
            {(['CRITICAL', 'HIGH', 'MODERATE', 'LOW'] as PriorityLevel[]).map((cls) => {
              const isSelected = selectedClass === cls;
              const prob = explanation?.class_probabilities?.[cls];
              return (
                <button
                  key={cls}
                  onClick={() => handleClassChange(cls)}
                  disabled={loading}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                    isSelected 
                      ? 'bg-medic-teal text-navy-950 shadow-md font-extrabold'
                      : 'bg-navy-800 text-slate-400 hover:text-white hover:bg-navy-700'
                  }`}
                >
                  <span>{cls}</span>
                  {prob !== undefined && (
                    <span className={`text-[10px] font-mono px-1 py-0.2 rounded ${isSelected ? 'bg-navy-950/20 text-navy-950' : 'bg-navy-900 text-slate-400'}`}>
                      {(prob * 100).toFixed(0)}%
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* View Toggle Tabs */}
        <div className="flex items-center gap-2 border-b border-navy-800 pb-2">
          <button
            onClick={() => setActiveTab('waterfall')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-colors flex items-center gap-2 ${
              activeTab === 'waterfall' 
                ? 'bg-navy-800 text-medic-teal border border-navy-700' 
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>SHAP Waterfall Plot</span>
          </button>

          <button
            onClick={() => setActiveTab('features')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-colors flex items-center gap-2 ${
              activeTab === 'features' 
                ? 'bg-navy-800 text-medic-teal border border-navy-700' 
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <TrendingUp className="w-4 h-4" />
            <span>Feature Drivers & Table</span>
          </button>

          <button
            onClick={() => setActiveTab('multiclass')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-colors flex items-center gap-2 ${
              activeTab === 'multiclass' 
                ? 'bg-navy-800 text-medic-teal border border-navy-700' 
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>All-Class Decomposition</span>
          </button>
        </div>

        {loading ? (
          <div className="py-16 flex flex-col items-center justify-center space-y-3">
            <RefreshCw className="w-8 h-8 text-medic-teal animate-spin" />
            <p className="text-xs text-slate-400">Computing ensemble SHAP tree values...</p>
          </div>
        ) : error ? (
          <div className="p-4 rounded-xl bg-emergency-950/50 border border-emergency-500/40 text-emergency-200 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-emergency-400 shrink-0" />
            <span>{error}</span>
          </div>
        ) : (
          <>
            {/* TAB 1: SHAP Waterfall Plot */}
            {activeTab === 'waterfall' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1.5 text-emergency-400 font-semibold">
                      <span className="w-3 h-3 rounded bg-emergency-500 inline-block" />
                      Risk Driver (Elevates {selectedClass})
                    </span>
                    <span className="flex items-center gap-1.5 text-medic-teal font-semibold">
                      <span className="w-3 h-3 rounded bg-medic-teal inline-block" />
                      Mitigating Factor (Reduces {selectedClass})
                    </span>
                  </div>
                  <span className="font-mono text-[11px]">Values in SHAP &phi; units</span>
                </div>

                <div className="p-5 rounded-2xl bg-navy-900 border border-navy-800 space-y-4">
                  {/* Waterfall Start Baseline */}
                  <div className="flex items-center justify-between text-xs pb-2 border-b border-navy-800 font-mono">
                    <span className="text-slate-400 font-sans font-bold flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-slate-400" />
                      Baseline Expected Value E[f(x)]
                    </span>
                    <span className="font-bold text-slate-300">{baseVal.toFixed(4)}</span>
                  </div>

                  {/* Waterfall Steps */}
                  <div className="space-y-2.5">
                    {waterfallSteps.map((step, idx) => {
                      const isPos = step.shap_value >= 0;
                      const absVal = Math.abs(step.shap_value);
                      const barWidth = Math.min(100, Math.max(8, absVal * 150));

                      return (
                        <div key={idx} className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs py-1 hover:bg-navy-800/40 px-2 rounded-xl transition-colors">
                          <div className="flex items-center gap-2 min-w-[220px]">
                            {isPos ? (
                              <TrendingUp className="w-3.5 h-3.5 text-emergency-400 shrink-0" />
                            ) : (
                              <TrendingDown className="w-3.5 h-3.5 text-medic-teal shrink-0" />
                            )}
                            <span className="font-bold text-white truncate">{step.feature_name}</span>
                          </div>

                          <div className="flex-1 flex items-center gap-3">
                            <div className="flex-1 bg-navy-950 h-5 rounded-lg overflow-hidden relative flex items-center px-2">
                              <div
                                style={{ width: `${barWidth}%` }}
                                className={`h-3 rounded-md transition-all ${
                                  isPos ? 'bg-emergency-500 shadow-sm shadow-emergency-500/50' : 'bg-medic-teal shadow-sm shadow-medic-teal/50'
                                }`}
                              />
                            </div>
                            <span className={`font-mono font-bold text-xs min-w-[65px] text-right ${isPos ? 'text-emergency-400' : 'text-medic-teal'}`}>
                              {isPos ? '+' : ''}{step.shap_value.toFixed(4)}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Waterfall End Result */}
                  <div className="flex items-center justify-between text-xs pt-3 border-t border-navy-800 font-mono">
                    <span className="text-white font-sans font-bold flex items-center gap-1.5">
                      <ArrowRight className="w-4 h-4 text-medic-teal" />
                      Final Model Prediction Output f(x)
                    </span>
                    <span className="font-extrabold text-medic-teal text-sm">{outputVal.toFixed(4)}</span>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: Feature Drivers & Detailed Table */}
            {activeTab === 'features' && (
              <div className="space-y-5">
                {/* Horizontal Positive vs Negative Summary */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="p-4 rounded-2xl bg-navy-900 border border-navy-800 space-y-2">
                    <h4 className="text-xs font-black uppercase tracking-wider text-emergency-400 flex items-center gap-1.5">
                      <TrendingUp className="w-4 h-4" />
                      <span>Top Positive Push (Elevating {selectedClass})</span>
                    </h4>
                    <div className="space-y-1.5">
                      {explanation?.top_positive_features.map((f, i) => (
                        <div key={i} className="flex items-center justify-between text-xs">
                          <span className="text-slate-300 truncate">{f.feature_name}</span>
                          <span className="font-mono font-bold text-emergency-400">+{f.shap_value.toFixed(4)}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-navy-900 border border-navy-800 space-y-2">
                    <h4 className="text-xs font-black uppercase tracking-wider text-medic-teal flex items-center gap-1.5">
                      <TrendingDown className="w-4 h-4" />
                      <span>Top Negative Push (Suppressing {selectedClass})</span>
                    </h4>
                    <div className="space-y-1.5">
                      {explanation?.top_negative_features.map((f, i) => (
                        <div key={i} className="flex items-center justify-between text-xs">
                          <span className="text-slate-300 truncate">{f.feature_name}</span>
                          <span className="font-mono font-bold text-medic-teal">{f.shap_value.toFixed(4)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Full Feature Table */}
                <div className="rounded-2xl border border-navy-800 overflow-hidden bg-navy-900">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-navy-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-navy-800">
                      <tr>
                        <th className="p-3">Rank</th>
                        <th className="p-3">Clinical / Model Feature</th>
                        <th className="p-3">Input Value</th>
                        <th className="p-3 text-right">SHAP Value (&phi;)</th>
                        <th className="p-3">Direction</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-navy-800">
                      {currentFeatures.map((f) => (
                        <tr key={f.rank} className="hover:bg-navy-800/40 transition-colors">
                          <td className="p-3 font-mono text-slate-400">#{f.rank}</td>
                          <td className="p-3">
                            <span className="font-bold text-white block">{f.feature_name}</span>
                            <span className="text-[11px] text-slate-400">{f.description}</span>
                          </td>
                          <td className="p-3 font-mono text-slate-300">{f.feature_value}</td>
                          <td className={`p-3 font-mono font-bold text-right ${f.shap_value >= 0 ? 'text-emergency-400' : 'text-medic-teal'}`}>
                            {f.shap_value >= 0 ? '+' : ''}{f.shap_value.toFixed(4)}
                          </td>
                          <td className="p-3">
                            <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                              f.shap_value >= 0 ? 'bg-emergency-500/20 text-emergency-400' : 'bg-medic-teal/20 text-medic-teal'
                            }`}>
                              {f.impact}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 3: All-Class Comparative Breakdown */}
            {activeTab === 'multiclass' && explanation?.multiclass_breakdown && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {Object.entries(explanation.multiclass_breakdown).map(([clsName, detail]) => (
                  <div key={clsName} className="p-4 rounded-2xl bg-navy-900 border border-navy-800 space-y-3">
                    <div className="flex items-center justify-between border-b border-navy-800 pb-2">
                      <span className={`font-black text-xs px-2.5 py-0.5 rounded border ${getPriorityColor(clsName as PriorityLevel)}`}>
                        {clsName}
                      </span>
                      <span className="text-xs font-mono font-bold text-slate-300">
                        Prob: {(detail.calibrated_probability * 100).toFixed(1)}%
                      </span>
                    </div>

                    <div className="text-xs space-y-1.5">
                      <div className="flex justify-between text-slate-400 text-[11px]">
                        <span>Base value E[f]:</span>
                        <span className="font-mono text-slate-300">{detail.base_value.toFixed(3)}</span>
                      </div>
                      <span className="text-[11px] font-bold text-slate-400 block pt-1">Leading Contributing Features:</span>
                      {detail.top_features.map((tf, idx) => (
                        <div key={idx} className="flex items-center justify-between text-[11px]">
                          <span className="text-slate-300 truncate max-w-[180px]">{tf.feature_name}</span>
                          <span className={`font-mono ${tf.shap_value >= 0 ? 'text-emergency-400' : 'text-medic-teal'}`}>
                            {tf.shap_value >= 0 ? '+' : ''}{tf.shap_value.toFixed(3)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* Clinical Interpretability Disclaimer */}
        <div className="p-4 rounded-2xl bg-navy-900/60 border border-navy-800 flex items-start gap-3 text-[11px] text-slate-400 leading-relaxed">
          <ShieldAlert className="w-5 h-5 text-medic-teal shrink-0 mt-0.5" />
          <p>
            {explanation?.clinical_disclaimer || 
              "Algorithmic interpretability aid only. SHAP values calculate mathematical feature attributions from the calibrated Random Forest ensemble and do not represent formal clinical diagnosis or replace human medical judgment."}
          </p>
        </div>

      </div>
    </div>
  );
};
