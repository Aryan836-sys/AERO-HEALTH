"""Phase 3 of database-build-guide.md: seed `locations` with the real,
currently-active WAQI and OpenAQ stations in the Kathmandu valley.

Repeatable: matches on `source_station_id`, so re-running updates existing
rows instead of creating duplicates.

Run with:
    python -m app.scripts.seed_locations
"""
import os

from dotenv import load_dotenv
from geoalchemy2.elements import WKTElement

from app.adapters.openaq import get_valley_openaq_locations, openaq_station_id
from app.adapters.waqi import get_valley_stations
from app.crud.locations import get_location_by_openaq_id
from app.database import SessionLocal
from app.models import Location

load_dotenv()

WAQI_TOKEN = os.environ["WAQI_TOKEN"]
OPENAQ_KEY = os.getenv("OPENAQ_KEY")


def seed() -> None:
    stations = get_valley_stations(WAQI_TOKEN)
    print(f"WAQI returned {len(stations)} stations in the valley bounding box.")

    db = SessionLocal()
    try:
        inserted = 0
        updated = 0
        for station in stations:
            station_id = str(station["uid"])
            geometry = WKTElement(
                f"POINT({station['lon']} {station['lat']})", srid=4326
            )
            name = station["station"]["name"]

            existing = (
                db.query(Location)
                .filter(Location.source_station_id == station_id)
                .one_or_none()
            )

            if existing:
                existing.area_name = name
                existing.geometry = geometry
                updated += 1
            else:
                db.add(
                    Location(
                        area_name=name,
                        geometry=geometry,
                        source_station_id=station_id,
                    )
                )
                inserted += 1

        db.commit()
        print(f"Seeded WAQI locations: {inserted} inserted, {updated} updated.")

        if OPENAQ_KEY:
            seed_openaq(db)
        else:
            print("OPENAQ_KEY not set; skipping OpenAQ stations.")
    finally:
        db.close()


def seed_openaq(db) -> None:
    """Add the valley's recently-active OpenAQ stations (mostly low-cost
    community sensors) alongside the WAQI ones."""
    stations = get_valley_openaq_locations(OPENAQ_KEY)
    print(f"OpenAQ returned {len(stations)} active stations in the valley.")

    inserted = updated = 0
    for station in stations:
        coords = station["coordinates"]
        geometry = WKTElement(
            f"POINT({coords['longitude']} {coords['latitude']})", srid=4326
        )
        name = station["name"].strip()

        existing = get_location_by_openaq_id(db, station["id"])
        if existing is None:
            db.add(
                Location(
                    area_name=name,
                    geometry=geometry,
                    source_station_id=openaq_station_id(station["id"]),
                )
            )
            inserted += 1
        elif existing.source_station_id.startswith("openaq:"):
            existing.area_name = name
            existing.geometry = geometry
            updated += 1

    db.commit()
    print(f"Seeded OpenAQ locations: {inserted} inserted, {updated} updated.")


if __name__ == "__main__":
    seed()
