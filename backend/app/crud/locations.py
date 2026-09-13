"""Location queries -- the reason PostGIS is in this stack.

Every function here takes plain lat/lng floats and returns plain Location
objects (or a (Location, distance_km) pair), so the API layer never has to
write SQL or know about PostGIS types.
"""
from geoalchemy2.types import Geography
from sqlalchemy import cast, func
from sqlalchemy.orm import Session

from app.models import Location


def _point(lat: float, lng: float):
    """A SRID-4326 point, built the same way everywhere so query plans match."""
    return func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)


def get_location(db: Session, location_id: int) -> Location | None:
    return db.get(Location, location_id)


def list_locations(db: Session) -> list[Location]:
    return db.query(Location).order_by(Location.id).all()


def get_nearest_location(
    db: Session, lat: float, lng: float
) -> tuple[Location, float] | None:
    """The single closest location to (lat, lng), with distance in km.

    Casts to ::geography so ST_Distance measures real meters on a sphere --
    left as ::geometry it would return a meaningless distance in degrees.
    """
    point = cast(_point(lat, lng), Geography)
    distance_m = func.ST_Distance(cast(Location.geometry, Geography), point).label(
        "distance_m"
    )

    row = db.query(Location, distance_m).order_by(distance_m).first()
    if row is None:
        return None

    location, distance_m_value = row
    return location, distance_m_value / 1000.0


def get_locations_within_radius(
    db: Session, lat: float, lng: float, meters: float
) -> list[Location]:
    """All locations within `meters` of (lat, lng) -- e.g. for "stations near me"."""
    point = cast(_point(lat, lng), Geography)
    return (
        db.query(Location)
        .filter(func.ST_DWithin(cast(Location.geometry, Geography), point, meters))
        .all()
    )


def get_locations_in_bbox(
    db: Session, min_lat: float, min_lng: float, max_lat: float, max_lng: float
) -> list[Location]:
    """All locations inside a map viewport. Uses the `&&` bounding-box overlap
    operator directly (index-only check) rather than ST_Intersects -- for
    point geometries the two are equivalent, and `&&` is what hits the GiST
    index without any exact-geometry work.
    """
    envelope = func.ST_MakeEnvelope(min_lng, min_lat, max_lng, max_lat, 4326)
    return db.query(Location).filter(Location.geometry.op("&&")(envelope)).all()
