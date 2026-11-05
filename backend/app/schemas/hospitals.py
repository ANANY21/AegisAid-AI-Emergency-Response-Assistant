from pydantic import BaseModel, Field
from typing import List, Optional

class MedicalFacility(BaseModel):
    id: str
    name: str
    facility_type: str = Field(..., description="hospital, clinic, emergency_department")
    address: str
    distance_km: float
    phone: Optional[str] = None
    has_emergency_room: bool = True
    latitude: float
    longitude: float
    directions_url: str
    real_time_status_note: str = "Live bed/staff availability cannot be verified via automated feed. Call ahead."

class HospitalSearchResponse(BaseModel):
    facilities: List[MedicalFacility]
    search_center_lat: float
    search_center_lng: float
    count: int
    data_source: str = "OpenStreetMap / Healthcare Registry"
    disclaimer: str = "Real-time bed availability and emergency room wait times require calling the facility directly."
