from pydantic import BaseModel, Field
from typing import Dict, List
from enum import Enum

class PriorityLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ClassificationResult(BaseModel):
    priority: PriorityLevel = Field(..., description="Triage priority level")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Calibrated classifier confidence probability")
    class_probabilities: Dict[str, float] = Field(..., description="Probabilities across LOW, MODERATE, HIGH, CRITICAL")
    decision_factors: List[str] = Field(default_factory=list, description="Extracted features triggering this priority")
    is_critical: bool = Field(default=False, description="Whether priority is CRITICAL triggering bypass")
    model_version: str = Field(default="incident-rf-calibrated-v1", description="Model architecture used")
    requires_emergency_bypass: bool = Field(default=False, description="Flag indicating emergency services dispatch is needed immediately")
