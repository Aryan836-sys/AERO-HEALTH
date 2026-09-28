from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.crud.pollution_reports import list_image_urls_for_user
from app.crud.users import delete_user
from app.database import get_db
from app.models import User
from app.schemas.auth import UserOut, UserUpdate
from app.services.uploads import delete_image

router = APIRouter(tags=["account"])


@router.get("/me", response_model=UserOut)
def read_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserOut)
def update_me(
    body: UserUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    user.preferred_language = body.preferred_language
    db.commit()
    db.refresh(user)
    return user


@router.delete("/me", status_code=204)
def delete_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete-my-data: removes the account and, via ON DELETE CASCADE, the
    user's profile, favorites, alerts and reports. Their uploaded report
    images are removed from disk too."""
    image_urls = list_image_urls_for_user(db, user.id)
    delete_user(db, user.id)
    for url in image_urls:
        delete_image(url)
