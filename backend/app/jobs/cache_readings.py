"""Day 6: the scheduled caching job.

Fetches a fresh reading for every WAQI-backed location and inserts it into
aqi_readings. Two sources per location:
- WAQI, via the location's own source_station_id (the same station the
  location was seeded from -- Day 4's pattern, moved here as the
  production job)
- OpenWeatherMap, via the location's lat/lng (Day 5's pattern) -- gives
  weather + a second, independent pollution reading

OpenAQ is intentionally NOT called here: OpenAQ uses its own location IDs,
which aren't stored anywhere on our Location model (WAQI's uid and OpenAQ's
location id are different ID systems for the same physical place). Wiring
that up needs a real id-mapping step (e.g. a `openaq_location_id` column,
or a nearest-match against OpenAQ's /locations by coordinates) -- not
guessed here, left as a follow-up rather than silently skipped without
explanation.

One location's failure never stops the rest -- each source, per location,
is wrapped so a single bad WAQI response or a down OpenWeatherMap call
doesn't lose every other reading in the run.

Run once:
    python -m app.jobs.cache_readings

Run continuously, sleeping AQI_CACHE_INTERVAL_MINUTES (default 30) between
runs:
    python -m app.jobs.cache_readings --loop
"""
import os
import sys
import time

from app.adapters.openweather import OpenWeatherError, get_location_reading as get_owm_reading
from app.adapters.waqi import WaqiFeedError, get_station_reading
from app.crud.readings import insert_reading
from app.database import SessionLocal
from app.models import Location
from geoalchemy2.shape import to_shape


def run_once() -> dict[str, int]:
    """One full pass over every WAQI-backed location. Returns counts."""
    db = SessionLocal()
    stats = {"waqi_inserted": 0, "waqi_skipped": 0, "owm_inserted": 0, "owm_skipped": 0}
    try:
        locations = (
            db.query(Location).filter(Location.source_station_id.isnot(None)).all()
        )
        print(f"Caching job: {len(locations)} location(s).")

        for loc in locations:
            try:
                fields = get_station_reading(loc.source_station_id)
                insert_reading(db, location_id=loc.id, **fields)
                stats["waqi_inserted"] += 1
                print(f"  waqi ok: {loc.area_name} -> aqi={fields['aqi']}")
            except WaqiFeedError as exc:
                stats["waqi_skipped"] += 1
                print(f"  waqi skipped: {loc.area_name} -> {exc}")

            try:
                point = to_shape(loc.geometry)
                fields = get_owm_reading(point.y, point.x)  # y=lat, x=lng
                insert_reading(db, location_id=loc.id, **fields)
                stats["owm_inserted"] += 1
                print(f"  owm ok: {loc.area_name} -> owm_aqi_index={fields['owm_aqi_index']}")
            except OpenWeatherError as exc:
                stats["owm_skipped"] += 1
                print(f"  owm skipped: {loc.area_name} -> {exc}")

        print(f"\nDone. {stats}")
        return stats
    finally:
        db.close()


def run_loop() -> None:
    interval_minutes = int(os.environ.get("AQI_CACHE_INTERVAL_MINUTES", "30"))
    print(f"Caching job loop: running every {interval_minutes} minute(s). Ctrl+C to stop.")
    while True:
        run_once()
        time.sleep(interval_minutes * 60)


if __name__ == "__main__":
    if "--loop" in sys.argv:
        run_loop()
    else:
        run_once()
