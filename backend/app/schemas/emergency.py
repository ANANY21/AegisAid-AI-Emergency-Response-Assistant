from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class InputTypeEnum(str, Enum):
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    MULTIMODAL = "multimodal"

class EmergencyInputRequest(BaseModel):
    description: str = Field(..., min_length=2, max_length=2000, description="Description of the emergency incident")
    input_type: InputTypeEnum = Field(default=InputTypeEnum.TEXT, description="Input modality used")
    voice_transcription: Optional[str] = Field(None, description="Raw transcription if audio was used")
    patient_age: Optional[int] = Field(None, ge=0, le=125, description="Patient age in years if known")
    duration: Optional[str] = Field(None, description="How long symptoms have lasted (e.g., '10 minutes', '2 hours')")
    severity_self_rating: Optional[str] = Field(None, description="User self-reported severity (e.g., mild, severe, unbearable)")
    location_text: Optional[str] = Field(None, description="User-reported location name or address")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="User latitude for nearby hospital dispatch")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="User longitude")
    image_base64: Optional[str] = Field(None, description="Optional base64-encoded image string")

class ExtractedEmergencyInfo(BaseModel):
    incident_type: str = Field(..., description="Categorized incident (e.g. cardiac_arrest, severe_bleeding, choking, burn, fracture, unknown)")
    symptoms: List[str] = Field(default_factory=list, description="Extracted clinical symptoms")
    affected_body_parts: List[str] = Field(default_factory=list, description="Body parts involved")
    severity_indicators: List[str] = Field(default_factory=list, description="Clinical high-risk markers e.g. cyanosis, unconsciousness")
    duration: str = Field(default="unknown", description="Reported duration of symptoms")
    age: Optional[int] = Field(default=None, description="Extracted age")
    location: str = Field(default="unspecified", description="Extracted location")
    input_type: str = Field(default="text", description="Modality")
    missing_information: List[str] = Field(default_factory=list, description="Critical information missing for safe triage")
    is_life_threatening: bool = Field(default=False, description="Flag indicating immediate peril")
