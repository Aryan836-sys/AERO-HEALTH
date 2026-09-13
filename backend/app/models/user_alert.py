from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.location import Location
    from app.models.user import User


class UserAlert(Base):
    """A user's threshold alert for one location: notify when AQI crosses it."""

    __tablename__ = "user_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)

    aqi_threshold: Mapped[int] = mapped_column(Integer, nullable=False)
    # in-app / email
    notification_type: Mapped[str] = mapped_column(String, nullable=False)
    # server_default (not just a Python-side default) so the default holds
    # even for a raw-SQL insert, not only ones that go through the ORM.
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())

    user: Mapped["User"] = relationship(back_populates="alerts")
    location: Mapped["Location"] = relationship()
