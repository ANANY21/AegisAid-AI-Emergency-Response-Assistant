"""
Machine Learning Classifier Module.
Exports the calibrated Random Forest TriageClassifier.
"""
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent.parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from app.models.classifier import TriageClassifier

__all__ = ["TriageClassifier"]
