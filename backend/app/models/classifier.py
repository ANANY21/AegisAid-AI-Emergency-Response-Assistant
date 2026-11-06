import numpy as np
import joblib
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import re

from ..schemas.classification import PriorityLevel, ClassificationResult
from ..core.logging import logger

CRITICAL_KEYWORDS = {
    "cardiac arrest", "not breathing", "unresponsive", "stopped breathing",
    "choking", "turning blue", "cyanosis", "arterial bleeding", "spurting blood",
    "stab wound", "gunshot", "unconscious", "anaphylaxis", "severe allergic",
    "stridor", "overdose", "pinpoint pupils", "heatstroke", "crushing chest",
    "facial droop", "slurred speech", "be fast", "head trauma", "pulseless",
    "decerebrate", "skull depression", "sucking chest", "drowning"
}

HIGH_KEYWORDS = {
    "deep burn", "scald", "broken bone", "compound fracture", "seizure",
    "convulsion", "severe pain", "bleeding profusely", "chemical burn",
    "worst headache", "diabetic ketoacidosis", "concussion", "vomiting blood",
    "testicular torsion", "preeclampsia", "melena"
}

class TriageClassifier:
    def __init__(self, model_path: Path = None):
        self.model_path = model_path
        self.pipeline = None
        self.classes_ = ["LOW", "MODERATE", "HIGH", "CRITICAL"]
        self.model_version = "rf-cost-calibrated-triage-v2.0"
        self.tau_crit = 0.30  # Safety-calibrated critical decision threshold
        
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
            self.tau_crit = loaded_data.get("tau_crit", getattr(self, "tau_crit", 0.30))
            logger.info(f"Loaded trained triage classifier ({self.model_version}) from {path} | tau_crit={self.tau_crit}")
        except Exception as e:
            logger.error(f"Failed to load classifier from {path}: {e}")
            self.pipeline = None

    def save(self, path: Path, metadata: Dict[str, Any] = None):
        data = {
            "pipeline": self.pipeline,
            "classes": self.classes_,
            "model_version": self.model_version,
            "tau_crit": self.tau_crit,
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
        has_chest_pain: int = 0,
        has_stroke_symptoms: Optional[int] = None,
        has_anaphylaxis_symptoms: Optional[int] = None,
        has_severe_trauma: Optional[int] = None,
        has_altered_mental_status: Optional[int] = None
    ) -> ClassificationResult:
        """
        Predicts incident priority with calibrated probabilities, safety thresholding,
        and rule-based safety escalation.
        Note: The ML classifier provides decision support, not a definitive medical diagnosis.
        """
        text_lower = text.lower()
        decision_factors = []
        
        # 1. Independent Safety-First Detection of Clinical Red Flags
        is_crit_rule = False
        for kw in CRITICAL_KEYWORDS:
            if kw in text_lower:
                is_crit_rule = True
                decision_factors.append(f"Critical keyword detected: '{kw}'")
                break
        
        # Automatic feature derivation from clinical NLP if not explicitly passed
        if has_stroke_symptoms is None:
            has_stroke_symptoms = int(bool(re.search(r"facial droop|slurred speech|arm weakness|face droop|hemiparesis|stroke|be fast", text_lower)))
        if has_anaphylaxis_symptoms is None:
            has_anaphylaxis_symptoms = int(bool(re.search(r"anaphylac|swollen tongue|throat closing|stridor|lips turning blue|peanut exposure|bee sting", text_lower)))
        if has_severe_trauma is None:
            has_severe_trauma = int(bool(re.search(r"skull depression|stab wound|gunshot|sucking chest|motor vehicle crash|head trauma|fell 12 feet|amputation", text_lower)))
        if has_altered_mental_status is None:
            has_altered_mental_status = int(bool(re.search(r"delirium|unresponsive|ceased sweating|pinpoint pupils|heatstroke|disoriented|confus|letharg", text_lower)))

        if has_unconsciousness:
            decision_factors.append("Clinical indicator: Loss of consciousness")
        if has_breathing_difficulty:
            decision_factors.append("Clinical indicator: Severe respiratory distress")
        if has_severe_bleeding:
            decision_factors.append("Clinical indicator: Uncontrolled / arterial hemorrhage")
        if has_chest_pain:
            decision_factors.append("Clinical indicator: Crushing substernal chest pain")
        if has_stroke_symptoms:
            decision_factors.append("Clinical indicator: Acute neurological deficit (BE-FAST signs)")
        if has_anaphylaxis_symptoms:
            decision_factors.append("Clinical indicator: Severe airway compromise / anaphylaxis")
        if has_severe_trauma:
            decision_factors.append("Clinical indicator: High-energy trauma / penetrating injury")
        if has_altered_mental_status:
            decision_factors.append("Clinical indicator: Altered mental status / extreme hyperthermia")

        # 2. ML Probability Estimation
        if self.pipeline:
            # Check pipeline features
            age_val = float(age) if age is not None else 35.0
            dur_val = float(duration_minutes) if duration_minutes is not None else 30.0
            
            row_dict = {
                "text": text,
                "age_norm": age_val / 100.0,
                "duration_log": np.log1p(dur_val),
                "has_breathing_difficulty": int(has_breathing_difficulty),
                "has_unconsciousness": int(has_unconsciousness),
                "has_severe_bleeding": int(has_severe_bleeding),
                "has_chest_pain": int(has_chest_pain),
                "has_stroke_symptoms": int(has_stroke_symptoms),
                "has_anaphylaxis_symptoms": int(has_anaphylaxis_symptoms),
                "has_severe_trauma": int(has_severe_trauma),
                "has_altered_mental_status": int(has_altered_mental_status),
                # Legacy columns for compatibility
                "age": age_val,
                "duration_minutes": dur_val
            }
            row = pd.DataFrame([row_dict])
            
            probs = self.pipeline.predict_proba(row)[0]
            pipe_classes = list(self.pipeline.classes_)
            class_probs = {cls_name: float(probs[i]) for i, cls_name in enumerate(pipe_classes)}
            
            crit_prob = class_probs.get("CRITICAL", 0.0)
            high_prob = class_probs.get("HIGH", 0.0)

            # 3. Decision Threshold Optimization (Safety-Calibrated Policy)
            # If P(CRITICAL) >= tau_crit, assign CRITICAL
            if crit_prob >= self.tau_crit:
                predicted_priority = "CRITICAL"
                confidence = crit_prob
                decision_factors.append(f"Safety-Calibrated Policy: P(CRITICAL)={crit_prob:.3f} exceeds threshold ({self.tau_crit:.2f})")
            # Borderline High vs Critical escalation
            elif (crit_prob + high_prob >= 0.60) and abs(crit_prob - high_prob) <= 0.12:
                predicted_priority = "CRITICAL"
                confidence = max(crit_prob, high_prob)
                decision_factors.append(f"Safety Escalation: Borderline urgency between High ({high_prob:.2f}) and Critical ({crit_prob:.2f}) - escalated to CRITICAL to prevent under-triage")
            else:
                # Argmax over remaining non-critical classes
                non_crit = [(cls_name, class_probs[cls_name]) for cls_name in pipe_classes if cls_name != "CRITICAL"]
                best_cls, best_p = max(non_crit, key=lambda x: x[1])
                predicted_priority = best_cls
                confidence = best_p
        else:
            # Fallback heuristic classifier
            class_probs = {"LOW": 0.25, "MODERATE": 0.25, "HIGH": 0.25, "CRITICAL": 0.25}
            if is_crit_rule or has_unconsciousness or has_breathing_difficulty or has_severe_bleeding or has_stroke_symptoms:
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

        # 4. SAFETY OVERRIDE: Never allow a false negative on explicit life-threatening indicators!
        life_threatening_trigger = (
            is_crit_rule or has_unconsciousness or has_stroke_symptoms or
            (has_breathing_difficulty and any(w in text_lower for w in ["blue", "gasp", "cyanosis", "silent", "stridor"])) or
            (has_severe_bleeding and any(w in text_lower for w in ["spurting", "arterial", "not stopping", "pumping"]))
        )

        if life_threatening_trigger and predicted_priority != "CRITICAL":
            logger.warning("Safety rule override: Clinical signs require priority escalation to CRITICAL")
            predicted_priority = "CRITICAL"
            confidence = max(confidence, 0.95)
            class_probs["CRITICAL"] = max(class_probs.get("CRITICAL", 0.0), 0.92)
            decision_factors.append("Safety Guardrail: Priority escalated to CRITICAL due to explicit life-threatening indicators")

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
