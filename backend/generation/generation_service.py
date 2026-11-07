"""
Medical Response Generation Module.
Exports generative AI and deterministic clinical guidance services.
"""
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent.parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from app.services.generation_service import generation_service, EmergencyGenerationService, DETERMINISTIC_FALLBACKS

__all__ = ["generation_service", "EmergencyGenerationService", "DETERMINISTIC_FALLBACKS"]
