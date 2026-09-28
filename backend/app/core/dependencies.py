"""Day 7: FastAPI dependencies that protect endpoints.

get_current_user is the base dependency -- any endpoint that depends on
it requires a valid access token, full stop. require_role() builds on
top of it for endpoints that need more than "any logged-in user" (e.g.
admin-only routes).

Guest access needs no dependency at all: a "guest" is simply a request
with no Authorization header, hitting a public endpoint. There is no
guest row in the users table and no guest token -- see security.py's
module docstring.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import TokenError, decode_token
from app.crud.users import get_user
from app.database import get_db
from app.models import User

# auto_error=False so a request with no Authorization header at all
# doesn't raise -- get_current_user_optional needs to tell "no token"
# apart from "bad token" itself.
bearer_scheme = HTTPBearer()
_optional_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """The base auth dependency. Raises 401 for any reason the token
    can't be trusted -- expired, malformed, wrong type, or naming a user
    that no longer exists (e.g. their account was deleted after the
    token was issued)."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        user_id = decode_token(credentials.credentials, expected_type="access")
    except TokenError:
        raise credentials_error

    user = get_user(db, user_id)
    if user is None:
        raise credentials_error

    return user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_optional_bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """For endpoints usable by both guests and logged-in users (e.g.
    advisory), where being logged in only changes the response, never
    gates access to it. Missing, malformed, expired, or otherwise
    untrustworthy credentials all quietly resolve to None -- exactly
    the same "act like a guest" outcome as never sending a token at
    all -- rather than raising 401 and blocking the request."""
    if credentials is None:
        return None
    try:
        user_id = decode_token(credentials.credentials, expected_type="access")
    except TokenError:
        return None
    return get_user(db, user_id)


def require_role(*allowed_roles: str):
    """Dependency factory: require_role("admin") protects an endpoint so
    only that role (or those roles) may call it -- built on top of
    get_current_user, so an invalid token is still rejected as 401
    before the role itself is ever checked."""

    def _check_role(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of these roles: {', '.join(allowed_roles)}",
            )
        return user

    return _check_role