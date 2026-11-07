"""Generation & Medical Response Protocols Package."""
from app.services.generation_service import generation_service, EmergencyGenerationService, DETERMINISTIC_FALLBACKS

__all__ = ["generation_service", "EmergencyGenerationService", "DETERMINISTIC_FALLBACKS"]
