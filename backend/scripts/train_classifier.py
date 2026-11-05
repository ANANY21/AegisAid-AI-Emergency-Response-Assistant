import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_recall_fscore_support

# Setup path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from app.models.classifier import TriageClassifier
from app.core.logging import logger

def train_and_evaluate():
    data_path = BASE_DIR / "data" / "training_data" / "emergency_triage_dataset.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Training dataset not found at {data_path}")
        
    df = pd.read_csv(data_path)
    logger.info(f"Loaded dataset with {len(df)} samples across classes: {df['priority'].value_counts().to_dict()}")
    
    # Feature engineering pipeline
    text_features = "text"
    numeric_features = [
        "age", "duration_minutes", "has_breathing_difficulty",
        "has_unconsciousness", "has_severe_bleeding", "has_chest_pain"
    ]
    
    preprocessor = ColumnTransformer(
        transformers=[
            ("text", TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=1000), text_features),
            ("num", "passthrough", numeric_features)
        ]
    )
    
    base_rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        class_weight="balanced",
        random_state=42
    )
    
    # Calibrate classifier using sigmoid/isotonic to yield true probabilities
    calibrated_clf = CalibratedClassifierCV(estimator=base_rf, method="sigmoid", cv=3)
    
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", calibrated_clf)
    ])
    
    X = df[["text"] + numeric_features]
    y = df["priority"]
    
    # 5-Fold Stratified Cross-Validation for evaluation metrics
    skf = StratifiedKFold(n_splits=4, shuffle=True, random_state=42)
    y_pred = cross_val_predict(pipeline, X, y, cv=skf)
    
    labels = ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    acc = accuracy_score(y, y_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(y, y_pred, average="macro", zero_division=0)
    
    # Critical class metrics
    prec_classes, rec_classes, f1_classes, _ = precision_recall_fscore_support(y, y_pred, labels=labels, zero_division=0)
    crit_idx = labels.index("CRITICAL")
    critical_recall = float(rec_classes[crit_idx])
    
    cm = confusion_matrix(y, y_pred, labels=labels).tolist()
    
    metrics = {
        "accuracy": float(acc),
        "precision_macro": float(prec),
        "recall_macro": float(rec),
        "f1_macro": float(f1),
        "critical_class_recall": critical_recall,
        "confusion_matrix": cm,
        "classes": labels,
        "sample_count": len(df)
    }
    
    logger.info("===== MODEL EVALUATION REPORT =====")
    logger.info(f"Accuracy: {acc:.4f} | F1-Macro: {f1:.4f}")
    logger.info(f"CRITICAL Class Recall (Safety Essential): {critical_recall:.4f}")
    logger.info(f"Confusion Matrix: {cm}")
    
    # Train full pipeline on entire dataset
    pipeline.fit(X, y)
    
    # Save model and metrics
    output_model_path = BASE_DIR / "models" / "incident_classifier.joblib"
    output_metrics_path = BASE_DIR / "data" / "evaluation_datasets" / "classification_metrics.json"
    
    triage_model = TriageClassifier()
    triage_model.pipeline = pipeline
    triage_model.classes_ = list(calibrated_clf.classes_)
    triage_model.save(output_model_path, metadata=metrics)
    
    output_metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
        
    logger.info(f"Model saved to {output_model_path}")
    logger.info(f"Metrics saved to {output_metrics_path}")
    return metrics

if __name__ == "__main__":
    train_and_evaluate()
