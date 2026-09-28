"""Public-safe report shape: deliberately has no user id, name or email, so a
report can never leak who submitted it."""
from datetime import datetime
from typing import Literal

from geoalchemy2.shape import to_shape
from pydantic import BaseModel

from app.models import PollutionReport

ReportCategory = Literal["waste_burning", "vehicle_smoke", "dust", "industrial", "other"]
ReportSeverity = Literal["low", "moderate", "high"]
ReportStatus = Literal["unverified", "verified", "rejected", "flagged"]


class ReportOut(BaseModel):
    id: int
    location_id: int
    latitude: float
    longitude: float
    category: str
    description: str | None
    severity: str | None
    image_url: str | None
    verification_status: str
    created_at: datetime


class ModerationRequest(BaseModel):
    verification_status: ReportStatus


class AdminReportOut(ReportOut):
    """What a moderator sees: adds who submitted it (None if anonymous)."""

    user_id: int | None


class StatsOut(BaseModel):
    users: int
    reports: int
    pending: int
    flagged: int
    reports_by_category: dict[str, int]


class AuditLogOut(BaseModel):
    id: int
    actor_id: int | None
    action: str
    target_type: str
    target_id: int
    detail: str | None
    created_at: datetime


def report_to_out(report: PollutionReport) -> ReportOut:
    point = to_shape(report.location.geometry)
    return ReportOut(
        id=report.id,
        location_id=report.location_id,
        latitude=point.y,
        longitude=point.x,
        category=report.category,
        description=report.description,
        severity=report.severity,
        image_url=report.image_url,
        verification_status=report.verification_status,
        created_at=report.created_at,
    )


def report_to_admin_out(report: PollutionReport) -> AdminReportOut:
    return AdminReportOut(**report_to_out(report).model_dump(), user_id=report.user_id)
