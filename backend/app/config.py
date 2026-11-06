import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "AegisAid - AI Emergency Response Assistant"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # GROQ API Configuration
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_VISION_MODEL: str = "qwen/qwen3.8-27b"
    GROQ_TIMEOUT_SECONDS: float = 20.0
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/data/emergency_assistant.db"
    
    # Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    KNOWLEDGE_BASE_DIR: Path = BASE_DIR / "data" / "knowledge_base"
    MODELS_DIR: Path = BASE_DIR / "models"
    UPLOADS_DIR: Path = BASE_DIR / "data" / "uploads"
    
    # RAG & Retrieval Validation Thresholds
    # Note: Semantic similarity thresholds must be validated against test data
    RETRIEVAL_SIMILARITY_THRESHOLD: float = 0.52
    RETRIEVAL_TOP_K: int = 4
    ENABLE_CROSS_ENCODER_RERANKING: bool = True
    
    # Safety & Classification Thresholds
    CLASSIFIER_CONFIDENCE_THRESHOLD: float = 0.60
    CRITICAL_BYPASS_ENABLED: bool = True
    
    # Facility Search (Google Maps Platform & OpenStreetMap)
    GOOGLE_MAPS_API_KEY: str = ""
    GOOGLE_MAPS_BASE_URL: str = "https://maps.googleapis.com/maps/api"
    GOOGLE_ROUTES_BASE_URL: str = "https://routes.googleapis.com"
    
    # OpenStreetMap Configuration & API Keys
    OPENSTREETMAP_API_KEY: str = ""
    OSM_API_KEY: str = ""
    LOCATIONIQ_API_KEY: str = ""
    GEOAPIFY_API_KEY: str = ""
    OPENROUTESERVICE_API_KEY: str = ""
    THUNDERFOREST_API_KEY: str = ""
    STADIA_MAPS_API_KEY: str = ""
    
    NOMINATIM_BASE_URL: str = "https://nominatim.openstreetmap.org"
    OVERPASS_API_URL: str = "https://overpass-api.de/api/interpreter"
    OSM_ROUTING_URL: str = "https://router.project-osrm.org"
    DEFAULT_SEARCH_RADIUS_METERS: int = 5000

    @property
    def active_osm_api_key(self) -> str:
        """Returns the first non-empty OpenStreetMap / OSM ecosystem API key."""
        return (
            self.OPENSTREETMAP_API_KEY or
            self.OSM_API_KEY or
            self.LOCATIONIQ_API_KEY or
            self.GEOAPIFY_API_KEY or
            self.OPENROUTESERVICE_API_KEY or
            self.THUNDERFOREST_API_KEY or
            self.STADIA_MAPS_API_KEY or
            ""
        ).strip()

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
