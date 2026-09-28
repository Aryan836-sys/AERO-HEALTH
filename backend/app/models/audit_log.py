from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(Base):
    """A record of every admin action -- who did what, to what, when.

    Deliberately append-only from the API's perspective: nothing in
    app/routers/admin.py ever updates or deletes a row here, only
    inserts. An audit trail that could be edited after the fact isn't
    one.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    # e.g. "report_status_update"
    action: Mapped[str] = mapped_column(String, nullable=False)
    # e.g. "pollution_report"
    target_type: Mapped[str] = mapped_column(String, nullable=False)
    target_id: Mapped[int] = mapped_column(nullable=False)
    # short human-readable detail, e.g. "unverified -> verified"
    detail: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    admin_user: Mapped["User"] = relationship()