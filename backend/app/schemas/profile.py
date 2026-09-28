from typing import Literal

from pydantic import BaseModel, ConfigDict


class ProfileIn(BaseModel):
    """Every field is optional -- a user shares only what they choose to.
    There is deliberately no user_id here: ownership comes from the token."""

    age_group: Literal["child", "adult", "elderly"] | None = None
    asthma: bool = False
    respiratory_condition: bool = False
    heart_condition: bool = False
    pregnancy_status: bool = False
    outdoor_worker: bool = False
    activity_level: Literal["low", "moderate", "high"] | None = None


class ProfileOut(ProfileIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
