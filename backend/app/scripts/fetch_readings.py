"""Day 4: fetch a real, current reading from WAQI for every seeded station
and insert it into aqi_readings.

Only touches locations that came from WAQI (source_station_id is set) --
never fabricates a reading for a location with no real station behind it.

Run with:
    python -m app.scripts.fetch_readings
"""
from app.adapters.waqi import WaqiFeedError, get_station_reading
from app.crud.readings import insert_reading
from app.database import SessionLocal
from app.models import Location


def fetch_readings() -> None:
    db = SessionLocal()
    try:
        stations = (
            db.query(Location).filter(Location.source_station_id.isnot(None)).all()
        )
        print(f"Fetching readings for {len(stations)} WAQI-backed location(s).")

        inserted, failed = 0, 0
        for loc in stations:
            try:
                fields = get_station_reading(loc.source_station_id)
                insert_reading(db, location_id=loc.id, **fields)
                inserted += 1
                print(f"  ok: {loc.area_name} -> aqi={fields['aqi']}")
            except WaqiFeedError as exc:
                failed += 1
                print(f"  skipped: {loc.area_name} -> {exc}")

        print(f"\nDone. {inserted} reading(s) inserted, {failed} skipped.")
    finally:
        db.close()


if __name__ == "__main__":
    fetch_readings()
