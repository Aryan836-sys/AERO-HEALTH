from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.location import Location
    from app.models.user import User


class PollutionReport(Base):
    """A community-submitted report, moderated before it appears publicly."""

    __tablename__ = "pollution_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    # nullable: anonymous reports are allowed
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)

    # waste burning / vehicle smoke / dust / etc.
    category: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    severity: Mapped[str | None] = mapped_column(String, nullable=True)
    # unverified / verified / rejected / flagged
    verification_status: Mapped[str] = mapped_column(
        String, nullable=False, server_default="unverified"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User | None"] = relationship(back_populates="reports")
    location: Mapped["Location"] = relationship()
