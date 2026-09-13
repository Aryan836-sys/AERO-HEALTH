from sqlalchemy.orm import Session

from app.models import UserAlert


def create_alert(
    db: Session,
    user_id: int,
    location_id: int,
    aqi_threshold: int,
    notification_type: str,
) -> UserAlert:
    alert = UserAlert(
        user_id=user_id,
        location_id=location_id,
        aqi_threshold=aqi_threshold,
        notification_type=notification_type,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def list_alerts_for_user(db: Session, user_id: int) -> list[UserAlert]:
    return db.query(UserAlert).filter(UserAlert.user_id == user_id).all()


def list_active_alerts_for_location(db: Session, location_id: int) -> list[UserAlert]:
    """Active alerts watching one location -- what a notification job would
    check after each new reading lands."""
    return (
        db.query(UserAlert)
        .filter(UserAlert.location_id == location_id, UserAlert.active.is_(True))
        .all()
    )


def set_alert_active(db: Session, alert_id: int, active: bool) -> UserAlert | None:
    alert = db.get(UserAlert, alert_id)
    if alert is not None:
        alert.active = active
        db.commit()
        db.refresh(alert)
    return alert
