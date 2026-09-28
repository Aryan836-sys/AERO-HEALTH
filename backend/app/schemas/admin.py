from datetime import datetime
from typing import Literal

from pydantic import BaseModel

ReportStatus = Literal["unverified", "verified", "rejected", "flagged"]


class ReportStatusUpdate(BaseModel):
    verification_status: ReportStatus


class AdminStatsOut(BaseModel):
    total_users: int
    total_locations: int
    total_reports: int
    reports_by_status: dict[str, int]
    active_alerts: int


class AuditLogOut(BaseModel):
    id: int
    admin_user_id: int
    action: str
    target_type: str
    target_id: int
    detail: str | None
    created_at: datetime

    model_config = {"from_attributes": True}