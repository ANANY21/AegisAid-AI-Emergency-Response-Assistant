import math
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import httpx

from ..config import settings
from ..schemas.hospitals import (
    MedicalFacility, PlaceDetailsResponse,
    RouteDirectionsResponse, ReverseGeocodeResponse
)
from ..core.logging import logger

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates geodesic straight-line distance in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

class GoogleMapsPlatformService:
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.timeout = 8.0

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 10)

    def search_nearby_places(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int = 5000,
        place_type: str = "hospital"
    ) -> List[Dict[str, Any]]:
        """
        Executes Google Places API (New or Legacy Nearby) search for actual medical facilities.
        """
        if not self.is_configured:
            return []

        # 1. Try Google Places API (New) endpoint
        try:
            url = "https://places.googleapis.com/v1/places:searchNearby"
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key,
                "X-Goog-FieldMask": (
                    "places.id,places.displayName,places.formattedAddress,places.location,"
                    "places.rating,places.userRatingCount,places.currentOpeningHours,"
                    "places.nationalPhoneNumber,places.websiteUri,places.googleMapsUri,places.types"
                )
            }
            payload = {
                "includedTypes": [place_type, "hospital", "medical_clinic"],
                "maxResultCount": 15,
                "locationRestriction": {
                    "circle": {
                        "center": {"latitude": latitude, "longitude": longitude},
                        "radius": float(radius_meters)
                    }
                }
            }

            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, headers=headers, json=payload)
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

                        name = p.get("displayName", {}).get("text", "Medical Facility")
                        p_id = p.get("id", f"place-{round(p_lat, 4)}-{round(p_lng, 4)}")
                        addr = p.get("formattedAddress", "Address not available from provider")
                        rating = p.get("rating")
                        ratings_count = p.get("userRatingCount")
                        phone = p.get("nationalPhoneNumber")
                        website = p.get("websiteUri")
                        maps_url = p.get("googleMapsUri") or f"https://www.google.com/maps/search/?api=1&query={p_lat},{p_lng}&query_place_id={p_id}"
                        
                        opening_hours = p.get("currentOpeningHours", {})
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
                            "has_emergency_room": any(t in ["hospital", "emergency_room"] for t in p.get("types", [])),
                            "provider": "Google Places API (New)"
                        })
                    if results:
                        logger.info(f"Google Places API (New) returned {len(results)} facilities around ({latitude}, {longitude})")
                        return results
                else:
                    logger.warning(f"Google Places API (New) returned HTTP {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"Error querying Google Places API (New): {e}")

        # 2. Fallback to standard Google Places Nearby Search
        try:
            legacy_url = f"{settings.GOOGLE_MAPS_BASE_URL}/place/nearbysearch/json"
            params = {
                "location": f"{latitude},{longitude}",
                "radius": radius_meters,
                "type": place_type,
                "key": self.api_key
            }
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(legacy_url, params=params)
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
                            vicinity = p.get("vicinity") or p.get("formatted_address") or "Address not available from provider"
                            rating = p.get("rating")
                            ratings_count = p.get("user_ratings_total")
                            is_open = p.get("opening_hours", {}).get("open_now")
                            maps_url = f"https://www.google.com/maps/search/?api=1&query={p_lat},{p_lng}&query_place_id={p_id}"

                            results.append({
                                "place_id": p_id,
                                "name": name,
                                "latitude": p_lat,
                                "longitude": p_lng,
                                "formatted_address": vicinity,
                                "rating": rating,
                                "user_ratings_total": ratings_count,
                                "phone": None,  # Will be enriched by place details if requested
                                "website": None,
                                "directions_url": maps_url,
                                "is_open_now": is_open,
                                "has_emergency_room": any(t in ["hospital", "emergency_room"] for t in p.get("types", [])),
                                "provider": "Google Places API"
                            })
                        logger.info(f"Google Places Nearby Search returned {len(results)} facilities")
                        return results
                    else:
                        logger.warning(f"Google Places Nearby API status: {status} - {data.get('error_message')}")
        except Exception as e:
            logger.error(f"Error querying Google Places Nearby API: {e}")

        return []

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

    def compute_road_distance_matrix(
        self,
        origin_lat: float,
        origin_lng: float,
        destinations: List[Tuple[float, float]]
    ) -> List[Dict[str, Any]]:
        """
        Calculates actual driving road distance and travel duration via Google Routes / Distance Matrix API.
        """
        if not self.is_configured or not destinations:
            return []

        try:
            # 1. Google Distance Matrix API
            dest_strings = [f"{lat},{lng}" for lat, lng in destinations[:25]]
            url = f"{settings.GOOGLE_MAPS_BASE_URL}/distancematrix/json"
            params = {
                "origins": f"{origin_lat},{origin_lng}",
                "destinations": "|".join(dest_strings),
                "mode": "driving",
                "traffic_model": "best_guess",
                "departure_time": "now",
                "key": self.api_key
            }
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") == "OK":
                        rows = data.get("rows", [])
                        if rows:
                            elements = rows[0].get("elements", [])
                            results = []
                            for el in elements:
                                if el.get("status") == "OK":
                                    dist_meters = el.get("distance", {}).get("value", 0)
                                    dur_seconds = el.get("duration", {}).get("value", 0)
                                    dur_text = el.get("duration", {}).get("text", "")
                                    results.append({
                                        "road_distance_km": round(dist_meters / 1000.0, 2),
                                        "driving_duration_mins": round(dur_seconds / 60.0, 1),
                                        "driving_duration_text": dur_text or f"{round(dur_seconds / 60.0)} mins"
                                    })
                                else:
                                    results.append(None)
                            return results
        except Exception as e:
            logger.error(f"Error computing Distance Matrix: {e}")

        return []

    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[ReverseGeocodeResponse]:
        """
        Reverse geocodes coordinates to street, locality, city, state, and postal code.
        """
        if not self.is_configured:
            return None

        try:
            url = f"{settings.GOOGLE_MAPS_BASE_URL}/geocode/json"
            params = {
                "latlng": f"{latitude},{longitude}",
                "key": self.api_key
            }
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    if results:
                        first = results[0]
                        formatted = first.get("formatted_address", "Unknown Locality")
                        
                        locality = None
                        sublocality = None
                        city = None
                        state = None
                        country = None
                        postal_code = None

                        for comp in first.get("address_components", []):
                            types = comp.get("types", [])
                            if "locality" in types:
                                locality = comp.get("long_name")
                            elif "sublocality" in types or "sublocality_level_1" in types:
                                sublocality = comp.get("long_name")
                            elif "administrative_area_level_2" in types:
                                city = comp.get("long_name")
                            elif "administrative_area_level_1" in types:
                                state = comp.get("long_name")
                            elif "country" in types:
                                country = comp.get("long_name")
                            elif "postal_code" in types:
                                postal_code = comp.get("long_name")

                        chosen_locality = sublocality or locality or city or "Detected Location"
                        return ReverseGeocodeResponse(
                            formatted_address=formatted,
                            locality=chosen_locality,
                            sublocality=sublocality,
                            city=city or locality,
                            state=state,
                            country=country,
                            postal_code=postal_code,
                            data_provider="Google Geocoding API"
                        )
        except Exception as e:
            logger.error(f"Error in Google Reverse Geocoding: {e}")

        return None

# Singleton service
google_maps_service = GoogleMapsPlatformService()
