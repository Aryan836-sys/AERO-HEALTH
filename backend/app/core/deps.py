"""Auth dependencies. User-scoped routes must get the user from here and
nowhere else -- never from a body, query or path field."""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import ACCESS, decode_token
from app.crud.users import get_user
from app.database import get_db
from app.models import User

_bearer = HTTPBearer(auto_error=False)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise _unauthorized()
    user_id = decode_token(credentials.credentials, ACCESS)
    user = get_user(db, user_id) if user_id is not None else None
    if user is None:
        raise _unauthorized()
    return user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User | None:
    """The caller if they sent a token, None for a guest. A token that is
    present but invalid is still a 401 -- never silently downgraded to guest,
    so a client with an expired token knows to refresh."""
    if credentials is None:
        return None
    return get_current_user(credentials, db)


def require_role(role: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role != role:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return user

    return checker


require_admin = require_role("admin")
