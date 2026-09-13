# Every model must be imported here so Alembic's autogenerate sees it via
# Base.metadata. Add each new model's import as it's created.
from app.models.location import Location
from app.models.aqi_reading import AqiReading
from app.models.user import User
from app.models.health_profile import HealthProfile
from app.models.pollution_report import PollutionReport
from app.models.user_alert import UserAlert
from app.models.favorite_location import FavoriteLocation
from app.models.health_advisory import HealthAdvisory

__all__ = [
    "Location",
    "AqiReading",
    "User",
    "HealthProfile",
    "PollutionReport",
    "UserAlert",
    "FavoriteLocation",
    "HealthAdvisory",
]
