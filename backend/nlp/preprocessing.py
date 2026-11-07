"""
NLP Preprocessing Module.
Exports clinical text sanitization, typo correction, and normalization functions.
"""
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent.parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from app.services.preprocessing import clean_and_normalize_text, COMMON_TYPOS

__all__ = ["clean_and_normalize_text", "COMMON_TYPOS"]
