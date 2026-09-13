from sqlalchemy.orm import Session

from app.models import HealthProfile


def get_health_profile(db: Session, user_id: int) -> HealthProfile | None:
    return db.query(HealthProfile).filter(HealthProfile.user_id == user_id).one_or_none()


def upsert_health_profile(db: Session, user_id: int, **fields) -> HealthProfile:
    """Create the profile if the user doesn't have one yet, else update it in
    place -- a user has at most one (see the unique constraint on user_id)."""
    profile = get_health_profile(db, user_id)
    if profile is None:
        profile = HealthProfile(user_id=user_id, **fields)
        db.add(profile)
    else:
        for key, value in fields.items():
            setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    return profile
