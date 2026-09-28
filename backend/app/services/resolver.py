"""The point resolver -- data-adapter-build-guide.md Phase 8, item 4.

Given any lat/lng in the valley, decide what to show: an official-station
reading, nearest-station-with-distance info, or a modelled estimate.
**Never a fabricated solid reading for an unmonitored area** (architecture.md
"Honest sparsity" rule).

The two radii below are a starting judgment call, not a spec handed down
anywhere -- nothing in architecture.md/data-sources.md picks a number. They
come from EPA/WHO siting guidance on what area a monitor is representative
of (neighborhood scale: a couple km; urban scale: several km) rather than
from this project's own station spacing, since the real WAQI stations
sit 0.6-20km apart (see cache_readings.py's OPENAQ_FALLBACK_RADIUS_M note)
-- too irregular to derive a threshold from directly. Tune these two
constants if that judgment turns out wrong in practice.
"""
import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.adapters.openweather import (
    openweather_client,
    openweather_weather_client,
    parse_openweather,
)
from app.crud.locations import get_nearest_location
from app.crud.readings import get_latest_reading
from app.models import AqiReading, Location
from app.schemas import NormalizedReading

logger = logging.getLogger(__name__)

# Within this distance, a station's own cached reading is shown as-is --
# the query point is treated as "at" that station.
STATION_RADIUS_KM = 2.0
# Beyond this, "nearest station, N km away" stops being a meaningful proxy
# for local air quality -- prefer a modelled estimate for the exact point.
MODELLED_FALLBACK_RADIUS_KM = 8.0


@dataclass
class ResolvedReading:
    kind: str  # "station" | "nearest_station" | "modelled" | "no_data"
    location: Location | None
    distance_km: float | None
    cached_reading: AqiReading | None
    modelled_reading: NormalizedReading | None


def resolve_reading(
    db: Session, lat: float, lng: float, owm_api_key: str | None = None
) -> ResolvedReading:
    nearest = get_nearest_location(db, lat, lng)
    location = nearest[0] if nearest else None
    distance_km = nearest[1] if nearest else None
    cached = get_latest_reading(db, location.id) if location else None

    if cached is not None and distance_km <= STATION_RADIUS_KM:
        return ResolvedReading("station", location, distance_km, cached, None)

    if cached is not None and distance_km <= MODELLED_FALLBACK_RADIUS_KM:
        return ResolvedReading("nearest_station", location, distance_km, cached, None)

    if owm_api_key:
        try:
            pollution = openweather_client(lat, lng, owm_api_key)
            weather = openweather_weather_client(lat, lng, owm_api_key)
            modelled = parse_openweather(pollution, weather_raw=weather)
            return ResolvedReading("modelled", location, distance_km, None, modelled)
        except Exception:
            logger.exception("Modelled fallback failed for (%s, %s)", lat, lng)

    if cached is not None:
        # Beyond the ideal radius and modelling failed/unavailable -- a real,
        # honestly-labeled distant reading beats nothing.
        return ResolvedReading("nearest_station", location, distance_km, cached, None)

    return ResolvedReading("no_data", location, distance_km, None, None)
