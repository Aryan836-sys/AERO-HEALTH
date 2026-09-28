"""Day 8: request/response shapes for the health profile.

There's deliberately no `user_id` field anywhere here -- the profile
router always derives it from the authenticated user (get_current_user),
never from the request body. That's what actually enforces "users can
only access their own profile," not a check that could be bypassed by
passing a different id.
"""
from typing import Literal

from pydantic import BaseModel

AgeGroup = Literal["child", "adult", "elderly"]
ActivityLevel = Literal["low", "moderate", "high"]


class HealthProfileIn(BaseModel):
    """Used for both POST (create) and PUT (update) -- upsert_health_profile
    handles either case identically, so one shape covers both."""

    age_group: AgeGroup | None = None
    asthma: bool = False
    respiratory_condition: bool = False
    heart_condition: bool = False
    pregnancy_status: bool = False
    outdoor_worker: bool = False
    activity_level: ActivityLevel | None = None


class HealthProfileOut(BaseModel):
    id: int
    user_id: int
    age_group: AgeGroup | None
    asthma: bool
    respiratory_condition: bool
    heart_condition: bool
    pregnancy_status: bool
    outdoor_worker: bool
    activity_level: ActivityLevel | None

    model_config = {"from_attributes": True}