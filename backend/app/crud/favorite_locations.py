from sqlalchemy.orm import Session

from app.models import FavoriteLocation


def add_favorite(db: Session, user_id: int, location_id: int) -> FavoriteLocation:
    existing = (
        db.query(FavoriteLocation)
        .filter_by(user_id=user_id, location_id=location_id)
        .one_or_none()
    )
    if existing is not None:
        return existing

    favorite = FavoriteLocation(user_id=user_id, location_id=location_id)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


def remove_favorite(db: Session, user_id: int, location_id: int) -> None:
    db.query(FavoriteLocation).filter_by(
        user_id=user_id, location_id=location_id
    ).delete()
    db.commit()


def list_favorites(db: Session, user_id: int) -> list[FavoriteLocation]:
    return db.query(FavoriteLocation).filter_by(user_id=user_id).all()
