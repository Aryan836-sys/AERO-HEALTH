from datetime import datetime

from pydantic import BaseModel


class FavoriteLocationIn(BaseModel):
    location_id: int


class FavoriteLocationOut(BaseModel):
    id: int
    user_id: int
    location_id: int
    created_at: datetime

    model_config = {"from_attributes": True}