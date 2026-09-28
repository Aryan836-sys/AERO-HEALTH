"""Day 7: registration, login, token refresh, and the current-user
endpoint -- the last one doubles as the "protected endpoint" proof the
plan's checklist asks to test.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.crud.users import create_user, get_user, get_user_by_email
from app.database import get_db
from app.models import User
from app.schemas.user import RefreshRequest, Token, UserLogin, UserOut, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    if get_user_by_email(db, payload.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = create_user(
        db,
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        preferred_language=payload.preferred_language,
        role="registered",
    )
    return user


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email)
    # Deliberately the same error for "no such email" and "wrong password" --
    # telling the two apart would let an attacker enumerate which emails
    # have accounts.
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password.",
    )
    if user is None or not verify_password(payload.password, user.password_hash):
        raise invalid_credentials

    return Token(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=Token)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    invalid_token = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token.",
    )
    try:
        user_id = decode_token(payload.refresh_token, expected_type="refresh")
    except TokenError:
        raise invalid_token

    user = get_user(db, user_id)
    if user is None:
        raise invalid_token

    # Issue a fresh pair rather than just a new access token -- a rotated
    # refresh token limits how long a leaked one stays useful.
    return Token(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    """Exists mainly to prove get_current_user actually protects an
    endpoint end-to-end: no/invalid token -> 401, valid token -> the
    account it belongs to."""
    return current_user