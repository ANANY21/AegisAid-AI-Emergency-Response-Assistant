from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from ..services.shap_service import shap_service
from ..core.logging import logger

router = APIRouter(prefix="", tags=["Explainable AI (SHAP)"])

class ExplainabilityRequest(BaseModel):
    text: str = Field(..., description="Emergency incident narrative")
    age: Optional[float] = Field(35.0, description="Patient age in years")
    duration_minutes: Optional[float] = Field(30.0, description="Symptom onset duration in minutes")
    has_breathing_difficulty: Optional[int] = Field(0, description="1 if breathing difficulty present")
    has_unconsciousness: Optional[int] = Field(0, description="1 if loss of consciousness present")
    has_severe_bleeding: Optional[int] = Field(0, description="1 if severe/arterial bleeding present")
    has_chest_pain: Optional[int] = Field(0, description="1 if chest pain present")
    has_stroke_symptoms: Optional[int] = Field(0, description="1 if stroke symptoms present")
    has_anaphylaxis_symptoms: Optional[int] = Field(0, description="1 if anaphylaxis symptoms present")
    has_severe_trauma: Optional[int] = Field(0, description="1 if severe trauma present")
    has_altered_mental_status: Optional[int] = Field(0, description="1 if altered mental status present")
    target_class: Optional[str] = Field(None, description="Optional target class for comparative waterfall: LOW, MODERATE, HIGH, CRITICAL")

@router.post("/api/v1/explainability/predict")
@router.post("/api/explainability/predict")
def explain_incident_prediction(req: ExplainabilityRequest):
    """
    Computes real-time SHAP feature attribution and waterfall decomposition for
    an emergency incident classification.
    """
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Emergency narrative text cannot be empty.")

    try:
        explanation = shap_service.explain_prediction(
            text=req.text,
            age=req.age,
            duration_minutes=req.duration_minutes,
            has_breathing_difficulty=req.has_breathing_difficulty or 0,
            has_unconsciousness=req.has_unconsciousness or 0,
            has_severe_bleeding=req.has_severe_bleeding or 0,
            has_chest_pain=req.has_chest_pain or 0,
            has_stroke_symptoms=req.has_stroke_symptoms or 0,
            has_anaphylaxis_symptoms=req.has_anaphylaxis_symptoms or 0,
            has_severe_trauma=req.has_severe_trauma or 0,
            has_altered_mental_status=req.has_altered_mental_status or 0,
            target_class=req.target_class
        )
        if explanation.get("status") == "unavailable":
            raise HTTPException(status_code=503, detail=explanation.get("error"))
        return explanation
    except Exception as e:
        logger.error(f"Error in explain_incident_prediction API: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate SHAP explanation: {str(e)}")

@router.get("/api/v1/explainability/global")
@router.get("/api/explainability/global")
def get_global_model_explanations():
    """
    Returns global SHAP feature importance summary across the clinical evaluation cohort.
    Restricted to authorized clinical and algorithmic reviewers.
    """
    try:
        global_summary = shap_service.get_global_feature_importance()
        if global_summary.get("status") == "unavailable":
            raise HTTPException(status_code=503, detail=global_summary.get("error"))
        return global_summary
    except Exception as e:
        logger.error(f"Error in get_global_model_explanations API: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve global SHAP explanation: {str(e)}")
