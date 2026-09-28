"""Phase 10 of data-adapter-build-guide.md: one-time import of OpenData
Nepal's "Air Quality Data in Kathmandu" dataset (Jan 2015 - Mar 2021,
CC BY-SA) so trend charts have historical data from day one.

Real, inspected data:
- The dataset is two long-format CSVs served via CKAN, one per US Embassy
  AirNow monitor in Kathmandu: "US Diplomatic Post: Phora Durbar"
  (locationId 3460) and "US Diplomatic Post: Embassy" (locationId 3459) --
  the same two government reference monitors OpenAQ serves live today
  (isMonitor=True; see app/adapters/openaq.py).
- Each file only has two parameters: o3 (always **ppm**) and pm25 (always
  µg/m³). Per the same unit-guard rule as the live OpenAQ adapter, o3 in
  ppm is skipped -- no EPA conversion factor is specced anywhere in this
  project, so importing it would either corrupt the column or require
  inventing a conversion. Only pm25 survives, so these two locations'
  historical data covers PM2.5 trends only, not AQI or other pollutants.
- Both files use a -999 / -0.999 sentinel for "no reading" -- skipped,
  never stored as a real value.
- Row counts (31832 / 31378 usable pm25 rows) both fit under the CKAN SQL
  API's ~32000-row response cap, so each file is pulled in one query --
  no pagination needed.

Repeatable: deletes existing opendata_nepal_historical rows before
re-inserting, so re-running replaces rather than duplicates (same
idempotency contract as seed_locations.py). The two Embassy/Phora Durbar
locations are get-or-created the same way.

Run with:
    python -m app.scripts.import_opendata_nepal
"""
import logging
from datetime import datetime, timezone

import httpx
from geoalchemy2.elements import WKTElement

from app.database import SessionLocal
from app.models import AqiReading, Location
from app.services.reliability import check_reliability

logger = logging.getLogger(__name__)

API_URL = "https://api.opendatanepal.com/api/3/action/datastore_search_sql"

# CKAN resource id -> the source's own location id (used as our
# source_station_id, matching how WAQI's `uid` is used in seed_locations.py).
RESOURCES = {
    "918b774b-2a51-404f-92a0-0be1fe780f90": "3460",  # Phora Durbar
    "ad8d1b4d-7667-455d-ab74-d5966e8ba4c3": "3459",  # Embassy
}

SOURCE = "opendata_nepal_historical"
RELIABILITY_STATUS = "official"


def fetch_pm25_rows(resource_id: str) -> list[dict]:
    """Every usable (µg/m³, not ppm) pm25 row for one resource. o3 is
    intentionally excluded -- see module docstring."""
    sql = (
        'SELECT "locationId", location, utc, value, latitude, longitude '
        f"FROM \"{resource_id}\" WHERE parameter='pm25' AND unit != 'ppm'"
    )
    response = httpx.get(API_URL, params={"sql": sql}, timeout=60)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("success"):
        raise RuntimeError(f"OpenData Nepal query failed: {payload}")
    return payload["result"]["records"]


def get_or_create_location(
    db, source_station_id: str, area_name: str, lat: float, lon: float
) -> Location:
    location = (
        db.query(Location)
        .filter(Location.source_station_id == source_station_id)
        .one_or_none()
    )
    if location is not None:
        return location

    location = Location(
        area_name=area_name,
        geometry=WKTElement(f"POINT({lon} {lat})", srid=4326),
        source_station_id=source_station_id,
    )
    db.add(location)
    db.flush()  # assigns location.id within the open transaction
    return location


def import_resource(db, resource_id: str, source_station_id: str) -> int:
    rows = fetch_pm25_rows(resource_id)
    if not rows:
        logger.warning("No usable pm25 rows for resource %s", resource_id)
        return 0

    first = rows[0]
    location = get_or_create_location(
        db,
        source_station_id,
        first["location"],
        float(first["latitude"]),
        float(first["longitude"]),
    )

    fetched_at = datetime.now(timezone.utc)
    readings = []
    skipped_negative = 0
    for row in rows:
        value = float(row["value"])
        if value < 0:
            skipped_negative += 1
            continue
        readings.append(
            AqiReading(
                location_id=location.id,
                pm25=value,
                source=SOURCE,
                reliability_status=RELIABILITY_STATUS,
                recorded_at=datetime.fromisoformat(row["utc"]),
                fetched_at=fetched_at,
            )
        )

    db.bulk_save_objects(readings)
    logger.info(
        "%s: inserted %d readings (%d skipped as negative sentinels)",
        first["location"],
        len(readings),
        skipped_negative,
    )
    return len(readings)


def import_all() -> None:
    check_reliability(SOURCE, RELIABILITY_STATUS)  # fail fast if this pairing is ever invalid

    db = SessionLocal()
    try:
        deleted = db.query(AqiReading).filter(AqiReading.source == SOURCE).delete()
        if deleted:
            logger.info("Cleared %d existing historical rows before re-import", deleted)

        total = sum(
            import_resource(db, resource_id, source_station_id)
            for resource_id, source_station_id in RESOURCES.items()
        )

        db.commit()
        logger.info("Historical import done: %d readings total", total)
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import_all()
