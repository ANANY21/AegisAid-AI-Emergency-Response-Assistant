from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from ..schemas.classification import ClassificationResult
from ..models.classifier import TriageClassifier
from ..config import settings

router = APIRouter(prefix="/api/classification", tags=["Classification"])
classifier = TriageClassifier(settings.MODELS_DIR / "incident_classifier.joblib")

class ClassifyRequest(BaseModel):
    text: str
    age: Optional[float] = 35.0
    duration_minutes: Optional[float] = 30.0
    has_breathing_difficulty: Optional[int] = 0
    has_unconsciousness: Optional[int] = 0
    has_severe_bleeding: Optional[int] = 0
    has_chest_pain: Optional[int] = 0

@router.post("/predict", response_model=ClassificationResult)
def predict_priority(req: ClassifyRequest):
    return classifier.predict(
        text=req.text,
        age=req.age,
        duration_minutes=req.duration_minutes,
        has_breathing_difficulty=req.has_breathing_difficulty,
        has_unconsciousness=req.has_unconsciousness,
        has_severe_bleeding=req.has_severe_bleeding,
        has_chest_pain=req.has_chest_pain
    )
