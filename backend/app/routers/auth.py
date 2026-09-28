from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.limiter import AUTH_LIMIT, limiter
from app.core.security import (
    REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.crud.users import create_user, get_user, get_user_by_email
from app.database import get_db
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Verified against when the email is unknown, so a login for a missing
# account takes as long as one with a wrong password (no user enumeration
# via response time).
_DUMMY_HASH = hash_password("not-a-real-password")


COOKIE_PATH = "/auth"


def _token_pair(user, response: Response) -> TokenPair:
    """Issue a token pair and also set the refresh token as an HttpOnly
    cookie, so a browser client never has to keep it in JS-readable storage.
    (It is also returned in the body for non-browser API clients.)"""
    settings = get_settings()
    pair = TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=UserOut.model_validate(user),
    )
    response.set_cookie(
        settings.refresh_cookie_name,
        pair.refresh_token,
        max_age=settings.refresh_token_days * 86400,
        httponly=True,
        # SameSite=None is only accepted by browsers together with Secure.
        secure=settings.environment == "production" or settings.cookie_samesite == "none",
        samesite=settings.cookie_samesite,
        path=COOKIE_PATH,
    )
    return pair


@router.post("/register", response_model=UserOut, status_code=201)
@limiter.limit(AUTH_LIMIT)
def register(request: Request, body: RegisterRequest, db: Session = Depends(get_db)):
    email = body.email.lower()
    if get_user_by_email(db, email) is not None:
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    try:
        user = create_user(
            db,
            full_name=body.full_name,
            email=email,
            password_hash=hash_password(body.password),
            preferred_language=body.preferred_language,
        )
    except IntegrityError:
        # Lost a race with a concurrent registration of the same email.
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    return user


@router.post("/login", response_model=TokenPair)
@limiter.limit(AUTH_LIMIT)
def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    db: Session = Depends(get_db),
):
    user = get_user_by_email(db, body.email.lower())
    password_ok = verify_password(
        body.password, user.password_hash if user else _DUMMY_HASH
    )
    if user is None or not password_ok:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return _token_pair(user, response)


@router.post("/refresh", response_model=TokenPair)
@limiter.limit(AUTH_LIMIT)
def refresh(
    request: Request,
    response: Response,
    body: RefreshRequest | None = None,
    cookie_token: str | None = Cookie(None, alias=get_settings().refresh_cookie_name),
    db: Session = Depends(get_db),
):
    """Exchange a refresh token (body, or the HttpOnly cookie) for a new pair."""
    token = (body.refresh_token if body else None) or cookie_token
    user_id = decode_token(token, REFRESH) if token else None
    user = get_user(db, user_id) if user_id is not None else None
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    return _token_pair(user, response)


@router.post("/logout", status_code=204)
def logout(response: Response):
    """Clear the refresh cookie. Tokens are stateless, so an already-issued
    access token stays valid until it expires (30 min by default)."""
    response.delete_cookie(get_settings().refresh_cookie_name, path=COOKIE_PATH)
