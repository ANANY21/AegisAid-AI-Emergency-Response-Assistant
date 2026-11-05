from pydantic import BaseModel, Field
from typing import Dict, List, Any

class ClassificationMetrics(BaseModel):
    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    critical_class_recall: float = Field(..., description="Crucial safety metric: recall specifically for CRITICAL cases")
    confusion_matrix: List[List[int]]
    classes: List[str]
    sample_count: int

class RetrievalMetrics(BaseModel):
    precision_at_k: float
    recall_at_k: float
    mrr: float
    ndcg_at_k: float
    relevance_threshold_rejection_rate: float
    evaluation_queries_count: int

class SafetyEscalationMetrics(BaseModel):
    total_incidents_processed: int
    critical_bypass_count: int
    low_relevance_escalations: int
    ambiguous_input_clarifications: int
    conflicting_information_escalations: int
    grounded_responses_count: int
    faithfulness_mean_score: float

class SystemBenchmarkReport(BaseModel):
    timestamp: str
    classification_metrics: ClassificationMetrics
    retrieval_metrics: RetrievalMetrics
    safety_escalation_metrics: SafetyEscalationMetrics
    knowledge_base_stats: Dict[str, Any]
