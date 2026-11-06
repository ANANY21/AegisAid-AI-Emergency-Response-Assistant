export type PriorityLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';

export type SystemOutcome = 
  | 'SUFFICIENT_EVIDENCE' 
  | 'AMBIGUOUS_INPUT' 
  | 'LOW_RETRIEVAL_RELEVANCE' 
  | 'CONFLICTING_INFORMATION' 
  | 'CRITICAL_EMERGENCY';

export type RelevanceStatus = 'VALID' | 'INSUFFICIENT' | 'IRRELEVANT' | 'CONFLICTING';

export interface FirstAidStep {
  step_number: number;
  action: string;
  details: string;
  caution?: string | null;
  visual_guide_key?: 'cpr' | 'heimlich' | 'pressure_bandage' | 'burns_water' | 'recovery_position' | null;
}

export interface ConfidenceBreakdown {
  classifier_confidence: number;
  retrieval_relevance_score: number;
  faithfulness_score: number;
  relevance_status: RelevanceStatus;
}

export interface SourceReference {
  source_name: string;
  document_title: string;
  section: string;
  source_url?: string | null;
  publication_date?: string | null;
  relevance_score: number;
  document_id?: string;
  publishing_organization?: string;
  version?: string;
  last_reviewed_date?: string | null;
  review_status?: string;
  document_type?: string;
  page_number?: string | null;
}

export interface CitationDetail {
  citation_index: number;
  citation_tag: string;
  document_id: string;
  document_title: string;
  publishing_organization: string;
  section: string;
  page_number?: string | null;
  source_url?: string | null;
  review_status: string;
  document_type: string;
  relevance_score: number;
  claim_support_score: number;
  is_verified_support: boolean;
  cited_excerpt: string;
}

export interface EvidenceVerificationSummary {
  total_citations: number;
  supported_claims_count: number;
  unsupported_claims_count: number;
  mean_grounding_score: number;
  outdated_sources_flagged: string[];
  conflicting_sources_flagged: string[];
  verification_passed: boolean;
}

export interface SHAPFeatureContribution {
  rank: number;
  raw_feature_name: string;
  feature_name: string;
  shap_value: number;
  feature_value: number;
  impact: 'positive' | 'negative';
  description: string;
}

export interface SHAPMulticlassClassDetail {
  base_value: number;
  calibrated_probability: number;
  top_features: Array<{ feature_name: string; shap_value: number; impact: string }>;
}

export interface SHAPExplanationResponse {
  session_id?: string;
  predicted_class: PriorityLevel;
  focus_class: PriorityLevel;
  model_version: string;
  base_value: number;
  model_output_value: number;
  class_probabilities: Record<string, number>;
  feature_contributions: SHAPFeatureContribution[];
  top_positive_features: SHAPFeatureContribution[];
  top_negative_features: SHAPFeatureContribution[];
  multiclass_breakdown: Record<string, SHAPMulticlassClassDetail>;
  threshold_applied: number;
  clinical_disclaimer: string;
  timestamp: string;
  status: string;
}

export interface GlobalSHAPFeature {
  rank: number;
  feature_name: string;
  mean_abs_shap: number;
  description: string;
  class_mean_impact: Record<string, number>;
}

export interface GlobalSHAPResponse {
  model_version: string;
  sample_count: number;
  global_top_features: GlobalSHAPFeature[];
  class_base_values: Record<string, number>;
  generated_at: string;
  reviewer_role: string;
  methodology: string;
  status?: string;
}

export interface MedicalSourceProvenance {
  document_id: string;
  file_name?: string;
  document_title: string;
  publishing_organization: string;
  source_url?: string | null;
  version: string;
  publication_date?: string | null;
  last_reviewed_date?: string | null;
  review_status: 'Verified' | 'Pending Review' | 'Outdated' | 'Unavailable';
  document_type: string;
  category: string;
  contraindications: string[];
  section_count: number;
  sections: any[];
  is_stale: boolean;
  freshness_days?: number | null;
}

export interface SourceRegistryMetrics {
  total_sources: number;
  verified_count: number;
  pending_review_count: number;
  outdated_count: number;
  unavailable_count: number;
  verification_rate_pct: number;
  total_chunks_indexed: number;
  stale_guidelines_count: number;
  all_sources_active: boolean;
}

export interface EmergencyResponse {
  session_id: string;
  outcome: SystemOutcome;
  priority: PriorityLevel;
  is_critical_bypass: boolean;
  immediate_emergency_warning?: string | null;
  emergency_service_number: string;
  summary: string;
  first_aid_steps: FirstAidStep[];
  precautions: string[];
  what_to_avoid: string[];
  when_to_seek_immediate_care: string;
  sources: SourceReference[];
  citations?: CitationDetail[];
  unsupported_claims?: string[];
  evidence_verification?: EvidenceVerificationSummary | null;
  shap_summary?: SHAPExplanationResponse | null;
  confidence_breakdown: ConfidenceBreakdown;
  clarification_questions: string[];
  disclaimer: string;
  generated_at: string;
  llm_provider: string;
}

export interface MedicalFacility {
  id: string;
  name: string;
  facility_type: string;
  address: string;
  distance_km: number;
  phone?: string | null;
  has_emergency_room: boolean;
  latitude: number;
  longitude: number;
  directions_url: string;
  real_time_status_note: string;
}

export interface HospitalSearchResponse {
  facilities: MedicalFacility[];
  search_center_lat: number;
  search_center_lng: number;
  count: number;
  data_source: string;
  disclaimer: string;
}

export interface HistorySession {
  session_id: string;
  created_at: string;
  priority: PriorityLevel;
  outcome: SystemOutcome;
  is_critical_bypass: boolean;
  raw_description: string;
  summary: string;
  extracted_symptoms: string[];
}

export interface BenchmarkReport {
  timestamp: string;
  classification_metrics: {
    accuracy: number;
    precision_macro: number;
    recall_macro: number;
    f1_macro: number;
    critical_class_recall: number;
    confusion_matrix: number[][];
    classes: string[];
    sample_count: number;
    model_version?: string;
    evaluation_date?: string;
    validation_methodology?: string;
    decision_threshold_tau_crit?: number;
    class_distribution?: Record<string, number>;
    baseline_comparison?: {
      model_version: string;
      sample_count: number;
      critical_recall: number;
      critical_precision: number;
      critical_false_negatives: number;
      overall_accuracy: number;
      macro_f1: number;
      confusion_matrix?: number[][];
    };
    cross_validation_5fold?: {
      mean_critical_recall: number;
      std_critical_recall: number;
      mean_critical_precision: number;
      std_critical_precision: number;
      mean_critical_f1: number;
      mean_overall_accuracy: number;
      total_aggregated_confusion_matrix: number[][];
      total_critical_false_negatives: number;
    };
    untouched_test_set_evaluation?: {
      test_sample_count: number;
      critical_class_recall: number;
      critical_class_precision: number;
      critical_class_f1: number;
      critical_class_specificity: number;
      critical_false_negatives: number;
      overall_accuracy: number;
      macro_precision: number;
      macro_recall: number;
      macro_f1: number;
      confusion_matrix: number[][];
    };
  };
  retrieval_metrics: {
    precision_at_k: number;
    recall_at_k: number;
    mrr: number;
    ndcg_at_k: number;
    relevance_threshold_rejection_rate: number;
    evaluation_queries_count: number;
  };
  safety_escalation_metrics: {
    total_incidents_processed: number;
    critical_bypass_count: number;
    low_relevance_escalations: number;
    ambiguous_input_clarifications: number;
    conflicting_information_escalations: number;
    grounded_responses_count: number;
    faithfulness_mean_score: number;
  };
  knowledge_base_stats: {
    indexed_chunks: number;
    total_documents: number;
    categories: string[];
    active_sources: string[];
  };
}
