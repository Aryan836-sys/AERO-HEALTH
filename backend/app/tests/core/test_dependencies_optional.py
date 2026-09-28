from unittest.mock import MagicMock

from app.core.dependencies import get_current_user_optional
from app.core.security import create_access_token


def test_returns_none_when_no_credentials_given():
    assert get_current_user_optional(credentials=None, db=MagicMock()) is None


def test_returns_none_for_an_invalid_token_rather_than_raising():
    from fastapi.security import HTTPAuthorizationCredentials

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="not.a.real.token")
    assert get_current_user_optional(credentials=creds, db=MagicMock()) is None


def test_returns_the_user_for_a_valid_token(monkeypatch):
    from fastapi.security import HTTPAuthorizationCredentials

    fake_user = MagicMock()
    monkeypatch.setattr("app.core.dependencies.get_user", lambda db, uid: fake_user)
    token = create_access_token(user_id=7)
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    assert get_current_user_optional(credentials=creds, db=MagicMock()) is fake_user