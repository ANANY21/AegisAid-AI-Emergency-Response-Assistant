import math
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import httpx

from ..config import settings
from ..schemas.hospitals import (
    MedicalFacility, PlaceDetailsResponse,
    RouteDirectionsResponse, ReverseGeocodeResponse
)
from ..core.logging import logger

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates geodesic straight-line distance in kilometers between two coordinates."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

class GoogleMapsPlatformService:
    PLACES_NEARBY_URL = "https://places.googleapis.com/v1/places:searchNearby"
    ROUTES_MATRIX_URL = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
    GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

    def __init__(self):
        self.api_key = (settings.GOOGLE_MAPS_API_KEY or "").strip()
        self.timeout = 8.0
        # Detailed diagnostics memory for last call
        self.last_diagnostics: Dict[str, Any] = {
            "is_configured": self.is_configured,
            "last_call_timestamp": None,
            "http_status": None,
            "error_message": None,
            "results_count": 0,
            "endpoint_used": None,
            "duration_ms": 0.0
        }

    @property
    def is_configured(self) -> bool:
        """Checks if a non-placeholder Google Maps API key is configured."""
        k = (self.api_key or "").strip()
        if not k or len(k) < 15:
            return False
        # Filter out common template strings
        if k in ["your_google_maps_api_key_here", "AIzaSyFakeKey", "None"]:
            return False
        return True

    def get_masked_key(self) -> Optional[str]:
        """Returns masked API key for safe developer diagnostics (e.g. AIzaSy...9xQz)."""
        if not self.is_configured:
            return None
        if len(self.api_key) <= 10:
            return "******"
        return f"{self.api_key[:6]}...{self.api_key[-4:]}"

    def search_nearby_places(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int = 5000,
        place_type: str = "hospital"
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Executes Google Places API (New) Nearby Search using official POST endpoint.
        Falls back to legacy Places Nearby Search if Places New returns format issues.
        Returns:
            Tuple of (facilities_list, diagnostic_metadata)
        """
        t0 = time.time()
        diag: Dict[str, Any] = {
            "is_configured": self.is_configured,
            "api_key_masked": self.get_masked_key(),
            "http_status": None,
            "error_code": None,
            "error_message": None,
            "endpoint": "https://places.googleapis.com/v1/places:searchNearby",
            "results_count": 0,
            "duration_ms": 0.0
        }

        if not self.is_configured:
            diag["error_code"] = "API_KEY_NOT_CONFIGURED"
            diag["error_message"] = "GOOGLE_MAPS_API_KEY is missing or empty in backend/.env"
            self.last_diagnostics = diag
            return [], diag

        # 1. Google Places API (New) - Nearby Search
        # Official endpoint: POST https://places.googleapis.com/v1/places:searchNearby
        url = "https://places.googleapis.com/v1/places:searchNearby"
        
        # Valid Table A types for Places API (New) searchNearby:
        # Note: "medical_clinic" is Table B and invalid in includedTypes; use "hospital"
        included_types = ["hospital"]

        field_mask = (
            "places.id,places.displayName,places.formattedAddress,places.location,"
            "places.types,places.nationalPhoneNumber,places.internationalPhoneNumber,"
            "places.websiteUri,places.rating,places.userRatingCount,places.regularOpeningHours,"
            "places.currentOpeningHours,places.googleMapsUri"
        )

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": field_mask
        }

        # Cap radius in meters per API limits (50,000m max)
        clamped_radius = min(max(float(radius_meters), 100.0), 50000.0)

        payload = {
            "includedTypes": included_types,
            "maxResultCount": 20,
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": float(latitude),
                        "longitude": float(longitude)
                    },
                    "radius": clamped_radius
                }
            }
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, headers=headers, json=payload)
                elapsed_ms = round((time.time() - t0) * 1000, 2)
                diag["http_status"] = resp.status_code
                diag["duration_ms"] = elapsed_ms

                if resp.status_code == 200:
                    data = resp.json()
                    places = data.get("places", [])
                    results = []
                    for p in places:
                        loc = p.get("location", {})
                        p_lat = loc.get("latitude")
                        p_lng = loc.get("longitude")
                        if p_lat is None or p_lng is None:
                            continue

                        name = p.get("displayName", {}).get("text", "Hospital / Medical Center")
                        p_id = p.get("id", f"place-{p_lat}-{p_lng}")
                        addr = p.get("formattedAddress", "Address available via Google Maps")
                        rating = p.get("rating")
                        ratings_count = p.get("userRatingCount")
                        phone = p.get("nationalPhoneNumber") or p.get("internationalPhoneNumber")
                        website = p.get("websiteUri")
                        maps_url = p.get("googleMapsUri") or f"https://www.google.com/maps/dir/?api=1&destination={p_lat},{p_lng}"
                        
                        opening_hours = p.get("regularOpeningHours") or p.get("currentOpeningHours") or {}
                        is_open = opening_hours.get("openNow")

                        results.append({
                            "place_id": p_id,
                            "name": name,
                            "latitude": p_lat,
                            "longitude": p_lng,
                            "formatted_address": addr,
                            "rating": rating,
                            "user_ratings_total": ratings_count,
                            "phone": phone,
                            "website": website,
                            "directions_url": maps_url,
                            "is_open_now": is_open,
                            "has_emergency_room": any(t in ["hospital", "emergency_room"] for t in p.get("types", ["hospital"])),
                            "provider": "Google Places API (New)"
                        })

                    diag["results_count"] = len(results)
                    self.last_diagnostics = diag
                    logger.info(f"Google Places API (New) returned {len(results)} facilities around ({latitude}, {longitude}) in {elapsed_ms}ms")
                    return results, diag

                # Capture explicit Google error codes
                try:
                    err_json = resp.json().get("error", {})
                    diag["error_code"] = err_json.get("status") or f"HTTP_{resp.status_code}"
                    diag["error_message"] = err_json.get("message") or resp.text[:200]
                except Exception:
                    diag["error_code"] = f"HTTP_{resp.status_code}"
                    diag["error_message"] = resp.text[:200]

                logger.warning(f"Google Places API (New) failed: HTTP {resp.status_code} ({diag['error_code']}): {diag['error_message']}")

        except Exception as e:
            diag["duration_ms"] = round((time.time() - t0) * 1000, 2)
            diag["error_code"] = type(e).__name__
            diag["error_message"] = str(e)
            logger.error(f"Error querying Google Places API (New): {e}")

        # 2. Secondary fallback to legacy Google Places Nearby Search if Places New gave 400 or other error
        try:
            t1 = time.time()
            legacy_url = f"{settings.GOOGLE_MAPS_BASE_URL}/place/nearbysearch/json"
            params = {
                "location": f"{latitude},{longitude}",
                "radius": clamped_radius,
                "type": "hospital",
                "key": self.api_key
            }
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(legacy_url, params=params)
                elapsed_ms = round((time.time() - t1) * 1000, 2)

                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get("status")
                    if status in ["OK", "ZERO_RESULTS"]:
                        results = []
                        for p in data.get("results", []):
                            geo = p.get("geometry", {}).get("location", {})
                            p_lat = geo.get("lat")
                            p_lng = geo.get("lng")
                            if p_lat is None or p_lng is None:
                                continue

                            p_id = p.get("place_id")
                            name = p.get("name", "Medical Facility")
                            vicinity = p.get("vicinity") or p.get("formatted_address") or "Address available via Google Maps"
                            maps_url = f"https://www.google.com/maps/dir/?api=1&destination={p_lat},{p_lng}"

                            results.append({
                                "place_id": p_id,
                                "name": name,
                                "latitude": p_lat,
                                "longitude": p_lng,
                                "formatted_address": vicinity,
                                "rating": p.get("rating"),
                                "user_ratings_total": p.get("user_ratings_total"),
                                "phone": None,
                                "website": None,
                                "directions_url": maps_url,
                                "is_open_now": p.get("opening_hours", {}).get("open_now"),
                                "has_emergency_room": True,
                                "provider": "Google Places API (Legacy)"
                            })

                        diag["http_status"] = 200
                        diag["results_count"] = len(results)
                        diag["endpoint"] = legacy_url
                        diag["duration_ms"] = elapsed_ms
                        self.last_diagnostics = diag
                        return results, diag
                    else:
                        diag["error_code"] = status
                        diag["error_message"] = data.get("error_message") or status
        except Exception as e:
            logger.error(f"Error querying legacy Google Places Nearby API: {e}")

        self.last_diagnostics = diag
        return [], diag

    def compute_road_distance_matrix(
        self,
        origin_lat: float,
        origin_lng: float,
        destinations: List[Tuple[float, float]]
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Computes real road distances and driving durations using Google Distance Matrix API.
        """
        if not self.is_configured or not destinations:
            return [None] * len(destinations)

        try:
            url = f"{settings.GOOGLE_MAPS_BASE_URL}/distancematrix/json"
            dest_str = "|".join([f"{d[0]},{d[1]}" for d in destinations[:10]])
            params = {
                "origins": f"{origin_lat},{origin_lng}",
                "destinations": dest_str,
                "mode": "driving",
                "departure_time": "now",
                "key": self.api_key
            }
            with httpx.Client(timeout=6.0) as client:
                resp = client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    rows = data.get("rows", [])
                    if rows and rows[0].get("elements"):
                        elements = rows[0]["elements"]
                        results = []
                        for el in elements:
                            if el.get("status") == "OK":
                                dist_m = el.get("distance", {}).get("value", 0)
                                dur_s = el.get("duration_in_traffic", {}).get("value") or el.get("duration", {}).get("value", 0)
                                dur_text = el.get("duration_in_traffic", {}).get("text") or el.get("duration", {}).get("text")
                                results.append({
                                    "road_distance_km": round(dist_m / 1000.0, 2),
                                    "driving_duration_mins": round(dur_s / 60.0, 1),
                                    "driving_duration_text": dur_text or f"{round(dur_s / 60.0)} mins"
                                })
                            else:
                                results.append(None)
                        return results
        except Exception as e:
            logger.warning(f"Error computing Google Road Distance Matrix: {e}")

        return [None] * len(destinations)

    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[ReverseGeocodeResponse]:
        """
        Resolves locality name and address via Google Geocoding API.
        """
        if not self.is_configured:
            return None

        try:
            url = f"{settings.GOOGLE_MAPS_BASE_URL}/geocode/json"
            params = {
                "latlng": f"{latitude},{longitude}",
                "result_type": "street_address|locality|sublocality|administrative_area_level_2",
                "key": self.api_key
            }
            with httpx.Client(timeout=4.0) as client:
                resp = client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    if results:
                        top = results[0]
                        formatted = top.get("formatted_address", "Detected Locality")
                        
                        locality = None
                        sublocality = None
                        city = None
                        state = None
                        country = None
                        postal_code = None

                        for c in top.get("address_components", []):
                            types = c.get("types", [])
                            if "sublocality" in types or "sublocality_level_1" in types:
                                sublocality = c.get("long_name")
                            elif "locality" in types:
                                locality = c.get("long_name")
                            elif "administrative_area_level_2" in types and not city:
                                city = c.get("long_name")
                            elif "administrative_area_level_1" in types:
                                state = c.get("long_name")
                            elif "country" in types:
                                country = c.get("long_name")
                            elif "postal_code" in types:
                                postal_code = c.get("long_name")

                        return ReverseGeocodeResponse(
                            formatted_address=formatted,
                            locality=locality or sublocality or city or "Detected Area",
                            sublocality=sublocality,
                            city=city or locality,
                            state=state,
                            country=country,
                            postal_code=postal_code,
                            data_provider="Google Geocoding API"
                        )
        except Exception as e:
            logger.warning(f"Google Geocoding API error: {e}")

        return None

    def get_place_details(self, place_id: str) -> Optional[PlaceDetailsResponse]:
        """
        Retrieves verified phone number, opening hours, and website via Google Place Details API.
        """
        if not self.is_configured:
            return None

        try:
            url = f"{settings.GOOGLE_MAPS_BASE_URL}/place/details/json"
            params = {
                "place_id": place_id,
                "fields": "place_id,name,formatted_address,formatted_phone_number,international_phone_number,website,rating,user_ratings_total,opening_hours,url,types",
                "key": self.api_key
            }
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    res = data.get("result")
                    if res:
                        op = res.get("opening_hours", {})
                        return PlaceDetailsResponse(
                            place_id=place_id,
                            name=res.get("name", "Medical Facility"),
                            formatted_address=res.get("formatted_address", "Address not available from provider"),
                            formatted_phone_number=res.get("formatted_phone_number"),
                            international_phone_number=res.get("international_phone_number"),
                            website=res.get("website"),
                            rating=res.get("rating"),
                            user_ratings_total=res.get("user_ratings_total"),
                            opening_hours=op.get("weekday_text"),
                            is_open_now=op.get("open_now"),
                            google_maps_url=res.get("url"),
                            types=res.get("types", [])
                        )
        except Exception as e:
            logger.error(f"Error fetching Google Place Details for {place_id}: {e}")

        return None

# Singleton Google Maps Platform Service instance
google_maps_service = GoogleMapsPlatformService()
