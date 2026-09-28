from datetime import datetime

from pydantic import BaseModel

from app.schemas.location import LocationOut


class FavoriteIn(BaseModel):
    location_id: int


class FavoriteOut(BaseModel):
    location_id: int
    created_at: datetime
    location: LocationOut
