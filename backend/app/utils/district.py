"""Determine which Kathmandu Valley district a coordinate falls in.

WAQI's API gives us station lat/lng but no structured district field --
only a free-text station name too inconsistent to parse reliably.

Approach: nearest-reference-point (each district's historic Durbar Square).
Approximation, not a real boundary lookup -- a station near a real district
border could be misassigned. A precise fix would use PostGIS against real
district boundary polygons (a shapefile we don't have yet).
"""
import math

_DISTRICT_REFERENCE_POINTS = [
    ("Kathmandu", 27.7040, 85.3070),
    ("Lalitpur", 27.6730, 85.3250),
    ("Bhaktapur", 27.6710, 85.4280),
    ("Kavre", 27.6221, 85.5428),  # Dhulikhel, the district HQ -- valley bounding
    # box (27.60,85.20,27.80,85.55) reaches this far east and picks up real
    # Kavrepalanchok stations (e.g. "Dhulikhel, Kavre, Nepal"), not just the
    # three traditional valley districts.
]


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def nearest_district(lat: float, lng: float) -> str:
    return min(
        _DISTRICT_REFERENCE_POINTS,
        key=lambda ref: _haversine_km(lat, lng, ref[1], ref[2]),
    )[0]