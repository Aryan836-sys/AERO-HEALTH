"""Adapter layer: converts internal DB-shaped schemas (LocationOut, ReadingOut)
into the shape the frontend's `types/api.ts` `Area`/`Reading` interfaces expect.

Why this exists: the frontend's types were written speculatively, before a real
backend existed ("Provisional... NOT generated from a real backend" -- see their
own comment in types/api.ts). Rather than reshaping the database around a guess,
this file is the one place that translates our real schema into their contract.

`district` now comes straight from the `locations.district` column (added via
migration c738e6d2e546, computed by app.utils.district.nearest_district --
WAQI gives no district field, so this is a nearest-reference-point
approximation, not a real boundary lookup; see that module for details).

Other known gaps, flagged rather than silently faked:
- `nameNe` (Nepali translation): no translation data exists yet. Empty string.
- `windDirection`: not stored (only wind *speed* is). Empty string.
- `isDemo`: always False here -- this is real data, never mock.
"""
from __future__ import annotations

from geoalchemy2.shape import to_shape
from pydantic import BaseModel, ConfigDict

from app.models.aqi_reading import AqiReading
from app.models.location import Location

# aqi_readings columns -> frontend's Pollutant keys
_POLLUTANT_COLUMNS = {
    "PM2.5": "pm25",
    "PM10": "pm10",
    "O3": "o3",
    "NO2": "no2",
    "SO2": "so2",
    "CO": "co",
}

# our internal pollutant column names -> frontend's Pollutant labels
_POLLUTANT_LABEL_BY_COLUMN = {
    "pm25": "PM2.5",
    "pm10": "PM10",
    "o3": "O3",
    "no2": "NO2",
    "so2": "SO2",
    "co": "CO",
}

# our reliability_status values -> frontend's Reliability union
_RELIABILITY_MAP = {
    "official": "official",
    "sensor": "official",
    "community": "community",
    "modelled": "modelled",
}


class FrontendWeather(BaseModel):
    temperature: float
    humidity: float
    windSpeed: float
    windDirection: str


class FrontendReading(BaseModel):
    aqi: int
    mainPollutant: str
    pollutants: dict[str, float]
    source: str
    reliability: str
    observedAt: str
    weather: FrontendWeather
    isDemo: bool = False

    @classmethod
    def from_reading(cls, reading: AqiReading) -> "FrontendReading":
        pollutants = {
            key: (getattr(reading, col) if getattr(reading, col) is not None else 0.0)
            for key, col in _POLLUTANT_COLUMNS.items()
        }
        return cls(
            aqi=reading.aqi if reading.aqi is not None else 0,
            mainPollutant=_POLLUTANT_LABEL_BY_COLUMN.get(
                reading.main_pollutant or "", "PM2.5"
            ),
            pollutants=pollutants,
            source=reading.source,
            reliability=_RELIABILITY_MAP.get(reading.reliability_status, "modelled"),
            observedAt=reading.recorded_at.isoformat(),
            weather=FrontendWeather(
                temperature=reading.temperature if reading.temperature is not None else 0.0,
                humidity=reading.humidity if reading.humidity is not None else 0.0,
                windSpeed=reading.wind if reading.wind is not None else 0.0,
                windDirection="",
            ),
        )


class FrontendArea(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    nameNe: str
    district: str
    latitude: float
    longitude: float
    reading: FrontendReading | None
    description: str
    featured: bool = False

    @classmethod
    def from_location(cls, location: Location, latest_reading: AqiReading | None) -> "FrontendArea":
        point = to_shape(location.geometry)
        return cls(
            id=str(location.id),
            name=location.area_name,
            nameNe="",
            district=location.district or "Kathmandu",
            latitude=point.y,
            longitude=point.x,
            reading=FrontendReading.from_reading(latest_reading) if latest_reading else None,
            description="",
            featured=False,
        )
