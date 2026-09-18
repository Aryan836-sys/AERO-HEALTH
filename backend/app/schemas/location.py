"""Location response schemas.

`Location.geometry` is a raw PostGIS column (a WKBElement at runtime) --
never exposed directly through the API. `LocationOut.from_location()`
converts it to plain `lat`/`lng` floats via geoalchemy2's `to_shape()`.
"""
from __future__ import annotations

from geoalchemy2.shape import to_shape
from pydantic import BaseModel, ConfigDict

from app.models.location import Location
from app.schemas.reading import ReadingOut


class LocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    area_name: str
    ward: str | None
    lat: float
    lng: float
    source_station_id: str | None

    @classmethod
    def from_location(cls, location: Location) -> "LocationOut":
        point = to_shape(location.geometry)  # shapely Point; .x = lng, .y = lat
        return cls(
            id=location.id,
            area_name=location.area_name,
            ward=location.ward,
            lat=point.y,
            lng=point.x,
            source_station_id=location.source_station_id,
        )


class LocationWithLatestReading(LocationOut):
    """A location plus its most recent AQI reading (null if none cached yet)."""

    latest_reading: ReadingOut | None = None

    @classmethod
    def from_location_and_reading(cls, location: Location, reading) -> "LocationWithLatestReading":
        base = LocationOut.from_location(location)
        return cls(
            **base.model_dump(),
            latest_reading=ReadingOut.model_validate(reading) if reading else None,
        )
