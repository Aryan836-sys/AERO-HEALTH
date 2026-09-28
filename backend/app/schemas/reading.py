"""The one shape every adapter produces, whatever source it came from.

Matches app.models.AqiReading field-for-field (data-adapter-build-guide.md
Phase 1) so `insert_reading(db, **reading.model_dump(exclude={"source_station_id"}))`
just works. `source_station_id` isn't a column on aqi_readings -- it's how the
caller resolves `location_id` before inserting.
"""
from datetime import datetime

from pydantic import BaseModel


class NormalizedReading(BaseModel):
    source_station_id: str | None = None

    # US EPA AQI. None when a source only gives raw concentrations
    # (OpenAQ/OWM) and Phase 9's computed-AQI step hasn't run yet.
    aqi: int | None = None
    main_pollutant: str | None = None

    # Every pollutant is optional -- real stations skip fields.
    pm25: float | None = None
    pm10: float | None = None
    o3: float | None = None
    no2: float | None = None
    so2: float | None = None
    co: float | None = None

    temperature: float | None = None
    humidity: float | None = None
    wind: float | None = None
    pressure: float | None = None

    # OpenWeatherMap's own 1-5 index. A different scale from `aqi` --
    # never blended into it.
    owm_aqi_index: int | None = None

    # waqi | openaq | openweathermap | community | opendata_nepal_historical
    source: str
    # official | sensor | community | modelled
    reliability_status: str

    recorded_at: datetime
    fetched_at: datetime
