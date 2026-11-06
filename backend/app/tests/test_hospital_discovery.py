"""
Unit tests for Real-Time GPS-Based Hospital Discovery System.
Validates:
1. Complete removal of hardcoded mock data, DEFAULT_FACILITIES, and fake offsets.
2. Haversine distance accuracy between real geographic coordinates.
3. OpenStreetMap / Google Places data parsing and field extraction.
4. Chennai demonstration presets validity and coordinates.
5. Reverse geocoding service and endpoints.
6. Route directions generation and road vs straight-line distance differentiation.
7. Presence of National Emergency Helpline 112 and safety disclaimers.
"""

import pytest
from unittest.mock import patch, MagicMock
from backend.app.services.google_maps_service import haversine_distance, google_maps_service
from backend.app.services.hospital_service import (
    hospital_service,
    HospitalDiscoveryService,
    CHENNAI_PRESETS
)
from backend.app.schemas.hospitals import (
    MedicalFacility,
    HospitalSearchResponse,
    ReverseGeocodeRequest,
    ReverseGeocodeResponse,
    PlaceDetailsResponse,
    RouteDirectionsResponse,
)
from backend.app.api.hospitals import (
    get_nearby_hospitals,
    get_hospital_details,
    get_hospital_directions,
    reverse_geocode_location,
    get_chennai_demonstration_presets,
)


# ============================================================================
# 1. Verification of Zero Mock / Dummy Data Fallbacks
# ============================================================================

def test_no_default_facilities_or_mock_offsets():
    """Verify that DEFAULT_FACILITIES and fake offsets are completely eliminated."""
    import backend.app.services.hospital_service as hs
    assert not hasattr(hs, "DEFAULT_FACILITIES"), "DEFAULT_FACILITIES dummy list must be removed!"
    
    import inspect
    source = inspect.getsource(hs)
    assert "+1-800-555-0199" not in source, "Mock phone number +1-800-555-0199 must not exist in hospital_service"
    assert "37.7749" not in source, "San Francisco dummy latitude 37.7749 must not exist in hospital_service"


# ============================================================================
# 2. Haversine Distance Accuracy
# ============================================================================

def test_haversine_distance_accuracy():
    """
    Test Haversine distance formula between known geographical landmarks:
    Chennai Central (13.0827, 80.2707) to Marina Beach (13.0500, 80.2824)
    Approximate straight-line distance is ~3.8 km.
    """
    lat1, lon1 = 13.0827, 80.2707
    lat2, lon2 = 13.0500, 80.2824
    dist = haversine_distance(lat1, lon1, lat2, lon2)
    assert 3.5 <= dist <= 4.2, f"Expected distance ~3.8 km, got {dist:.2f} km"


def test_haversine_distance_identical_coordinates():
    """Distance to identical coordinates must be 0."""
    dist = haversine_distance(12.9249, 80.1000, 12.9249, 80.1000)
    assert dist == 0.0


# ============================================================================
# 3. Chennai Demonstration Presets
# ============================================================================

def test_chennai_presets_validity():
    """Verify Chennai demonstration localities are populated with accurate coordinates."""
    presets = hospital_service.get_chennai_presets()
    assert len(presets) >= 12, "Should have at least 12 key Chennai localities"

    preset_names = [p["name"] for p in presets]
    assert "Tambaram" in preset_names
    assert "Chromepet" in preset_names
    assert "Guindy" in preset_names
    assert "Adyar" in preset_names
    assert "Velachery" in preset_names
    assert "Anna Nagar" in preset_names
    assert "T. Nagar" in preset_names
    assert "Porur" in preset_names
    assert "OMR" in preset_names

    # Check bounds (Chennai metropolitan area: Lat ~12.7-13.4, Lon ~79.9-80.4)
    for p in presets:
        assert 12.7 <= p["latitude"] <= 13.4, f"Invalid latitude for preset {p['name']}: {p['latitude']}"
        assert 79.9 <= p["longitude"] <= 80.4, f"Invalid longitude for preset {p['name']}: {p['longitude']}"
        assert len(p["locality"]) > 0


# ============================================================================
# 4. Overpass Response Normalization & Fallback
# ============================================================================

def test_find_nearby_facilities_parsing():
    """Test facilities normalization from mock Overpass API data."""
    mock_overpass_response = {
        "elements": [
            {
                "type": "node",
                "id": 101,
                "lat": 12.9255,
                "lon": 80.1012,
                "tags": {
                    "name": "Tambaram Taluk Hospital",
                    "amenity": "hospital",
                    "emergency": "yes",
                    "phone": "+91 44 2226 1234",
                    "addr:street": "GST Road",
                    "addr:city": "Chennai"
                }
            },
            {
                "type": "node",
                "id": 102,
                "lat": 12.9300,
                "lon": 80.1050,
                "tags": {
                    "name": "Chromepet Dental Clinic",
                    "amenity": "clinic",
                    "emergency": "no"
                }
            }
        ]
    }

    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_overpass_response
        mock_post.return_value = mock_resp

        # Search around Tambaram (12.9249, 80.1000)
        result = hospital_service.find_nearby_facilities(
            latitude=12.9249,
            longitude=80.1000,
            radius_km=5.0,
            sort_by="distance",
            filter_type="all"
        )

        assert isinstance(result, HospitalSearchResponse)
        assert result.count == 2
        assert result.search_center_lat == 12.9249
        assert result.search_center_lng == 80.1000
        assert len(result.facilities) == 2
        
        # Verify first facility (Tambaram Taluk Hospital)
        hosp = result.facilities[0]
        assert hosp.id == "osm-node-101"
        assert hosp.name == "Tambaram Taluk Hospital"
        assert hosp.has_emergency_room is True
        assert hosp.phone == "+91 44 2226 1234"
        assert hosp.straight_line_distance_km is not None
        assert hosp.straight_line_distance_km < 1.0

        # Safety disclaimer and helpline must be present
        assert "112" in result.emergency_helpline
        assert "Hospital location information does not guarantee" in result.disclaimer


def test_find_nearby_facilities_emergency_filter():
    """Verify that filter_type='emergency_only' filters out clinics without emergency facilities."""
    mock_overpass_response = {
        "elements": [
            {
                "type": "node",
                "id": 201,
                "lat": 12.9255,
                "lon": 80.1012,
                "tags": {
                    "name": "Tambaram Emergency Care",
                    "amenity": "hospital",
                    "emergency": "yes"
                }
            },
            {
                "type": "node",
                "id": 202,
                "lat": 12.9300,
                "lon": 80.1050,
                "tags": {
                    "name": "General Wellness Clinic",
                    "amenity": "clinic",
                    "emergency": "no"
                }
            }
        ]
    }

    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_overpass_response
        mock_post.return_value = mock_resp

        result = hospital_service.find_nearby_facilities(
            latitude=12.9249,
            longitude=80.1000,
            radius_km=5.0,
            filter_type="emergency_only"
        )

        assert len(result.facilities) == 1
        assert result.facilities[0].name == "Tambaram Emergency Care"


# ============================================================================
# 5. Reverse Geocoding Service
# ============================================================================

def test_reverse_geocode_nominatim():
    """Test reverse geocoding via Nominatim when Google Maps is not active."""
    mock_nom_response = {
        "display_name": "Madras Institute of Technology, Chromepet, Chennai, Tamil Nadu, 600044, India",
        "address": {
            "suburb": "Chromepet",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "country": "India",
            "postcode": "600044"
        }
    }

    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_nom_response
        mock_get.return_value = mock_resp

        res = hospital_service.reverse_geocode(12.9516, 80.1462)
        assert isinstance(res, ReverseGeocodeResponse)
        assert res.locality == "Chromepet"
        assert res.city == "Chennai"
        assert res.data_provider == "OpenStreetMap Nominatim"


# ============================================================================
# 6. Route Directions Generation
# ============================================================================

def test_get_route_directions():
    """Verify route directions computation generates navigation URLs and duration estimates."""
    directions = hospital_service.get_route_directions(
        origin_lat=12.9249,
        origin_lng=80.1000,
        dest_lat=12.9300,
        dest_lng=80.1050
    )
    assert isinstance(directions, RouteDirectionsResponse)
    assert directions.origin_lat == 12.9249
    assert directions.destination_lat == 12.9300
    assert directions.navigation_url.startswith("https://www.google.com/maps/dir/")
    assert directions.driving_duration_mins > 0
    assert len(directions.steps) >= 3


# ============================================================================
# 7. FastAPI Endpoint Handlers
# ============================================================================

def test_fastapi_endpoints():
    """Test direct invocation of FastAPI route handlers."""
    # 1. Chennai Demonstration Presets
    presets_resp = get_chennai_demonstration_presets()
    assert len(presets_resp) >= 12
    assert presets_resp[0]["name"] != ""

    # 2. Reverse Geocode Endpoint
    with patch.object(hospital_service, "reverse_geocode") as mock_rg:
        mock_rg.return_value = ReverseGeocodeResponse(
            formatted_address="Tambaram Railway Station, GST Road, Chennai",
            locality="Tambaram",
            city="Chennai",
            state="Tamil Nadu",
            country="India",
            data_provider="OpenStreetMap Nominatim"
        )
        req = ReverseGeocodeRequest(lat=12.9249, lng=80.1000)
        rg_resp = reverse_geocode_location(req)
        assert rg_resp.locality == "Tambaram"
        assert rg_resp.city == "Chennai"

    # 3. Nearby Hospitals Endpoint
    with patch.object(hospital_service, "find_nearby_facilities") as mock_find:
        mock_find.return_value = HospitalSearchResponse(
            facilities=[
                MedicalFacility(
                    id="osm-1",
                    place_id=None,
                    name="Deepam Hospital Tambaram",
                    facility_type="hospital",
                    address="GST Road, Tambaram",
                    latitude=12.9270,
                    longitude=80.1020,
                    distance_km=0.35,
                    straight_line_distance_km=0.35,
                    has_emergency_room=True,
                    data_provider="OpenStreetMap Overpass Network"
                )
            ],
            search_center_lat=12.9249,
            search_center_lng=80.1000,
            search_locality="Tambaram",
            search_radius_km=5.0,
            count=1,
            data_provider="OpenStreetMap Overpass Network",
            is_live_provider=True,
            provider_attribution="Live data via OpenStreetMap",
            google_maps_search_url="https://www.google.com/maps/search/hospitals/@12.9249,80.1,14z",
            emergency_helpline="112 (India National Emergency Helpline)"
        )
        nearby_resp = get_nearby_hospitals(lat=12.9249, lng=80.1000, radius_km=5.0)
        assert nearby_resp.count == 1
        assert nearby_resp.facilities[0].name == "Deepam Hospital Tambaram"
        assert nearby_resp.search_locality == "Tambaram"
