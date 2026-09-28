from typing import Literal

from pydantic import BaseModel, Field

NotificationType = Literal["in_app", "email"]


class AlertCreate(BaseModel):
    location_id: int
    # US AQI is 0-500 -- reject anything outside that up front rather
    # than silently storing an alert that can never fire (>500) or
    # always fires immediately (<0).
    aqi_threshold: int = Field(ge=0, le=500)
    notification_type: NotificationType


class AlertActiveUpdate(BaseModel):
    active: bool


class AlertOut(BaseModel):
    id: int
    user_id: int
    location_id: int
    aqi_threshold: int
    notification_type: str
    active: bool

    model_config = {"from_attributes": True}