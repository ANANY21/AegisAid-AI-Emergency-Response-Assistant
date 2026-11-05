from fastapi import APIRouter, Query
from typing import Optional
from ..schemas.hospitals import HospitalSearchResponse
from ..services.hospital_service import HospitalService

router = APIRouter(prefix="/api/hospitals", tags=["Medical Facilities"])

@router.get("/nearby", response_model=HospitalSearchResponse)
def get_nearby_hospitals(
    lat: Optional[float] = Query(None, description="User latitude"),
    lng: Optional[float] = Query(None, description="User longitude"),
    radius: int = Query(8000, description="Search radius in meters")
):
    return HospitalService.find_nearby_facilities(latitude=lat, longitude=lng, radius_meters=radius)
