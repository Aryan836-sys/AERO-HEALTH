from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.location import Location
    from app.models.user import User


class FavoriteLocation(Base):
    """A location a user has starred. Not spec'd in database-build-guide.md
    or data-dictionary.md (only user_alerts is) -- this minimal shape was
    agreed with the project owner to unblock M1/M5 now; adjust if the
    feature's real owner specs something different later.
    """

    __tablename__ = "favorite_locations"
    __table_args__ = (UniqueConstraint("user_id", "location_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="favorites")
    location: Mapped["Location"] = relationship()
