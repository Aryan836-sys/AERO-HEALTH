from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class HealthProfile(Base):
    """Optional, at most one per user -- used by M1's advisory engine to
    tailor recommendations (e.g. asthma + high AQI -> stronger warning)."""

    __tablename__ = "health_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # child / adult / elderly
    age_group: Mapped[str | None] = mapped_column(String, nullable=True)
    # server_default (not just a Python-side default) so it holds even for a
    # raw-SQL insert, not only ones that go through the ORM.
    asthma: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())
    respiratory_condition: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=false()
    )
    heart_condition: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=false()
    )
    pregnancy_status: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=false()
    )
    outdoor_worker: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=false()
    )
    # low / moderate / high
    activity_level: Mapped[str | None] = mapped_column(String, nullable=True)

    user: Mapped["User"] = relationship(back_populates="health_profile")
