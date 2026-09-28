"""Day 8: POST/GET/PUT /profile, always scoped to the authenticated user.

Every handler takes `current_user` from get_current_user and uses
current_user.id -- there is no way to pass a different user_id in, by
design (see schemas/health_profile.py's docstring).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.crud.health_profiles import get_health_profile, upsert_health_profile
from app.database import get_db
from app.models import User
from app.schemas.health_profile import HealthProfileIn, HealthProfileOut

router = APIRouter(prefix="/profile", tags=["profile"])


@router.post("", response_model=HealthProfileOut, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: HealthProfileIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Creates the profile, or updates it in place if one already exists
    -- a user has at most one (see the model's unique constraint on
    user_id), so "create when there's already one" isn't a conflict,
    just a no-op-shaped update."""
    return upsert_health_profile(db, user_id=current_user.id, **payload.model_dump())


@router.get("", response_model=HealthProfileOut)
def read_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = get_health_profile(db, current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No health profile yet for this account.",
        )
    return profile


@router.put("", response_model=HealthProfileOut)
def update_profile(
    payload: HealthProfileIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return upsert_health_profile(db, user_id=current_user.id, **payload.model_dump())