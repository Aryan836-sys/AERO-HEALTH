from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.location import Location


class AqiReading(Base):
    """One normalized reading, from any source, tagged with where it came
    from and how much to trust it. Matches app.schemas.NormalizedReading
    field-for-field -- see data-adapter-build-guide.md Phase 1.
    """

    __tablename__ = "aqi_readings"
    __table_args__ = (
        # Speeds up both "latest reading per location" and the 24h/7d/30d
        # trend queries, which always filter on location_id and order/range
        # on recorded_at (database-build-guide.md Phase 7).
        Index("ix_aqi_readings_location_recorded", "location_id", "recorded_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)

    # Nullable: OpenAQ gives raw concentrations, not an AQI, until Phase 9
    # computes one via the EPA formula -- never fake this value in the
    # meantime (data-adapter-build-guide.md Phase 6/9).
    aqi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    main_pollutant: Mapped[str | None] = mapped_column(String, nullable=True)

    # Every pollutant is nullable -- real stations skip fields (e.g. no SO2 sensor).
    pm25: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm10: Mapped[float | None] = mapped_column(Float, nullable=True)
    o3: Mapped[float | None] = mapped_column(Float, nullable=True)
    no2: Mapped[float | None] = mapped_column(Float, nullable=True)
    so2: Mapped[float | None] = mapped_column(Float, nullable=True)
    co: Mapped[float | None] = mapped_column(Float, nullable=True)

    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind: Mapped[float | None] = mapped_column(Float, nullable=True)
    pressure: Mapped[float | None] = mapped_column(Float, nullable=True)

    # OpenWeatherMap's own 1-5 index -- a different scale from `aqi` (US EPA
    # 0-500). Kept in its own column, never blended. See architecture.md's
    # "Scale-safety rule".
    owm_aqi_index: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    # waqi | openaq | openweathermap | community | opendata_nepal_historical
    source: Mapped[str] = mapped_column(String, nullable=False)
    # official | sensor | community | modelled
    reliability_status: Mapped[str] = mapped_column(String, nullable=False)

    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    location: Mapped["Location"] = relationship(back_populates="readings")
