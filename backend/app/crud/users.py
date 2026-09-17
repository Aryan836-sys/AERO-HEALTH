"""User account queries.

Password hashing is M1's concern (auth/JWT), not the DB layer's -- these
functions take an already-hashed `password_hash`, never a raw password.
"""
from sqlalchemy.orm import Session

from app.models import User


def create_user(
    db: Session,
    full_name: str,
    email: str,
    password_hash: str,
    preferred_language: str = "en",
    home_location_id: int | None = None,
) -> User:
    user = User(
        full_name=full_name,
        email=email,
        password_hash=password_hash,
        preferred_language=preferred_language,
        home_location_id=home_location_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).one_or_none()


def delete_user(db: Session, user_id: int) -> None:
    """Deletes the user; ON DELETE CASCADE handles their profile, alerts,
    favorites, and reports at the database level (see Phase 5)."""
    user = db.get(User, user_id)
    if user is not None:
        db.delete(user)
        db.commit()
