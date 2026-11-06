import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import joblib
import shap
from datetime import datetime

from ..config import settings
from ..core.logging import logger

FEATURE_DISPLAY_MAP = {
    "num__has_breathing_difficulty": "Clinical: Respiratory Distress / Apnea",
    "num__has_unconsciousness": "Clinical: Loss of Consciousness / Coma",
    "num__has_severe_bleeding": "Clinical: Arterial / Severe Hemorrhage",
    "num__has_chest_pain": "Clinical: Crushing Substernal Chest Pain",
    "num__has_stroke_symptoms": "Clinical: Acute Neurological Deficit (BE-FAST)",
    "num__has_anaphylaxis_symptoms": "Clinical: Airway Angioedema / Stridor",
    "num__has_severe_trauma": "Clinical: High-Velocity / Penetrating Trauma",
    "num__has_altered_mental_status": "Clinical: Altered Mental Status / Delirium",
    "num__duration_log": "Timeline: Symptom Onset Duration",
    "num__age_norm": "Demographic: Patient Age"
}

FEATURE_DESCRIPTIONS = {
    "Clinical: Respiratory Distress / Apnea": "Severe shortness of breath, gasping, stridor, or complete respiratory arrest.",
    "Clinical: Loss of Consciousness / Coma": "Unresponsiveness to verbal or physical stimuli, syncope, or Glasgow Coma Scale depression.",
    "Clinical: Arterial / Severe Hemorrhage": "High-volume, pulsatile, or continuous bleeding not controlled by basic first aid.",
    "Clinical: Crushing Substernal Chest Pain": "Severe retrosternal pressure, tightness, or pain radiating to left arm/jaw.",
    "Clinical: Acute Neurological Deficit (BE-FAST)": "Sudden unilateral facial drooping, arm weakness, or slurred dysarthric speech.",
    "Clinical: Airway Angioedema / Stridor": "Rapid swelling of the tongue, lips, or pharynx with inspiratory crowing sounds.",
    "Clinical: High-Velocity / Penetrating Trauma": "Depressed skull fracture, thoracic stab wound, ejection from vehicle, or high fall.",
    "Clinical: Altered Mental Status / Delirium": "Disorientation, severe confusion, pinpoint pupils, or core temperature collapse.",
    "Timeline: Symptom Onset Duration": "Elapsed time since initial emergency presentation.",
    "Demographic: Patient Age": "Patient age in years, normalized for clinical baseline assessment."
}

class SHAPExplanationService:
    def __init__(self, model_path: Path = None):
        self.model_path = model_path or (settings.MODELS_DIR / "incident_classifier.joblib")
        self.pipeline = None
        self.classes: List[str] = ["LOW", "MODERATE", "HIGH", "CRITICAL"]
        self.model_version: str = "rf-cost-calibrated-triage-v2.0"
        self.tau_crit: float = 0.20
        self.explainers: List[shap.TreeExplainer] = []
        self.feature_names: List[str] = []
        self.global_cache: Optional[Dict[str, Any]] = None
        self._load_and_initialize()

    def _load_and_initialize(self):
        if not self.model_path.exists():
            logger.warning(f"Model path {self.model_path} does not exist for SHAP initialization.")
            return

        try:
            model_data = joblib.load(self.model_path)
            self.pipeline = model_data["pipeline"]
            self.classes = model_data.get("classes", self.classes)
            self.model_version = model_data.get("model_version", self.model_version)
            self.tau_crit = model_data.get("tau_crit", 0.20)

            prep = self.pipeline.named_steps["preprocessor"]
            cal_clf = self.pipeline.named_steps["classifier"]
            self.feature_names = list(prep.get_feature_names_out())

            # Initialize TreeExplainers for each base estimator in the calibrated ensemble
            self.explainers = []
            if hasattr(cal_clf, "calibrated_classifiers_"):
                for cc in cal_clf.calibrated_classifiers_:
                    self.explainers.append(shap.TreeExplainer(cc.estimator))
            elif hasattr(cal_clf, "estimator"):
                self.explainers.append(shap.TreeExplainer(cal_clf.estimator))

            logger.info(f"Initialized SHAP explanation service with {len(self.explainers)} TreeExplainers across {len(self.feature_names)} features.")
        except Exception as e:
            logger.error(f"Failed to initialize SHAP TreeExplainer: {e}")

    def _format_feature_name(self, raw_name: str) -> str:
        if raw_name in FEATURE_DISPLAY_MAP:
            return FEATURE_DISPLAY_MAP[raw_name]
        if raw_name.startswith("text__"):
            token = raw_name.replace("text__", "")
            return f"Keyword: \"{token}\""
        if raw_name.startswith("num__"):
            token = raw_name.replace("num__", "").replace("_", " ")
            return f"Clinical: {token.title()}"
        return raw_name

    def explain_prediction(
        self,
        text: str,
        age: float = 35.0,
        duration_minutes: float = 30.0,
        has_breathing_difficulty: int = 0,
        has_unconsciousness: int = 0,
        has_severe_bleeding: int = 0,
        has_chest_pain: int = 0,
        has_stroke_symptoms: int = 0,
        has_anaphylaxis_symptoms: int = 0,
        has_severe_trauma: int = 0,
        has_altered_mental_status: int = 0,
        target_class: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Computes exact, calibrated multiclass SHAP values and waterfall decomposition
        for an individual patient incident prediction.
        """
        if not self.pipeline or not self.explainers:
            self._load_and_initialize()
            if not self.pipeline:
                return {
                    "status": "unavailable",
                    "error": "SHAP model pipeline not initialized."
                }

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
            "age": age_val,
            "duration_minutes": dur_val
        }
        df_row = pd.DataFrame([row_dict])

        # 1. Pipeline Prediction & Calibrated Probabilities
        prep = self.pipeline.named_steps["preprocessor"]
        X_dense = prep.transform(df_row)
        if hasattr(X_dense, "toarray"):
            X_dense = X_dense.toarray()

        probs = self.pipeline.predict_proba(df_row)[0]
        pipe_classes = list(self.pipeline.classes_)
        class_probs = {cls_name: float(probs[i]) for i, cls_name in enumerate(pipe_classes)}

        crit_prob = class_probs.get("CRITICAL", 0.0)
        high_prob = class_probs.get("HIGH", 0.0)

        # Decision threshold policy
        if crit_prob >= self.tau_crit:
            predicted_class = "CRITICAL"
        elif (crit_prob + high_prob >= 0.60) and abs(crit_prob - high_prob) <= 0.12:
            predicted_class = "CRITICAL"
        else:
            non_crit = [(cls_name, class_probs[cls_name]) for cls_name in pipe_classes if cls_name != "CRITICAL"]
            predicted_class = max(non_crit, key=lambda x: x[1])[0]

        # Selected class for detailed waterfall (default to predicted_class)
        focus_class = target_class if (target_class and target_class in pipe_classes) else predicted_class
        focus_c_idx = pipe_classes.index(focus_class)

        # 2. Compute Ensemble SHAP Values
        n_features = len(self.feature_names)
        shap_sum = np.zeros((1, n_features, len(pipe_classes)))
        expected_sum = np.zeros(len(pipe_classes))

        for exp in self.explainers:
            vals = exp.shap_values(X_dense)
            shap_sum += vals
            expected_sum += exp.expected_value

        shap_avg = shap_sum / len(self.explainers)
        expected_avg = expected_sum / len(self.explainers)

        class_shap_values = shap_avg[0, :, focus_c_idx]
        base_value = float(expected_avg[focus_c_idx])
        model_output_value = float(base_value + np.sum(class_shap_values))

        # 3. Rank Top Contributing Features (Positive & Negative)
        # Select top features by absolute magnitude
        top_indices = np.argsort(np.abs(class_shap_values))[::-1]
        
        feature_contributions = []
        top_positive_features = []
        top_negative_features = []

        for rank, idx in enumerate(top_indices[:15]):
            val = float(class_shap_values[idx])
            raw_name = self.feature_names[idx]
            display_name = self._format_feature_name(raw_name)
            
            # Value in original input
            feat_val = float(X_dense[0, idx])
            
            item = {
                "rank": rank + 1,
                "raw_feature_name": raw_name,
                "feature_name": display_name,
                "shap_value": round(val, 4),
                "feature_value": round(feat_val, 2),
                "impact": "positive" if val > 0 else "negative",
                "description": FEATURE_DESCRIPTIONS.get(display_name, f"Model feature: {display_name}")
            }
            feature_contributions.append(item)
            
            if val > 0 and len(top_positive_features) < 5:
                top_positive_features.append(item)
            elif val < 0 and len(top_negative_features) < 5:
                top_negative_features.append(item)

        # 4. Multiclass Comparative Summary
        multiclass_breakdown = {}
        for c_idx, c_name in enumerate(pipe_classes):
            c_vals = shap_avg[0, :, c_idx]
            c_top = np.argsort(np.abs(c_vals))[::-1][:5]
            multiclass_breakdown[c_name] = {
                "base_value": round(float(expected_avg[c_idx]), 4),
                "calibrated_probability": round(float(class_probs[c_name]), 4),
                "top_features": [
                    {
                        "feature_name": self._format_feature_name(self.feature_names[f_idx]),
                        "shap_value": round(float(c_vals[f_idx]), 4),
                        "impact": "positive" if c_vals[f_idx] > 0 else "negative"
                    }
                    for f_idx in c_top
                ]
            }

        # 5. Waterfall step progression data for visualization
        running_value = base_value
        waterfall_steps = [{
            "step_name": "Baseline Output E[f(x)]",
            "contribution": round(base_value, 4),
            "cumulative_value": round(base_value, 4),
            "is_base": True
        }]

        for item in feature_contributions[:8]:
            running_value += item["shap_value"]
            waterfall_steps.append({
                "step_name": item["feature_name"],
                "contribution": item["shap_value"],
                "cumulative_value": round(running_value, 4),
                "impact": item["impact"]
            })

        waterfall_steps.append({
            "step_name": f"Final Class Output f(x)",
            "contribution": 0.0,
            "cumulative_value": round(running_value, 4),
            "is_final": True
        })

        return {
            "status": "success",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "model_version": self.model_version,
            "predicted_class": predicted_class,
            "focus_class": focus_class,
            "available_classes": pipe_classes,
            "calibrated_probabilities": {k: round(v, 4) for k, v in class_probs.items()},
            "class_probabilities": {k: round(v, 4) for k, v in class_probs.items()},
            "decision_threshold_tau_crit": self.tau_crit,
            "threshold_applied": self.tau_crit,
            "base_value": round(base_value, 4),
            "model_output_value": round(model_output_value, 4),
            "feature_contributions": feature_contributions,
            "top_positive_features": top_positive_features,
            "top_negative_features": top_negative_features,
            "waterfall_steps": waterfall_steps,
            "multiclass_breakdown": multiclass_breakdown,
            "clinical_disclaimer": (
                "EXPLAINABLE AI CLINICAL DISCLAIMER: SHAP values explain how the machine learning model "
                "statistically weighted its mathematical features to arrive at a triage priority classification. "
                "SHAP values DO NOT establish clinical biological causation, diagnose a medical condition, or "
                "prove that a feature is medically responsible for an emergency. Emergency decisions must be made "
                "by certified medical professionals."
            ),
            "disclaimer": (
                "EXPLAINABLE AI CLINICAL DISCLAIMER: SHAP values explain how the machine learning model "
                "statistically weighted its mathematical features to arrive at a triage priority classification. "
                "SHAP values DO NOT establish clinical biological causation, diagnose a medical condition, or "
                "prove that a feature is medically responsible for an emergency. Emergency decisions must be made "
                "by certified medical professionals."
            )
        }

    def get_global_feature_importance(self) -> Dict[str, Any]:
        """
        Calculates global feature importance (mean absolute SHAP across the clinical evaluation dataset).
        Caches the result to avoid recomputing on every administrative request.
        """
        if self.global_cache:
            return self.global_cache

        dataset_path = settings.DATA_DIR / "training_data" / "emergency_triage_dataset_clinical.csv"
        if not dataset_path.exists():
            return {
                "status": "unavailable",
                "error": "Clinical dataset not found."
            }

        try:
            df = pd.read_csv(dataset_path)
            
            # Stratified representative sample of 40 instances across classes for fast, accurate attribution
            if "urgency_category" in df.columns:
                sample_df = df.groupby("urgency_category", group_keys=False).apply(
                    lambda g: g.sample(min(len(g), 10), random_state=42)
                ).reset_index(drop=True)
            else:
                sample_df = df.sample(min(len(df), 40), random_state=42).reset_index(drop=True)

            sample_df["duration_log"] = np.log1p(sample_df["duration_minutes"].fillna(30.0))
            sample_df["age_norm"] = sample_df["age"].fillna(35.0) / 100.0

            prep = self.pipeline.named_steps["preprocessor"]
            X_dense = prep.transform(sample_df)
            if hasattr(X_dense, "toarray"):
                X_dense = X_dense.toarray()

            # Compute mean absolute SHAP for each class
            pipe_classes = list(self.pipeline.classes_)
            n_features = len(self.feature_names)
            global_importance_by_class: Dict[str, List[Dict[str, Any]]] = {}

            # Average over explainers
            shap_all = np.zeros((len(sample_df), n_features, len(pipe_classes)))
            expected_sum = np.zeros(len(pipe_classes))
            for exp in self.explainers:
                shap_all += exp.shap_values(X_dense)
                expected_sum += exp.expected_value
            shap_all /= len(self.explainers)
            expected_avg = expected_sum / len(self.explainers)

            class_base_values = {
                c_name: round(float(expected_avg[c_idx]), 4)
                for c_idx, c_name in enumerate(pipe_classes)
            }

            # Mean absolute SHAP per feature across all samples
            overall_importance = np.mean(np.abs(shap_all), axis=(0, 2))
            top_global_indices = np.argsort(overall_importance)[::-1][:20]

            global_rankings = []
            global_top_features = []

            for idx, f_idx in enumerate(top_global_indices):
                f_name = self._format_feature_name(self.feature_names[f_idx])
                mean_val = round(float(overall_importance[f_idx]), 4)
                desc = FEATURE_DESCRIPTIONS.get(f_name, f"Global clinical feature: {self.feature_names[f_idx]}")
                
                # Class mean impacts
                class_mean_impact = {
                    c_name: round(float(np.mean(shap_all[:, f_idx, c_idx])), 4)
                    for c_idx, c_name in enumerate(pipe_classes)
                }

                item = {
                    "rank": idx + 1,
                    "raw_feature_name": self.feature_names[f_idx],
                    "feature_name": f_name,
                    "mean_absolute_shap": mean_val,
                    "mean_abs_shap": mean_val,
                    "description": desc,
                    "class_mean_impact": class_mean_impact
                }
                global_rankings.append(item)
                global_top_features.append(item)

            # Class-specific importance
            for c_idx, c_name in enumerate(pipe_classes):
                c_imp = np.mean(np.abs(shap_all[:, :, c_idx]), axis=0)
                top_c = np.argsort(c_imp)[::-1][:10]
                global_importance_by_class[c_name] = [
                    {
                        "rank": idx + 1,
                        "feature_name": self._format_feature_name(self.feature_names[f_idx]),
                        "mean_absolute_shap": round(float(c_imp[f_idx]), 4),
                        "mean_abs_shap": round(float(c_imp[f_idx]), 4)
                    }
                    for idx, f_idx in enumerate(top_c)
                ]

            self.global_cache = {
                "status": "success",
                "calculated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "generated_at": datetime.utcnow().isoformat(),
                "sample_count": len(sample_df),
                "model_version": self.model_version,
                "classes": pipe_classes,
                "class_base_values": class_base_values,
                "global_rankings": global_rankings,
                "global_top_features": global_top_features,
                "global_importance_by_class": global_importance_by_class,
                "reviewer_role": "Clinical Algorithmic Safety Auditor",
                "methodology": "Ensemble TreeExplainer interventional feature attribution across calibrated Random Forest estimators",
                "clinical_disclaimer": (
                    "Global SHAP feature importance reflects empirical attribution across the clinical "
                    "evaluation cohort. It informs algorithmic auditing, model transparency, and bias verification."
                ),
                "disclaimer": (
                    "Global SHAP feature importance reflects empirical attribution across the clinical "
                    "evaluation cohort. It informs algorithmic auditing, model transparency, and bias verification."
                )
            }
            return self.global_cache
        except Exception as e:
            logger.error(f"Error computing global SHAP importance: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

shap_service = SHAPExplanationService()
