import numpy as np
import joblib
from pathlib import Path
from typing import Dict, Any, List, Tuple
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
from ..schemas.classification import PriorityLevel, ClassificationResult
from ..core.logging import logger

CRITICAL_KEYWORDS = {
    "cardiac arrest", "not breathing", "unresponsive", "stopped breathing",
    "choking", "turning blue", "cyanosis", "arterial bleeding", "spurting blood",
    "stab wound", "gunshot", "unconscious", "anaphylaxis", "severe allergic",
    "stridor", "overdose", "pinpoint pupils", "heatstroke", "crushing chest",
    "facial droop", "slurred speech", "be fast", "head trauma"
}

HIGH_KEYWORDS = {
    "deep burn", "scald", "broken bone", "compound fracture", "seizure",
    "convulsion", "severe pain", "bleeding profusely", "chemical burn",
    "worst headache", "diabetic ketoacidosis", "concussion", "vomiting blood"
}

class TriageClassifier:
    def __init__(self, model_path: Path = None):
        self.model_path = model_path
        self.pipeline = None
        self.classes_ = ["LOW", "MODERATE", "HIGH", "CRITICAL"]
        self.model_version = "rf-calibrated-triage-v1.0"
        
        if model_path and model_path.exists():
            self.load(model_path)
        else:
            logger.info("Classifier model file not found yet; will initialize baseline model")

    def load(self, path: Path):
        try:
            loaded_data = joblib.load(path)
            self.pipeline = loaded_data.get("pipeline")
            self.classes_ = loaded_data.get("classes", self.classes_)
            self.model_version = loaded_data.get("model_version", self.model_version)
            logger.info(f"Loaded trained triage classifier from {path}")
        except Exception as e:
            logger.error(f"Failed to load classifier from {path}: {e}")
            self.pipeline = None

    def save(self, path: Path, metadata: Dict[str, Any] = None):
        data = {
            "pipeline": self.pipeline,
            "classes": self.classes_,
            "model_version": self.model_version,
            "metadata": metadata or {}
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(data, path)
        logger.info(f"Saved classifier model to {path}")

    def predict(
        self,
        text: str,
        age: float = 35.0,
        duration_minutes: float = 30.0,
        has_breathing_difficulty: int = 0,
        has_unconsciousness: int = 0,
        has_severe_bleeding: int = 0,
        has_chest_pain: int = 0
    ) -> ClassificationResult:
        """
        Predicts incident priority with calibrated probabilities and rule-based safety enforcement.
        Note: The ML classifier provides decision support, not a definitive medical diagnosis.
        """
        text_lower = text.lower()
        decision_factors = []
        
        # Clinical red-flag triggers for safety enforcement
        is_crit_rule = False
        for kw in CRITICAL_KEYWORDS:
            if kw in text_lower:
                is_crit_rule = True
                decision_factors.append(f"Critical keyword detected: '{kw}'")
        
        if has_unconsciousness or has_breathing_difficulty or has_severe_bleeding or has_chest_pain:
            if has_unconsciousness:
                decision_factors.append("Clinical indicator: Loss of consciousness")
            if has_breathing_difficulty:
                decision_factors.append("Clinical indicator: Severe breathing difficulty")
            if has_severe_bleeding:
                decision_factors.append("Clinical indicator: Uncontrolled / severe bleeding")
            if has_chest_pain:
                decision_factors.append("Clinical indicator: Severe substernal chest pain")
                
        # If pipeline is loaded, predict using calibrated probabilities
        if self.pipeline:
            import pandas as pd
            row = pd.DataFrame([{
                "text": text,
                "age": age if age is not None else 35.0,
                "duration_minutes": duration_minutes if duration_minutes is not None else 30.0,
                "has_breathing_difficulty": int(has_breathing_difficulty),
                "has_unconsciousness": int(has_unconsciousness),
                "has_severe_bleeding": int(has_severe_bleeding),
                "has_chest_pain": int(has_chest_pain)
            }])
            
            probs = self.pipeline.predict_proba(row)[0]
            class_probs = {cls_name: float(probs[i]) for i, cls_name in enumerate(self.pipeline.classes_)}
            
            best_idx = int(np.argmax(probs))
            predicted_priority = str(self.pipeline.classes_[best_idx])
            confidence = float(probs[best_idx])
        else:
            # Fallback heuristic classifier if model not yet trained on disk
            class_probs = {"LOW": 0.25, "MODERATE": 0.25, "HIGH": 0.25, "CRITICAL": 0.25}
            if is_crit_rule or has_unconsciousness or has_breathing_difficulty or has_severe_bleeding:
                predicted_priority = "CRITICAL"
                confidence = 0.94
                class_probs = {"LOW": 0.01, "MODERATE": 0.02, "HIGH": 0.07, "CRITICAL": 0.90}
            elif any(hw in text_lower for hw in HIGH_KEYWORDS):
                predicted_priority = "HIGH"
                confidence = 0.85
                class_probs = {"LOW": 0.05, "MODERATE": 0.15, "HIGH": 0.75, "CRITICAL": 0.05}
            elif any(w in text_lower for w in ["sprain", "cut", "fever", "rash", "vomit", "migraine"]):
                predicted_priority = "MODERATE"
                confidence = 0.78
                class_probs = {"LOW": 0.10, "MODERATE": 0.75, "HIGH": 0.12, "CRITICAL": 0.03}
            else:
                predicted_priority = "LOW"
                confidence = 0.70
                class_probs = {"LOW": 0.70, "MODERATE": 0.20, "HIGH": 0.08, "CRITICAL": 0.02}

        # SAFETY OVERRIDE: Never allow a false negative on explicit life-threatening indicators!
        if (is_crit_rule or has_unconsciousness) and predicted_priority != "CRITICAL":
            logger.warning("Safety rule override: Clinical signs require priority escalation to CRITICAL")
            predicted_priority = "CRITICAL"
            confidence = max(confidence, 0.92)
            class_probs["CRITICAL"] = max(class_probs.get("CRITICAL", 0.0), 0.90)
            decision_factors.append("Safety Guardrail: Priority escalated to CRITICAL due to life-threatening signs")

        priority_enum = PriorityLevel(predicted_priority)
        is_critical = (priority_enum == PriorityLevel.CRITICAL)

        return ClassificationResult(
            priority=priority_enum,
            confidence=round(confidence, 3),
            class_probabilities={k: round(v, 3) for k, v in class_probs.items()},
            decision_factors=decision_factors or [f"Statistical prediction ({predicted_priority}) based on clinical features"],
            is_critical=is_critical,
            model_version=self.model_version,
            requires_emergency_bypass=is_critical
        )
