from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.dependencies import get_current_user
from app.database import get_db
from app.main import app

client = TestClient(app)
app.dependency_overrides[get_db] = lambda: MagicMock()


def _fake_user(user_id=1):
    user = MagicMock()
    user.id = user_id
    return user


def _fake_favorite(user_id=1, location_id=2):
    from datetime import datetime, timezone

    fav = MagicMock()
    fav.id = 1
    fav.user_id = user_id
    fav.location_id = location_id
    fav.created_at = datetime.now(timezone.utc)
    return fav


def _authed():
    app.dependency_overrides[get_current_user] = lambda: _fake_user(user_id=1)


def _clear_auth():
    app.dependency_overrides.pop(get_current_user, None)


def test_create_favorite_requires_auth():
    _clear_auth()
    response = client.post("/favorites", json={"location_id": 2})
    assert response.status_code in (401, 403)


def test_create_favorite_uses_the_authenticated_users_id():
    _authed()
    with patch("app.routers.favorites.add_favorite", return_value=_fake_favorite()) as mock_add:
        response = client.post("/favorites", json={"location_id": 2})
    assert response.status_code == 201
    assert mock_add.call_args.kwargs["user_id"] == 1
    assert mock_add.call_args.kwargs["location_id"] == 2
    _clear_auth()


def test_read_favorites_returns_the_users_list():
    _authed()
    with patch("app.routers.favorites.list_favorites", return_value=[_fake_favorite()]):
        response = client.get("/favorites")
    assert response.status_code == 200
    assert len(response.json()) == 1
    _clear_auth()


def test_delete_favorite_returns_204():
    _authed()
    with patch("app.routers.favorites.remove_favorite") as mock_remove:
        response = client.delete("/favorites/2")
    assert response.status_code == 204
    assert mock_remove.call_args.kwargs["user_id"] == 1
    assert mock_remove.call_args.kwargs["location_id"] == 2
    _clear_auth()