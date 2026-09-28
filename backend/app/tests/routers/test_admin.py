from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.dependencies import get_current_user
from app.database import get_db
from app.main import app

client = TestClient(app)
app.dependency_overrides[get_db] = lambda: MagicMock()


def _fake_user(user_id=1, role="registered"):
    user = MagicMock()
    user.id = user_id
    user.role = role
    return user


def _fake_report(report_id=1, verification_status="unverified"):
    report = MagicMock()
    report.id = report_id
    report.user_id = 2
    report.location_id = 1
    report.category = "dust"
    report.description = "test"
    report.image_url = None
    report.severity = "low"
    report.verification_status = verification_status
    report.created_at = datetime.now(timezone.utc)
    return report


def _as_admin():
    app.dependency_overrides[get_current_user] = lambda: _fake_user(role="admin")


def _as_regular_user():
    app.dependency_overrides[get_current_user] = lambda: _fake_user(role="registered")


def _clear_auth():
    app.dependency_overrides.pop(get_current_user, None)


def test_non_admin_cannot_view_the_moderation_queue():
    _as_regular_user()
    response = client.get("/admin/reports")
    assert response.status_code == 403
    _clear_auth()


def test_admin_can_view_the_moderation_queue():
    _as_admin()
    with patch("app.routers.admin.list_reports", return_value=[_fake_report()]) as mock_list:
        response = client.get("/admin/reports")
    assert response.status_code == 200
    assert len(response.json()) == 1
    # defaults to the unverified queue, not every report
    assert mock_list.call_args.kwargs["verification_status"] == "unverified"
    _clear_auth()


def test_non_admin_cannot_moderate_a_report():
    _as_regular_user()
    response = client.patch("/admin/reports/1", json={"verification_status": "verified"})
    assert response.status_code == 403
    _clear_auth()


def test_admin_can_verify_a_report_and_it_writes_an_audit_log_entry():
    _as_admin()
    with patch("app.routers.admin.update_report_status", return_value=_fake_report(verification_status="verified")), \
         patch("app.routers.admin.create_audit_log") as mock_audit:
        response = client.patch("/admin/reports/1", json={"verification_status": "verified"})
    assert response.status_code == 200
    assert response.json()["verification_status"] == "verified"
    assert mock_audit.call_args.kwargs["admin_user_id"] == 1
    assert mock_audit.call_args.kwargs["target_id"] == 1
    assert mock_audit.call_args.kwargs["action"] == "report_status_update"
    _clear_auth()


def test_moderating_a_nonexistent_report_returns_404():
    _as_admin()
    with patch("app.routers.admin.update_report_status", return_value=None), \
         patch("app.routers.admin.create_audit_log") as mock_audit:
        response = client.patch("/admin/reports/999", json={"verification_status": "verified"})
    assert response.status_code == 404
    # no audit entry for an action that never actually happened
    mock_audit.assert_not_called()
    _clear_auth()


def test_rejects_an_invalid_status_value():
    _as_admin()
    response = client.patch("/admin/reports/1", json={"verification_status": "not_a_real_status"})
    assert response.status_code == 422
    _clear_auth()


def test_non_admin_cannot_view_stats():
    _as_regular_user()
    response = client.get("/admin/stats")
    assert response.status_code == 403
    _clear_auth()


def test_admin_can_view_stats():
    _as_admin()
    fake_db = MagicMock()
    fake_db.query.return_value.count.return_value = 3
    fake_db.query.return_value.filter.return_value.count.return_value = 1
    app.dependency_overrides[get_db] = lambda: fake_db

    response = client.get("/admin/stats")
    assert response.status_code == 200
    body = response.json()
    assert "reports_by_status" in body
    assert set(body["reports_by_status"].keys()) == {"unverified", "verified", "rejected", "flagged"}

    app.dependency_overrides[get_db] = lambda: MagicMock()
    _clear_auth()


def test_non_admin_cannot_view_the_audit_log():
    _as_regular_user()
    response = client.get("/admin/audit-log")
    assert response.status_code == 403
    _clear_auth()


def test_admin_can_view_the_audit_log():
    _as_admin()
    fake_entry = MagicMock()
    fake_entry.id = 1
    fake_entry.admin_user_id = 1
    fake_entry.action = "report_status_update"
    fake_entry.target_type = "pollution_report"
    fake_entry.target_id = 1
    fake_entry.detail = "-> verified"
    fake_entry.created_at = datetime.now(timezone.utc)

    with patch("app.routers.admin.list_audit_logs", return_value=[fake_entry]):
        response = client.get("/admin/audit-log")
    assert response.status_code == 200
    assert len(response.json()) == 1
    _clear_auth()