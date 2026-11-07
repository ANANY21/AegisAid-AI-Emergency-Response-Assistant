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
  nearby_facilities?: MedicalFacility[];
  nearest_hospital_names?: string[];
  user_location_label?: string | null;
  disclaimer: string;
  generated_at: string;
  llm_provider: string;
}

export interface MedicalFacility {
  id: string;
  place_id?: string | null;
  name: string;
  facility_type: string;
  address: string;
  locality?: string | null;
  latitude: number;
  longitude: number;
  road_distance_km?: number | null;
  straight_line_distance_km: number;
  distance_km: number;
  driving_duration_mins?: number | null;
  driving_duration_text?: string | null;
  phone?: string | null;
  website?: string | null;
  rating?: number | null;
  user_ratings_total?: number | null;
  is_open_now?: boolean | null;
  opening_hours_text?: string | null;
  has_emergency_room: boolean;
  directions_url: string;
  osm_directions_url?: string | null;
  place_url?: string | null;
  real_time_status_note: string;
  data_provider: string;
  last_updated: string;
}

export interface HospitalDiscoveryDiagnostics {
  timestamp: string;
  active_provider: string;
  google_places_configured: boolean;
  google_places_masked_key?: string | null;
  google_places_http_status?: number | null;
  google_places_error?: string | null;
  osm_fallback_used: boolean;
  osm_http_status?: number | null;
  search_radius_km: number;
  initial_radius_km: number;
  radius_expanded: boolean;
  raw_result_count: number;
  filtered_result_count: number;
  duration_ms: number;
  status_code: 'OK' | 'ZERO_RESULTS' | 'CONFIG_REQUIRED' | 'ERROR';
  actionable_guidance?: string | null;
}

export interface HospitalSearchResponse {
  facilities: MedicalFacility[];
  search_center_lat: number;
  search_center_lng: number;
  search_locality?: string | null;
  search_radius_km: number;
  count: number;
  data_provider: string;
  is_live_provider: boolean;
  provider_attribution: string;
  google_maps_search_url: string;
  osm_search_url?: string | null;
  osm_api_key_configured?: boolean;
  emergency_helpline: string;
  diagnostics?: HospitalDiscoveryDiagnostics | null;
  disclaimer: string;
}

export interface ReverseGeocodeResponse {
  formatted_address: string;
  locality: string;
  sublocality?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  postal_code?: string | null;
  data_provider: string;
}

export interface PlaceDetailsResponse {
  place_id: string;
  name: string;
  formatted_address: string;
  formatted_phone_number?: string | null;
  international_phone_number?: string | null;
  website?: string | null;
  rating?: number | null;
  user_ratings_total?: number | null;
  opening_hours?: string[] | null;
  is_open_now?: boolean | null;
  google_maps_url?: string | null;
  types: string[];
}

export interface RouteDirectionsResponse {
  origin_lat: number;
  origin_lng: number;
  destination_lat: number;
  destination_lng: number;
  road_distance_km: number;
  driving_duration_mins: number;
  driving_duration_text: string;
  navigation_url: string;
  route_summary?: string | null;
  steps: string[];
  data_provider: string;
}

export interface ChennaiPreset {
  name: string;
  locality: string;
  latitude: number;
  longitude: number;
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
