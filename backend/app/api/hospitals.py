from fastapi import APIRouter, Query, HTTPException, Path as FPath
from typing import Optional, List, Dict, Any

from ..schemas.hospitals import (
    HospitalSearchResponse, PlaceDetailsResponse,
    RouteDirectionsResponse, ReverseGeocodeRequest,
    ReverseGeocodeResponse
)
from ..services.hospital_service import hospital_service
from ..core.logging import logger

router = APIRouter(prefix="", tags=["Hospital Discovery & Geolocation"])

@router.get("/api/v1/hospitals/nearby", response_model=HospitalSearchResponse)
@router.get("/api/hospitals/nearby", response_model=HospitalSearchResponse)
def get_nearby_hospitals(
    lat: Optional[float] = Query(None, description="User latitude (-90 to 90)"),
    lng: Optional[float] = Query(None, description="User longitude (-180 to 180)"),
    radius_km: float = Query(5.0, description="Search radius in kilometers (e.g. 3, 5, 10, 20)"),
    sort_by: str = Query("distance", description="Sort criteria: distance, travel_time, rating"),
    filter_type: str = Query("all", description="Facility filter: all, emergency_only, has_phone")
):
    """
    Discovers real, verified hospitals and emergency trauma centers using
    live Google Places API (New) or authoritative OpenStreetMap Overpass Network.
    Never returns fabricated or dummy hospital records.
    """
    if lat is not None and not (-90.0 <= lat <= 90.0):
        raise HTTPException(status_code=400, detail="Latitude must be between -90.0 and 90.0 degrees.")
    if lng is not None and not (-180.0 <= lng <= 180.0):
        raise HTTPException(status_code=400, detail="Longitude must be between -180.0 and 180.0 degrees.")
    if radius_km <= 0 or radius_km > 50:
        raise HTTPException(status_code=400, detail="Radius must be between 1 and 50 kilometers.")

    try:
        return hospital_service.find_nearby_facilities(
            latitude=lat,
            longitude=lng,
            radius_km=radius_km,
            sort_by=sort_by,
            filter_type=filter_type
        )
    except Exception as e:
        logger.error(f"Error executing hospital discovery: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to discover nearby hospitals: {str(e)}")

@router.get("/api/v1/hospitals/{place_id}", response_model=Optional[PlaceDetailsResponse])
@router.get("/api/hospitals/{place_id}", response_model=Optional[PlaceDetailsResponse])
def get_hospital_details(
    place_id: str = FPath(..., description="Google Place ID or provider facility ID")
):
    """
    Retrieves full details for a facility including verified contact numbers, website, and opening hours.
    """
    details = hospital_service.get_facility_details(place_id)
    if not details:
        raise HTTPException(status_code=404, detail="Additional provider details not found for this facility.")
    return details

@router.get("/api/v1/hospitals/{place_id}/directions", response_model=RouteDirectionsResponse)
@router.get("/api/hospitals/{place_id}/directions", response_model=RouteDirectionsResponse)
def get_hospital_directions(
    place_id: str = FPath(..., description="Google Place ID or provider facility ID"),
    origin_lat: float = Query(..., description="Origin latitude"),
    origin_lng: float = Query(..., description="Origin longitude"),
    dest_lat: float = Query(..., description="Hospital destination latitude"),
    dest_lng: float = Query(..., description="Hospital destination longitude")
):
    """
    Computes road distance and driving duration via Google Routes API.
    """
    try:
        return hospital_service.get_route_directions(
            origin_lat=origin_lat,
            origin_lng=origin_lng,
            dest_lat=dest_lat,
            dest_lng=dest_lng
        )
    except Exception as e:
        logger.error(f"Error computing route directions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/location/reverse-geocode", response_model=ReverseGeocodeResponse)
@router.post("/api/location/reverse-geocode", response_model=ReverseGeocodeResponse)
def reverse_geocode_location(req: ReverseGeocodeRequest):
    """
    Converts browser GPS coordinates into human-readable locality and address.
    """
    try:
        return hospital_service.reverse_geocode(req.lat, req.lng)
    except Exception as e:
        logger.error(f"Error in reverse geocoding: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/location/chennai-presets")
@router.get("/api/location/chennai-presets")
def get_chennai_demonstration_presets():
    """
    Returns official demonstration localities across Chennai with coordinates.
    """
    return hospital_service.get_chennai_presets()
