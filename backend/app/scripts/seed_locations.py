"""Phase 3 of database-build-guide.md: seed `locations` with the real,
currently-active WAQI stations in the Kathmandu valley.

Repeatable: matches on `source_station_id`, so re-running updates existing
rows instead of creating duplicates.

Run with:
    python -m app.scripts.seed_locations
"""
import json
import os
import urllib.request

from dotenv import load_dotenv
from geoalchemy2.elements import WKTElement

from app.database import SessionLocal
from app.models import Location
from app.utils.district import nearest_district

load_dotenv()

# Kathmandu valley bounding box: swLat,swLng,neLat,neLng
# (matches the box used in data-sources.md / data-adapter-build-guide.md)
VALLEY_BOUNDS = "27.60,85.20,27.80,85.55"

WAQI_TOKEN = os.environ["WAQI_TOKEN"]
BOUNDS_URL = f"https://api.waqi.info/map/bounds/?latlng={VALLEY_BOUNDS}&token={WAQI_TOKEN}"


def get_valley_stations() -> list[dict]:
    """Call WAQI's /map/bounds/ and return the raw list of station dicts.

    Real, live data only -- if this call fails, it raises. Never fall back
    to fabricated station data.
    """
    with urllib.request.urlopen(BOUNDS_URL, timeout=15) as resp:
        payload = json.load(resp)

    if payload.get("status") != "ok":
        raise RuntimeError(f"WAQI bounds call failed: {payload}")

    return payload["data"]


def seed() -> None:
    stations = get_valley_stations()
    print(f"WAQI returned {len(stations)} stations in the valley bounding box.")

    db = SessionLocal()
    try:
        inserted = 0
        updated = 0
        for station in stations:
            station_id = str(station["uid"])
            lat, lng = station["lat"], station["lon"]
            geometry = WKTElement(f"POINT({lng} {lat})", srid=4326)
            name = station["station"]["name"]
            district = nearest_district(lat, lng)

            existing = (
                db.query(Location)
                .filter(Location.source_station_id == station_id)
                .one_or_none()
            )

            if existing:
                existing.area_name = name
                existing.geometry = geometry
                existing.district = district
                updated += 1
            else:
                db.add(
                    Location(
                        area_name=name,
                        geometry=geometry,
                        source_station_id=station_id,
                        district=district,
                    )
                )
                inserted += 1

        db.commit()
        print(f"Seeded locations: {inserted} inserted, {updated} updated.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
