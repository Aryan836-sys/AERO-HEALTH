"""Day 6: reliability categories, nearest-station lookup, and the
WAQI -> OpenAQ -> stale-cache fallback chain.

Why this exists: Day 4/5 gave us three independent adapters, each of which
raises its own exception the moment its source is untrustworthy (down,
malformed, rate-limited). Nothing above them decided what to do next. This
module is that decision layer -- it tries sources in priority order and
only gives up on a location once every option (including reusing the last
good reading already in the database) has failed.

Reliability categories (also enforced by normalizer.py's _VALID_RELIABILITY,
kept here as the human-facing reference the plan asks for):
    official  -- a government/embassy-grade monitor (WAQI's own stations)
    sensor    -- a lower-cost community/reference sensor (OpenAQ)
    community -- a citizen-submitted pollution report, not a fixed monitor
    modelled  -- computed/interpolated, not measured (OpenWeatherMap)
"""
import json
import math
import os
import socket
import time
from datetime import datetime, timezone
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session

from app.adapters.openaq import OpenAqError, get_location_reading as get_openaq_reading
from app.adapters.waqi import WaqiFeedError, get_station_reading as get_waqi_reading
from app.crud.readings import get_latest_reading
from app.models import AqiReading, Location

load_dotenv()

OPENAQ_API_KEY = os.environ.get("OPENAQ_API_KEY", "")
OPENAQ_LOCATIONS_URL = "https://api.openaq.org/v3/locations?coordinates={lat},{lon}&radius={radius}&limit={limit}"

RELIABILITY_CATEGORIES: dict[str, str] = {
    "official": "Government or embassy-grade reference monitor (e.g. WAQI).",
    "sensor": "Lower-cost community/reference sensor network (e.g. OpenAQ).",
    "community": "Citizen-submitted pollution report, not a fixed monitor.",
    "modelled": "Computed or interpolated, not directly measured (e.g. OpenWeatherMap).",
}

# Network-level failures (as opposed to a well-formed "the data is bad"
# response, which each adapter already raises its own error for). These are
# the failures a retry actually has a chance of fixing.
_RETRYABLE_EXCEPTIONS = (URLError, socket.timeout, TimeoutError, ConnectionError)


class ReliabilityError(Exception):
    """Raised when a source fails at the network level even after retries."""


def retry_with_backoff(
    fn,
    *args,
    retries: int = 2,
    base_delay_seconds: float = 1.0,
    **kwargs,
) -> Any:
    """Call fn(*args, **kwargs), retrying on network-level failures only.

    A malformed/error *response* (WaqiFeedError, OpenAqError, ...) is not
    retried -- calling WAQI again won't fix a station that's genuinely
    reporting "-" for its AQI. Only timeouts, connection resets and DNS/
    connection failures are worth a second attempt, with exponential
    backoff (1s, 2s, 4s, ...) between them.
    """
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return fn(*args, **kwargs)
        except _RETRYABLE_EXCEPTIONS as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(base_delay_seconds * (2**attempt))
    fn_name = getattr(fn, "__name__", repr(fn))
    raise ReliabilityError(
        f"{fn_name} failed after {retries + 1} attempt(s): {last_exc}"
    ) from last_exc


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def nearest_openaq_location(
    lat: float, lon: float, radius_m: int = 25_000, limit: int = 5
) -> str | None:
    """Find the OpenAQ location id physically closest to (lat, lon).

    Our Location model only stores WAQI's station id (source_station_id) --
    OpenAQ has its own, unrelated id space for the same physical stations,
    and there's no stored mapping between the two (see cache_readings.py's
    module docstring). Rather than guessing or hard-coding a mapping, this
    asks OpenAQ itself which of its stations are near this point, right
    when we actually need a fallback, and picks the closest one.

    Returns None if OpenAQ has no station within radius_m -- not an error,
    just "no fallback available here."
    """
    url = OPENAQ_LOCATIONS_URL.format(lat=lat, lon=lon, radius=radius_m, limit=limit)
    req = Request(url, headers={"X-API-Key": OPENAQ_API_KEY})

    def _fetch() -> dict[str, Any]:
        with urlopen(req, timeout=15) as resp:
            return json.load(resp)

    payload = retry_with_backoff(_fetch)
    results = payload.get("results") or []
    if not results:
        return None

    best_id, best_km = None, None
    for result in results:
        coords = result.get("coordinates") or {}
        r_lat, r_lon = coords.get("latitude"), coords.get("longitude")
        if r_lat is None or r_lon is None:
            continue
        km = _haversine_km(lat, lon, r_lat, r_lon)
        if best_km is None or km < best_km:
            best_id, best_km = result.get("id"), km

    return str(best_id) if best_id is not None else None


def get_reading_with_fallback(db: Session, location: Location) -> dict[str, Any]:
    """Try WAQI, then OpenAQ, then the last cached reading, in that order.

    Returns a dict describing what happened and, where a live fetch
    succeeded, the fields ready for crud.readings.insert_reading():

        {"tier": "waqi",        "fresh": True,  "fields": {...}}
        {"tier": "openaq",      "fresh": True,  "fields": {...}}
        {"tier": "stale_cache", "fresh": False, "stale_reading": <AqiReading>}
        {"tier": "unavailable", "fresh": False, "stale_reading": None}

    Never fabricates a reading -- "stale_cache" means "reuse the real
    reading we already have," and "unavailable" means there is truly
    nothing to show, both of which the caller (the caching job, or an API
    endpoint) surfaces honestly rather than inventing a number.
    """
    point = to_shape(location.geometry)
    lat, lon = point.y, point.x

    if location.source_station_id:
        try:
            fields = retry_with_backoff(get_waqi_reading, location.source_station_id)
            return {"tier": "waqi", "fresh": True, "fields": fields, "error": None}
        except (WaqiFeedError, ReliabilityError) as exc:
            waqi_error = str(exc)
    else:
        waqi_error = "no source_station_id on this location"

    try:
        nearest_id = nearest_openaq_location(lat, lon)
        if nearest_id is not None:
            fields = retry_with_backoff(get_openaq_reading, nearest_id)
            return {"tier": "openaq", "fresh": True, "fields": fields, "error": None}
        openaq_error = "no OpenAQ station within radius"
    except (OpenAqError, ReliabilityError) as exc:
        openaq_error = str(exc)

    stale = get_latest_reading(db, location.id)
    if stale is not None:
        return {
            "tier": "stale_cache",
            "fresh": False,
            "stale_reading": stale,
            "error": f"waqi: {waqi_error}; openaq: {openaq_error}",
        }

    return {
        "tier": "unavailable",
        "fresh": False,
        "stale_reading": None,
        "error": f"waqi: {waqi_error}; openaq: {openaq_error}; no cached reading exists",
    }