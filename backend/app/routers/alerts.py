"""Day 9: create/list AQI threshold alerts, and activate/deactivate one.

Creating and listing are naturally scoped to current_user.id, same
pattern as favorites.py and profile.py. Activate/deactivate needs an
explicit ownership check before touching a specific alert_id, since
that id could name anyone's alert -- crud.set_alert_active itself has
no user filter (it just loads by id), so the router is what actually
enforces "only your own alerts."
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.crud.user_alerts import create_alert, list_alerts_for_user, set_alert_active
from app.database import get_db
from app.models import User, UserAlert
from app.schemas.alert import AlertActiveUpdate, AlertCreate, AlertOut

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("", response_model=AlertOut, status_code=status.HTTP_201_CREATED)
def create_user_alert(
    payload: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_alert(
        db,
        user_id=current_user.id,
        location_id=payload.location_id,
        aqi_threshold=payload.aqi_threshold,
        notification_type=payload.notification_type,
    )


@router.get("", response_model=list[AlertOut])
def read_user_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_alerts_for_user(db, user_id=current_user.id)


@router.patch("/{alert_id}", response_model=AlertOut)
def update_alert_active(
    alert_id: int,
    payload: AlertActiveUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = db.get(UserAlert, alert_id)
    # Same response whether the alert doesn't exist at all or exists but
    # belongs to someone else -- a 403 here would confirm to an attacker
    # that alert_id 47 exists and just isn't theirs.
    not_found = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found."
    )
    if alert is None or alert.user_id != current_user.id:
        raise not_found

    return set_alert_active(db, alert_id=alert_id, active=payload.active)