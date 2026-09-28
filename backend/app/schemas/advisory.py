from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.profile import ProfileIn

Activity = Literal["low", "moderate", "high"]


class AdvisoryRequest(BaseModel):
    location_id: int
    # Planned exertion right now. Optional; falls back to the profile's usual
    # activity level.
    activity: Activity | None = None
    # Will the user be outside for a long stretch (roughly 2h+)?
    prolonged_exposure: bool = False
    # Optional "what-if" profile (e.g. the example adult/child on the
    # Advisory page). It is only ever input to the calculation -- it is not
    # saved and grants no access to anyone's stored profile. Without it, a
    # logged-in caller's own stored profile is used; a guest gets the
    # general (unpersonalised) advisory.
    profile: ProfileIn | None = None


class ReasonOut(BaseModel):
    code: str
    message: str


class AdvisoryOut(BaseModel):
    location_id: int
    aqi: int
    aqi_category: str
    risk_level: str  # low | moderate | high | very_high | severe
    recommendation: str
    reasons: list[ReasonOut]
    disclaimer: str
    personalized: bool
    source: str
    reliability_status: str
    recorded_at: datetime
