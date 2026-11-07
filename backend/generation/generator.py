"""
Generator alias module for backward compatibility.
"""
from .generation_service import generation_service, EmergencyGenerationService, DETERMINISTIC_FALLBACKS

__all__ = ["generation_service", "EmergencyGenerationService", "DETERMINISTIC_FALLBACKS"]
