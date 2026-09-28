"""Health profile. The owner is always `user` from the token -- there is no
user_id anywhere in a request, so there is no way to address another
user's profile."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.crud.health_profiles import get_health_profile, upsert_health_profile
from app.database import get_db
from app.models import User
from app.schemas.profile import ProfileIn, ProfileOut

router = APIRouter(prefix="/profile", tags=["profile"])


@router.post("", response_model=ProfileOut, status_code=201)
def create_profile(
    body: ProfileIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if get_health_profile(db, user.id) is not None:
        raise HTTPException(status_code=409, detail="Profile already exists; use PUT to update it")
    return upsert_health_profile(db, user.id, **body.model_dump())


@router.get("", response_model=ProfileOut)
def read_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_health_profile(db, user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="No profile yet")
    return profile


@router.put("", response_model=ProfileOut)
def update_profile(
    body: ProfileIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if get_health_profile(db, user.id) is None:
        raise HTTPException(status_code=404, detail="No profile yet; use POST to create it")
    return upsert_health_profile(db, user.id, **body.model_dump())


@router.delete("", status_code=204)
def delete_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_health_profile(db, user.id)
    if profile is not None:
        db.delete(profile)
        db.commit()
