from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class HealthAdvisory(Base):
    """Reference rules for M1's advisory engine. Listed as 'optional to
    persist; may live in code' in database-build-guide.md -- the table
    exists so M1 can choose either approach without a schema change.
    """

    __tablename__ = "health_advisories"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Good / Moderate / Unhealthy for Sensitive Groups / ... / Hazardous
    aqi_category: Mapped[str] = mapped_column(String, nullable=False)
    # children / elderly / asthma / pregnant / outdoor_worker / general / etc.
    health_group: Mapped[str] = mapped_column(String, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[int] = mapped_column(Integer, nullable=False)
