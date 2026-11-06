from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from .classification import PriorityLevel
from .retrieval import RelevanceStatus, RetrievedChunk

class SystemOutcome(str, Enum):
    SUFFICIENT_EVIDENCE = "SUFFICIENT_EVIDENCE"
    AMBIGUOUS_INPUT = "AMBIGUOUS_INPUT"
    LOW_RETRIEVAL_RELEVANCE = "LOW_RETRIEVAL_RELEVANCE"
    CONFLICTING_INFORMATION = "CONFLICTING_INFORMATION"
    CRITICAL_EMERGENCY = "CRITICAL_EMERGENCY"

class FirstAidStep(BaseModel):
    step_number: int
    action: str
    details: str
    caution: Optional[str] = None
    visual_guide_key: Optional[str] = Field(None, description="Key for visual animation/illustration: cpr, heimlich, pressure_bandage, burns_water, recovery_position")

class ConfidenceBreakdown(BaseModel):
    classifier_confidence: float = Field(..., ge=0.0, le=1.0, description="Calibrated ML classification confidence")
    retrieval_relevance_score: float = Field(..., ge=0.0, le=1.0, description="Semantic similarity & rerank metric of retrieved evidence")
    faithfulness_score: float = Field(..., ge=0.0, le=1.0, description="Response grounding faithfulness against verified evidence")
    relevance_status: RelevanceStatus

class EmergencyResponse(BaseModel):
    session_id: str
    outcome: SystemOutcome
    priority: PriorityLevel
    is_critical_bypass: bool = False
    immediate_emergency_warning: Optional[str] = None
    emergency_service_number: str = "911 / 112"
    summary: str
    first_aid_steps: List[FirstAidStep] = Field(default_factory=list)
    precautions: List[str] = Field(default_factory=list)
    what_to_avoid: List[str] = Field(default_factory=list)
    when_to_seek_immediate_care: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_breakdown: ConfidenceBreakdown
    clarification_questions: List[str] = Field(default_factory=list)
    disclaimer: str = (
        "CRITICAL DISCLAIMER: AegisAid is an automated AI decision-support tool, NOT a licensed medical professional "
        "or diagnostic service. In any serious, worsening, or life-threatening emergency, immediately call local emergency "
        "services (911/112/999/108) or go to the nearest emergency facility."
    )
    generated_at: str
    llm_provider: str = "Groq (openai/gpt-oss-120b)"
