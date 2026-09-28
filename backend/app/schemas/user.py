"""Day 7: request/response shapes for registration, login, and the
current-user endpoint. Never includes password_hash in any response --
UserOut is the only shape a user's own data is ever returned as.

Uses a plain `str` + a light regex check for email, not Pydantic's
EmailStr -- that needs the optional `email-validator` package, which
isn't in requirements.txt, and this avoids adding a dependency for one
field.
"""
import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(value: str) -> str:
    if not _EMAIL_RE.match(value):
        raise ValueError(f"Not a valid email address: {value!r}")
    return value.lower()


class UserRegister(BaseModel):
    full_name: str = Field(min_length=1)
    email: str
    password: str = Field(min_length=8)
    preferred_language: str = "en"

    _validate_email = field_validator("email")(_validate_email)


class UserLogin(BaseModel):
    email: str
    password: str

    _validate_email = field_validator("email")(_validate_email)


class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    preferred_language: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str