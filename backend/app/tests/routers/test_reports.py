from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.dependencies import get_current_user_optional
from app.database import get_db
from app.main import app

client = TestClient(app)
app.dependency_overrides[get_db] = lambda: MagicMock()


def _fake_report(report_id=1, user_id=None, verification_status="unverified"):
    report = MagicMock()
    report.id = report_id
    report.user_id = user_id
    report.location_id = 2
    report.category = "waste_burning"
    report.description = "Smoke from a field being burned nearby."
    report.image_url = None
    report.severity = "moderate"
    report.verification_status = verification_status
    report.created_at = datetime.now(timezone.utc)
    return report


def test_anonymous_submission_is_allowed():
    """The model itself documents this as intentional -- a guest can
    submit a report, and it's stored with user_id=None."""
    app.dependency_overrides[get_current_user_optional] = lambda: None
    with patch("app.routers.reports.create_report", return_value=_fake_report(user_id=None)) as mock_create:
        response = client.post(
            "/reports",
            json={
                "location_id": 2,
                "category": "waste_burning",
                "description": "Smoke from a field being burned nearby.",
            },
        )
    assert response.status_code == 201
    assert mock_create.call_args.kwargs["user_id"] is None
    assert response.json()["verification_status"] == "unverified"
    app.dependency_overrides.pop(get_current_user_optional, None)


def test_logged_in_submission_attaches_the_users_id():
    fake_user = MagicMock()
    fake_user.id = 5
    app.dependency_overrides[get_current_user_optional] = lambda: fake_user
    with patch("app.routers.reports.create_report", return_value=_fake_report(user_id=5)) as mock_create:
        response = client.post(
            "/reports", json={"location_id": 2, "category": "dust"}
        )
    assert response.status_code == 201
    assert mock_create.call_args.kwargs["user_id"] == 5
    app.dependency_overrides.pop(get_current_user_optional, None)


def test_rejects_an_unknown_category():
    app.dependency_overrides[get_current_user_optional] = lambda: None
    response = client.post(
        "/reports", json={"location_id": 2, "category": "made_up_category"}
    )
    assert response.status_code == 422
    app.dependency_overrides.pop(get_current_user_optional, None)


def test_a_client_cannot_set_verification_status_on_create():
    """There's no verification_status field in ReportCreate at all --
    confirm the schema silently ignores an attempt to pass one rather
    than accepting a pre-verified report."""
    app.dependency_overrides[get_current_user_optional] = lambda: None
    with patch("app.routers.reports.create_report", return_value=_fake_report()) as mock_create:
        client.post(
            "/reports",
            json={
                "location_id": 2,
                "category": "dust",
                "verification_status": "verified",  # should be ignored
            },
        )
    assert "verification_status" not in mock_create.call_args.kwargs
    app.dependency_overrides.pop(get_current_user_optional, None)


def test_read_reports_supports_a_status_filter():
    with patch("app.routers.reports.list_reports", return_value=[_fake_report()]) as mock_list:
        response = client.get("/reports?verification_status=unverified")
    assert response.status_code == 200
    assert mock_list.call_args.kwargs["verification_status"] == "unverified"