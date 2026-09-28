"""Response shapes for locations and readings -- the contract the frontend
builds against. Every reading carries `source`, `reliability_status` and
`recorded_at` so the honesty fields always reach the UI."""
from datetime import datetime
from typing import Literal

from geoalchemy2.shape import to_shape
from pydantic import BaseModel, ConfigDict, computed_field

from app.models import AqiReading, Location
from app.services.aqi import aqi_category

ReadingRange = Literal["24h", "7d", "30d"]


class ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    location_id: int

    # None when the source only gave raw concentrations -- never faked.
    aqi: int | None
    main_pollutant: str | None
    pm25: float | None
    pm10: float | None
    o3: float | None
    no2: float | None
    so2: float | None
    co: float | None

    temperature: float | None
    humidity: float | None
    wind: float | None
    pressure: float | None

    # OpenWeatherMap's own 1-5 scale; NOT comparable to `aqi`.
    owm_aqi_index: int | None

    source: str
    reliability_status: str
    recorded_at: datetime
    fetched_at: datetime

    @computed_field
    @property
    def aqi_category(self) -> str | None:
        return aqi_category(self.aqi)


class LocationOut(BaseModel):
    id: int
    area_name: str
    ward: str | None
    latitude: float
    longitude: float
    source_station_id: str | None
    latest_reading: ReadingOut | None = None


class CompareOut(BaseModel):
    a: LocationOut
    b: LocationOut


def location_to_out(location: Location, latest: AqiReading | None) -> LocationOut:
    point = to_shape(location.geometry)
    return LocationOut(
        id=location.id,
        area_name=location.area_name,
        ward=location.ward,
        latitude=point.y,
        longitude=point.x,
        source_station_id=location.source_station_id,
        latest_reading=ReadingOut.model_validate(latest) if latest else None,
    )
