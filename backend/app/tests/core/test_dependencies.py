from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.dependencies import get_current_user, require_role
from app.core.security import create_access_token


def _mock_user(user_id=1, role="registered"):
    user = MagicMock()
    user.id = user_id
    user.role = role
    return user


def _credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_get_current_user_returns_the_user_for_a_valid_token(monkeypatch):
    token = create_access_token(user_id=7)
    fake_user = _mock_user(user_id=7)
    monkeypatch.setattr("app.core.dependencies.get_user", lambda db, uid: fake_user)

    result = get_current_user(credentials=_credentials(token), db=MagicMock())
    assert result is fake_user


def test_get_current_user_rejects_an_invalid_token():
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=_credentials("not.a.real.token"), db=MagicMock())
    assert exc_info.value.status_code == 401


def test_get_current_user_rejects_a_token_for_a_deleted_user(monkeypatch):
    token = create_access_token(user_id=999)
    monkeypatch.setattr("app.core.dependencies.get_user", lambda db, uid: None)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=_credentials(token), db=MagicMock())
    assert exc_info.value.status_code == 401


def test_require_role_allows_a_matching_role():
    guard = require_role("admin")
    admin_user = _mock_user(role="admin")
    assert guard(user=admin_user) is admin_user


def test_require_role_rejects_a_non_matching_role():
    guard = require_role("admin")
    regular_user = _mock_user(role="registered")
    with pytest.raises(HTTPException) as exc_info:
        guard(user=regular_user)
    assert exc_info.value.status_code == 403


def test_require_role_allows_any_of_several_roles():
    guard = require_role("admin", "registered")
    regular_user = _mock_user(role="registered")
    assert guard(user=regular_user) is regular_user
