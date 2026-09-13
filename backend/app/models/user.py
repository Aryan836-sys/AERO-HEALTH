from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.favorite_location import FavoriteLocation
    from app.models.health_profile import HealthProfile
    from app.models.pollution_report import PollutionReport
    from app.models.user_alert import UserAlert


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    # 'en' or 'ne'
    preferred_language: Mapped[str] = mapped_column(
        String, nullable=False, server_default="en"
    )
    home_location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # passive_deletes=True: let Postgres's ON DELETE CASCADE (set on each FK)
    # do the actual deleting -- the delete-my-data promise must hold even for
    # a raw SQL delete, not just deletes that go through the ORM.
    health_profile: Mapped["HealthProfile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    alerts: Mapped[list["UserAlert"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    favorites: Mapped[list["FavoriteLocation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    reports: Mapped[list["PollutionReport"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
