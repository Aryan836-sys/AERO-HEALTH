from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# Matches the categories named in pollution_report.py's own model comment.
ReportCategory = Literal["waste_burning", "vehicle_smoke", "dust", "industrial", "other"]
ReportSeverity = Literal["low", "moderate", "high"]


class ReportCreate(BaseModel):
    """No `verification_status` field -- every report starts 'unverified'
    (the model's server_default); a client can never submit a
    pre-verified report. No `user_id` either -- see routers/reports.py
    for how it's set (or left null for an anonymous report)."""

    location_id: int
    category: ReportCategory
    description: str | None = Field(default=None, max_length=1000)
    image_url: str | None = None
    severity: ReportSeverity | None = None


class ReportOut(BaseModel):
    id: int
    user_id: int | None
    location_id: int
    category: str
    description: str | None
    image_url: str | None
    severity: str | None
    verification_status: str
    created_at: datetime

    model_config = {"from_attributes": True}