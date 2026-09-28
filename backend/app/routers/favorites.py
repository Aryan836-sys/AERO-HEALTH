from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.crud.favorite_locations import add_favorite, list_favorites, remove_favorite
from app.crud.locations import get_location
from app.crud.readings import get_latest_readings
from app.database import get_db
from app.models import User
from app.schemas.favorite import FavoriteIn, FavoriteOut
from app.schemas.location import location_to_out

router = APIRouter(prefix="/favorites", tags=["favorites"])


def _to_out(db: Session, favorites) -> list[FavoriteOut]:
    latest = get_latest_readings(db, [f.location_id for f in favorites])
    return [
        FavoriteOut(
            location_id=f.location_id,
            created_at=f.created_at,
            location=location_to_out(f.location, latest.get(f.location_id)),
        )
        for f in favorites
    ]


@router.get("", response_model=list[FavoriteOut])
def read_favorites(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _to_out(db, list_favorites(db, user.id))


@router.post("", response_model=FavoriteOut, status_code=201)
def save_favorite(
    body: FavoriteIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if get_location(db, body.location_id) is None:
        raise HTTPException(status_code=404, detail="Location not found")
    favorite = add_favorite(db, user.id, body.location_id)
    return _to_out(db, [favorite])[0]


@router.delete("/{location_id}", status_code=204)
def delete_favorite(
    location_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Scoped to the caller's own favorites by construction (user_id comes
    from the token), so removing someone else's is impossible."""
    remove_favorite(db, user.id, location_id)
