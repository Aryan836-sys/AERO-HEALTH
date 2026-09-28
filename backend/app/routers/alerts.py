from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.crud.locations import get_location
from app.crud.user_alerts import (
    create_alert,
    delete_alert,
    get_alert_for_user,
    list_alerts_for_user,
    set_alert_active,
)
from app.database import get_db
from app.models import User
from app.schemas.alert import AlertIn, AlertOut, AlertUpdate

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _owned_alert(db: Session, alert_id: int, user: User):
    # 404 (not 403) for someone else's alert: don't reveal that it exists.
    alert = get_alert_for_user(db, alert_id, user.id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.get("", response_model=list[AlertOut])
def read_alerts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_alerts_for_user(db, user.id)


@router.post("", response_model=AlertOut, status_code=201)
def new_alert(
    body: AlertIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if get_location(db, body.location_id) is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return create_alert(
        db, user.id, body.location_id, body.aqi_threshold, body.notification_type
    )


@router.patch("/{alert_id}", response_model=AlertOut)
def update_alert(
    alert_id: int,
    body: AlertUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_alert(db, alert_id, user)
    return set_alert_active(db, alert_id, body.active)


@router.delete("/{alert_id}", status_code=204)
def remove_alert(
    alert_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    delete_alert(db, _owned_alert(db, alert_id, user))
