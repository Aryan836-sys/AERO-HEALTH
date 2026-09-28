"""The scheduled caching job (data-adapter-build-guide.md Phase 4/5): pull
every valley station from WAQI and OpenAQ, resolve each to a seeded
Location, and write a normalized reading. One flaky station must not kill the whole run.

Run once, manually:
    python -m app.jobs.cache_readings --once

Run on a schedule (every 30 min, blocks the process):
    python -m app.jobs.cache_readings
"""
import argparse
import logging
import os
import time

from dotenv import load_dotenv
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.adapters.openaq import (
    get_openaq_locations,
    get_valley_openaq_locations,
    openaq_client,
    parse_openaq,
)
from app.adapters.waqi import get_valley_stations, parse_waqi
from app.crud.locations import get_location_by_openaq_id, get_location_by_station_id
from app.crud.readings import insert_normalized_reading
from app.database import SessionLocal
from app.schemas import NormalizedReading

load_dotenv()
logger = logging.getLogger(__name__)

WAQI_TOKEN = os.environ["WAQI_TOKEN"]
# Optional: without it, a WAQI station with no current reading is stored
# as-is (aqi=None) rather than backfilled from OpenAQ.
OPENAQ_KEY = os.getenv("OPENAQ_KEY")
CACHE_INTERVAL_MINUTES = 30
# OpenAQ's free tier allows 60 requests/min; one /latest call per station.
OPENAQ_REQUEST_DELAY_S = 0.5

# 6 of the 7 real WAQI valley stations have a real OpenAQ location within
# 5.3km; the one outlier (Dhulikhel, in Kavre) is 19.7km from the nearest
# OpenAQ location and should NOT get a fallback match at this radius.
OPENAQ_FALLBACK_RADIUS_M = 6000
# How many nearest OpenAQ candidates to try before giving up -- the
# nearest one can have no current/usable sensor value.
OPENAQ_FALLBACK_CANDIDATES = 3


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((TimeoutError, ConnectionError)),
)
def _fetch_stations() -> list[dict]:
    return get_valley_stations(WAQI_TOKEN)


def _openaq_fallback(lat: float, lon: float) -> NormalizedReading | None:
    """Try the nearest OpenAQ locations to (lat, lon) in turn, returning the
    first one with a usable current reading. None if OPENAQ_KEY isn't set,
    discovery fails, or nothing nearby has data -- the caller falls back to
    whatever WAQI already gave it.
    """
    if not OPENAQ_KEY:
        return None

    try:
        candidates = get_openaq_locations(lat, lon, OPENAQ_FALLBACK_RADIUS_M, OPENAQ_KEY)
    except Exception:
        logger.exception("OpenAQ fallback discovery failed for (%s, %s)", lat, lon)
        return None

    for candidate in candidates[:OPENAQ_FALLBACK_CANDIDATES]:
        try:
            latest = openaq_client(candidate["id"], OPENAQ_KEY)
            return parse_openaq(candidate, latest)
        except ValueError:
            continue  # no usable sensor values at this candidate; try the next
        except Exception:
            logger.exception("OpenAQ fallback failed for location %s", candidate["id"])
            continue

    return None


def cache_readings() -> None:
    """One full pass: WAQI stations, then OpenAQ stations. Each source is
    independent -- one being down never blocks the other."""
    _cache_waqi_readings()
    _cache_openaq_readings()


def _cache_openaq_readings() -> None:
    """Fetch the latest reading for every seeded OpenAQ station and insert
    it. A single station's failure is logged and skipped."""
    if not OPENAQ_KEY:
        return
    try:
        stations = get_valley_openaq_locations(OPENAQ_KEY)
    except Exception:
        logger.exception("OpenAQ discovery failed; skipping OpenAQ this run")
        return

    db = SessionLocal()
    inserted, skipped = 0, 0
    try:
        for station in stations:
            try:
                location = get_location_by_openaq_id(db, station["id"])
                if location is None:
                    logger.warning(
                        "No seeded location for OpenAQ station %s (%s); run "
                        "seed_locations first. Skipping.",
                        station["id"],
                        station.get("name"),
                    )
                    skipped += 1
                    continue

                reading = parse_openaq(station, openaq_client(station["id"], OPENAQ_KEY))
                insert_normalized_reading(db, location.id, reading)
                inserted += 1
            except ValueError:
                logger.info("OpenAQ station %s has no usable values; skipping", station["id"])
                skipped += 1
            except Exception:
                logger.exception("Failed to cache reading for OpenAQ station %s", station["id"])
                db.rollback()
                skipped += 1
            time.sleep(OPENAQ_REQUEST_DELAY_S)
    finally:
        db.close()

    logger.info("OpenAQ cache run done: %d inserted, %d skipped", inserted, skipped)


def _cache_waqi_readings() -> None:
    """One pass over every valley WAQI station: fetch, parse, resolve, insert.

    A single station's failure (network error, unseeded station, bad
    payload) is logged and skipped -- it never aborts the rest of the run.
    """
    try:
        stations = _fetch_stations()
    except Exception:
        logger.exception("WAQI bounds call failed; skipping this cache run")
        return

    db = SessionLocal()
    inserted, skipped = 0, 0
    try:
        for station in stations:
            station_id = str(station["uid"])
            try:
                location = get_location_by_station_id(db, station_id)
                if location is None:
                    logger.warning(
                        "No seeded location for WAQI station %s (%s); run "
                        "seed_locations first. Skipping.",
                        station_id,
                        station.get("station", {}).get("name"),
                    )
                    skipped += 1
                    continue

                reading = parse_waqi(station)
                if reading.aqi is None:
                    fallback = _openaq_fallback(station["lat"], station["lon"])
                    if fallback is not None:
                        logger.info(
                            "WAQI had no current reading for station %s; using "
                            "OpenAQ fallback (source_station_id=%s)",
                            station_id,
                            fallback.source_station_id,
                        )
                        reading = fallback

                insert_normalized_reading(db, location.id, reading)
                inserted += 1
            except Exception:
                logger.exception("Failed to cache reading for station %s", station_id)
                skipped += 1
    finally:
        db.close()

    logger.info("WAQI cache run done: %d inserted, %d skipped", inserted, skipped)


def start_scheduler():
    """Run `cache_readings` now and then every CACHE_INTERVAL_MINUTES, on a
    background thread. Started by the FastAPI lifespan in app/main.py.
    """
    from datetime import datetime

    from apscheduler.schedulers.background import BackgroundScheduler

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        cache_readings,
        "interval",
        minutes=CACHE_INTERVAL_MINUTES,
        next_run_time=datetime.now(),  # first pass at startup, not 30 min later
        max_instances=1,  # a slow run never overlaps the next one
        coalesce=True,
    )
    scheduler.start()
    return scheduler


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # httpx logs full request URLs at INFO, including WAQI_TOKEN as a query
    # param -- keep it at WARNING so the token never lands in log output.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--once", action="store_true", help="Run a single cache pass and exit."
    )
    args = parser.parse_args()

    if args.once:
        cache_readings()
    else:
        import time

        start_scheduler()
        logger.info("Scheduler started, running every %d minutes.", CACHE_INTERVAL_MINUTES)
        while True:
            time.sleep(3600)
