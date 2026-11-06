from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

class MedicalFacility(BaseModel):
    id: str
    place_id: Optional[str] = None
    name: str
    facility_type: str = Field(default="hospital", description="hospital, clinic, trauma_center, emergency_department")
    address: str
    locality: Optional[str] = None
    latitude: float
    longitude: float
    road_distance_km: Optional[float] = Field(None, description="Actual driving road distance via Google Routes API")
    straight_line_distance_km: float = Field(..., description="Calculated straight-line distance in kilometers")
    distance_km: float = Field(..., description="Primary distance display in kilometers (road distance preferred)")
    driving_duration_mins: Optional[float] = Field(None, description="Estimated driving duration in minutes")
    driving_duration_text: Optional[str] = Field(None, description="Formatted travel time (e.g., '12 mins')")
    phone: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    is_open_now: Optional[bool] = None
    opening_hours_text: Optional[str] = None
    has_emergency_room: bool = True
    directions_url: Optional[str] = None
    place_url: Optional[str] = None
    osm_directions_url: Optional[str] = None
    real_time_status_note: str = (
        "Hospital location information does not guarantee emergency department availability "
        "or treatment capacity. Call the hospital or emergency services (112) to confirm."
    )
    data_provider: str = "Google Places API"
    last_updated: Optional[str] = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    )

class HospitalSearchResponse(BaseModel):
    facilities: List[MedicalFacility]
    search_center_lat: float
    search_center_lng: float
    search_locality: Optional[str] = None
    search_radius_km: float
    count: int
    data_provider: str = "Google Maps Platform (Places New & Routes)"
    is_live_provider: bool = True
    provider_attribution: str = "Powered by Google Maps Platform & Official Healthcare Registry"
    google_maps_search_url: str
    osm_search_url: Optional[str] = None
    osm_api_key_configured: bool = False
    emergency_helpline: str = "112 (India National Emergency Helpline)"
    disclaimer: str = (
        "CRITICAL DISCLAIMER: Hospital location information does not guarantee emergency department availability "
        "or treatment capacity. Call the hospital or emergency services (112) to confirm. In life-threatening "
        "emergencies, immediately call 112 for ambulance transport."
    )

class ReverseGeocodeRequest(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0)
    lng: float = Field(..., ge=-180.0, le=180.0)

class ReverseGeocodeResponse(BaseModel):
    formatted_address: str
    locality: str
    sublocality: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    data_provider: str = "Google Geocoding API"

class PlaceDetailsResponse(BaseModel):
    place_id: str
    name: str
    formatted_address: str
    formatted_phone_number: Optional[str] = None
    international_phone_number: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    opening_hours: Optional[List[str]] = None
    is_open_now: Optional[bool] = None
    google_maps_url: Optional[str] = None
    types: List[str] = Field(default_factory=list)

class RouteDirectionsResponse(BaseModel):
    origin_lat: float
    origin_lng: float
    destination_lat: float
    destination_lng: float
    road_distance_km: float
    driving_duration_mins: float
    driving_duration_text: str
    navigation_url: str
    osm_navigation_url: Optional[str] = None
    route_summary: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    data_provider: str = "Google Routes API"
