"""Day 6: the scheduled caching job.

Fetches a reading for every WAQI-backed location using the fallback chain
in adapters/reliability.py (WAQI -> OpenAQ -> reuse the last cached
reading), plus an independent OpenWeatherMap call for weather + OWM's own
pollution index.

Why OWM is separate from the fallback chain: it's not a substitute for a
missing AQI reading (it never provides `aqi`, only `owm_aqi_index`, a
different scale -- see aqi_reading.py's "Scale-safety rule"), so it's
inserted as its own row alongside whatever the fallback chain produced,
not used *instead of* it.

One location's failure never stops the rest -- each source, per location,
is wrapped so a single bad response or a down API doesn't lose every other
reading in the run.

Run once:
    python -m app.jobs.cache_readings

Run continuously, sleeping AQI_CACHE_INTERVAL_MINUTES (default 30) between
runs:
    python -m app.jobs.cache_readings --loop
"""
import os
import sys
import time

from geoalchemy2.shape import to_shape

from app.adapters.openweather import OpenWeatherError, get_location_reading as get_owm_reading
from app.adapters.reliability import ReliabilityError, get_reading_with_fallback
from app.crud.readings import insert_reading
from app.database import SessionLocal
from app.models import Location


def run_once() -> dict[str, int]:
    """One full pass over every WAQI-backed location. Returns counts."""
    db = SessionLocal()
    stats = {
        "waqi_inserted": 0,
        "openaq_inserted": 0,
        "stale_cache_reused": 0,
        "unavailable": 0,
        "owm_inserted": 0,
        "owm_skipped": 0,
    }
    try:
        locations = (
            db.query(Location).filter(Location.source_station_id.isnot(None)).all()
        )
        print(f"Caching job: {len(locations)} location(s).")

        for loc in locations:
            try:
                result = get_reading_with_fallback(db, loc)
            except ReliabilityError as exc:
                stats["unavailable"] += 1
                print(f"  reliability error: {loc.area_name} -> {exc}")
            else:
                tier = result["tier"]
                if tier in ("waqi", "openaq"):
                    fields = result["fields"]
                    insert_reading(db, location_id=loc.id, **fields)
                    stats[f"{tier}_inserted"] += 1
                    print(f"  {tier} ok: {loc.area_name} -> aqi={fields.get('aqi')}")
                elif tier == "stale_cache":
                    stale = result["stale_reading"]
                    stats["stale_cache_reused"] += 1
                    print(
                        f"  stale cache: {loc.area_name} -> reusing reading from "
                        f"{stale.recorded_at} ({result['error']})"
                    )
                else:  # "unavailable"
                    stats["unavailable"] += 1
                    print(f"  unavailable: {loc.area_name} -> {result['error']}")

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