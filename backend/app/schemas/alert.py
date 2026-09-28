from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

NotificationType = Literal["in-app", "email"]


class AlertIn(BaseModel):
    location_id: int
    aqi_threshold: int = Field(ge=1, le=500)
    notification_type: NotificationType = "in-app"


class AlertUpdate(BaseModel):
    active: bool


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    location_id: int
    aqi_threshold: int
    notification_type: str
    active: bool
