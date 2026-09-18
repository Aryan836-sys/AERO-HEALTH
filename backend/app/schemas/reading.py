"""AQI reading response schema -- mirrors app.models.aqi_reading.AqiReading
column-for-column (which itself mirrors the NormalizedReading contract)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    location_id: int

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

    owm_aqi_index: int | None

    source: str
    reliability_status: str

    recorded_at: datetime
    fetched_at: datetime
