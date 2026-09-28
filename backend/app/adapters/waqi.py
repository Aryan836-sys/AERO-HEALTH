"""WAQI adapter.

Phase 0 finding (see tests/fixtures/waqi_feed_kathmandu_FAILS.json): WAQI's
per-station detail endpoint (`/feed/@{uid}/`, `/feed/{url-slug}/`,
`/feed/geo:lat;lon/`) returns `{"status": "nope", "data": "can not connect"}`
for every real Kathmandu-valley station, even though the same token works
fine against other cities (confirmed against Beijing/Shanghai/Delhi). Only
`/map/bounds/` and `/search/` work for this region, and both give just a
bare `aqi` number -- no `iaqi` pollutant breakdown, no `dominentpol`.

So unlike the textbook WAQI adapter (feed -> iaqi.* -> full breakdown), this
one parses the bounds/search station shape directly: `main_pollutant` and
every pollutant field stay `None`, and `aqi` is the only real signal. If
WAQI ever restores the per-station feed for this region, add a
`parse_waqi_feed()` alongside this one rather than replacing it -- the
bounds/search shape may still be the cheaper path for the discovery loop.
"""
from datetime import datetime, timezone

import httpx

from app.schemas import NormalizedReading

# Kathmandu valley bounding box: swLat,swLng,neLat,neLng
VALLEY_BOUNDS = "27.60,85.20,27.80,85.55"


def get_valley_stations(token: str, timeout: float = 15.0) -> list[dict]:
    """Call WAQI's /map/bounds/ and return the raw list of station dicts.

    Real, live data only -- if this call fails or WAQI reports non-ok
    status, it raises. Never fall back to fabricated station data.
    """
    url = "https://api.waqi.info/map/bounds/"
    response = httpx.get(
        url, params={"latlng": VALLEY_BOUNDS, "token": token}, timeout=timeout
    )
    response.raise_for_status()
    payload = response.json()

    if payload.get("status") != "ok":
        raise RuntimeError(f"WAQI bounds call failed: {payload}")

    return payload["data"]


def parse_waqi(station: dict, fetched_at: datetime | None = None) -> NormalizedReading:
    """Map one raw bounds/search station dict to a NormalizedReading.

    `aqi` comes back as a string ("60") or "-" when the station has no
    current reading -- "-" must yield `None`, not a crash or a fake 0.
    """
    raw_aqi = station["aqi"]
    aqi = int(raw_aqi) if raw_aqi not in (None, "-") else None

    recorded_at = datetime.fromisoformat(station["station"]["time"])

    return NormalizedReading(
        source_station_id=str(station["uid"]),
        aqi=aqi,
        source="waqi",
        reliability_status="official",
        recorded_at=recorded_at,
        fetched_at=fetched_at or datetime.now(timezone.utc),
    )
