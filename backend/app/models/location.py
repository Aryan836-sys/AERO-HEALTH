from __future__ import annotations

from typing import TYPE_CHECKING

from geoalchemy2 import Geometry
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.aqi_reading import AqiReading


class Location(Base):
    """A monitored point in the Kathmandu valley.

    Usually a real WAQI/OpenAQ station (seeded by Phase 3's
    seed_locations.py), but a location can also be a user-picked point with
    no station of its own -- resolved to modelled/nearest-station data at
    query time, never a fabricated reading (see architecture.md).
    """

    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    area_name: Mapped[str] = mapped_column(String, nullable=False)
    ward: Mapped[str | None] = mapped_column(String, nullable=True)

    # SRID 4326 = WGS84, the lat/lng system GPS and the source APIs use.
    geometry: Mapped[str] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326), nullable=False
    )

    # WAQI/OpenAQ station id, e.g. WAQI's "uid". Null for a non-station point.
    source_station_id: Mapped[str | None] = mapped_column(String, nullable=True)

    readings: Mapped[list["AqiReading"]] = relationship(back_populates="location")
