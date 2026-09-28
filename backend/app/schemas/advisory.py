from pydantic import BaseModel


class AdvisoryOut(BaseModel):
    location_id: int
    aqi: int
    aqi_category: str
    severity: int
    recommendations: list[str]
    disclaimer: str
    personalized: bool