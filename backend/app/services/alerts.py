"""Alert threshold checking.

Delivery (email/SMS) is out of scope for the MVP: crossing detection is
what matters and what is tested; a notification job can call
`check_alerts_for_reading` after each new reading lands and log/notify.
"""
from typing import Iterable

from sqlalchemy.orm import Session

from app.crud.user_alerts import list_active_alerts_for_location
from app.models import AqiReading, UserAlert


def find_crossed_alerts(alerts: Iterable[UserAlert], aqi: int | None) -> list[UserAlert]:
    """Active alerts whose threshold `aqi` has reached. A reading with no AQI
    can never trigger an alert -- we don't guess."""
    if aqi is None:
        return []
    return [a for a in alerts if a.active and aqi >= a.aqi_threshold]


def check_alerts_for_reading(db: Session, reading: AqiReading) -> list[UserAlert]:
    alerts = list_active_alerts_for_location(db, reading.location_id)
    return find_crossed_alerts(alerts, reading.aqi)
