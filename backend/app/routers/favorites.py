"""Day 9: save/list/remove favorite locations, scoped to the
authenticated user the same way profile.py is -- current_user.id, never
a client-supplied user_id.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.crud.favorite_locations import add_favorite, list_favorites, remove_favorite
from app.database import get_db
from app.models import User
from app.schemas.favorite import FavoriteLocationIn, FavoriteLocationOut

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.post("", response_model=FavoriteLocationOut, status_code=status.HTTP_201_CREATED)
def create_favorite(
    payload: FavoriteLocationIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Idempotent -- favoriting an already-favorited location just
    returns the existing row (see add_favorite), not a 409. Starring
    something twice isn't a conflict worth surfacing to the user."""
    return add_favorite(db, user_id=current_user.id, location_id=payload.location_id)


@router.get("", response_model=list[FavoriteLocationOut])
def read_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_favorites(db, user_id=current_user.id)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_favorite(
    location_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """204 whether or not it was actually favorited -- removing
    something that isn't there isn't an error from the client's
    perspective, it's just already in the state they wanted."""
    remove_favorite(db, user_id=current_user.id, location_id=location_id)