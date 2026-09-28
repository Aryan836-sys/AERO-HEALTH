"""Password hashing and JWT creation/verification.

bcrypt is used directly rather than through passlib: passlib is unmaintained
and breaks against bcrypt >= 4.1 and Python 3.13. The scheme is the same
(bcrypt), so the guide's intent is unchanged.
"""
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings

ACCESS = "access"
REFRESH = "refresh"

# bcrypt only looks at the first 72 bytes; longer input is rejected by the
# request schema (max_length) so nothing is silently truncated.
MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def _create_token(user_id: int, token_type: str, expires: timedelta) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + expires,
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int) -> str:
    return _create_token(
        user_id, ACCESS, timedelta(minutes=get_settings().access_token_minutes)
    )


def create_refresh_token(user_id: int) -> str:
    return _create_token(
        user_id, REFRESH, timedelta(days=get_settings().refresh_token_days)
    )


def decode_token(token: str, expected_type: str) -> int | None:
    """The user id inside a valid token of `expected_type`, else None.

    Checking `type` matters: without it a long-lived refresh token could be
    presented as an access token (or vice versa).
    """
    settings = get_settings()
    try:
        claims = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        if claims.get("type") != expected_type:
            return None
        return int(claims["sub"])
    except (JWTError, KeyError, ValueError):
        return None
