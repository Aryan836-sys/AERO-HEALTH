"""Day 7: password hashing and JWT issuing/verification.

Password hashing uses bcrypt via passlib (already a project dependency).
JWTs use python-jose. Both libraries were already pinned in
requirements.txt before this file existed -- Day 5/6's authors clearly
anticipated this module, even though it hadn't been built yet.

JWT_SECRET_KEY must be set in .env -- there is no fallback default,
because a guessable or shared default secret would let anyone forge a
valid token for any user. Generate one with:
    python -c "import secrets; print(secrets.token_hex(32))"
"""
import os
from datetime import datetime, timedelta, timezone

import bcrypt
from dotenv import load_dotenv
from jose import JWTError, jwt

load_dotenv()

JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "14"))


class TokenError(Exception):
    """Raised when a token is missing, expired, malformed, or the wrong type."""


def hash_password(plain_password: str) -> str:
    """Hashes via the `bcrypt` library directly, not passlib's bcrypt
    wrapper. passlib 1.7.4 is unmaintained and breaks against
    bcrypt>=4.1 (bcrypt removed the `__about__` attribute passlib's
    version-detection relies on) -- with bcrypt==5.0.0 pinned in
    requirements.txt, passlib.CryptContext silently corrupts the hashing
    call rather than raising a clear error. bcrypt itself has no such
    issue, so this bypasses passlib entirely.

    bcrypt has a genuine (not a bug) 72-byte limit on the input -- raise
    a clear error rather than let a long password truncate silently and
    then fail to verify later in a confusing way.
    """
    encoded = plain_password.encode("utf-8")
    if len(encoded) > 72:
        raise ValueError("Password must be 72 bytes or fewer.")
    return bcrypt.hashpw(encoded, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def _create_token(user_id: int, expires_delta: timedelta, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_access_token(user_id: int) -> str:
    return _create_token(user_id, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES), "access")


def create_refresh_token(user_id: int) -> str:
    return _create_token(user_id, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS), "refresh")


def decode_token(token: str, expected_type: str) -> int:
    """Returns the user id encoded in the token.

    Raises TokenError -- never a raw jose exception -- so callers (the
    auth dependency, the /refresh endpoint) have one exception type to
    handle regardless of *why* the token was bad.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise TokenError(f"Invalid or expired token: {exc}") from exc

    if payload.get("type") != expected_type:
        raise TokenError(f"Expected a {expected_type} token, got {payload.get('type')!r}")

    try:
        return int(payload["sub"])
    except (KeyError, ValueError, TypeError) as exc:
        raise TokenError(f"Token has no valid subject: {payload!r}") from exc