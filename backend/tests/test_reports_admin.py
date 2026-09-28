import io
from pathlib import Path

from app.config import get_settings
from tests.conftest import make_user

# Smallest valid-looking files (magic bytes are what the server checks).
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 64


def submit(client, headers, image=None, filename="photo.jpg", **fields):
    data = {"category": "dust", "location_id": "1", **fields}
    files = {"image": (filename, io.BytesIO(image), "image/jpeg")} if image is not None else None
    return client.post("/reports", data=data, files=files, headers=headers)


def uploaded_files():
    return list(Path(get_settings().upload_dir).glob("*"))


# --- submitting -------------------------------------------------------------------


def test_guest_can_report_and_it_is_always_anonymous(client, db):
    from app.models import PollutionReport

    r = client.post("/reports", data={"category": "dust", "location_id": "1"})
    assert r.status_code == 201
    assert db.query(PollutionReport).one().user_id is None


def test_report_with_a_bad_token_is_401_not_silently_a_guest(client):
    r = client.post(
        "/reports",
        data={"category": "dust", "location_id": "1"},
        headers={"Authorization": "Bearer junk"},
    )
    assert r.status_code == 401


def test_report_with_image_lands_unverified_and_is_publicly_listed(client, user):
    r = submit(client, user, image=JPEG, description="  Smoke near the road ", severity="high")
    assert r.status_code == 201
    body = r.json()
    assert body["verification_status"] == "unverified"
    assert body["description"] == "Smoke near the road"
    assert body["image_url"].startswith("/uploads/") and body["image_url"].endswith(".jpg")
    assert body["latitude"] == 27.693 and body["longitude"] == 85.281

    public = client.get("/reports").json()
    assert [p["id"] for p in public] == [body["id"]]


def test_uploaded_image_is_served_back(client, user):
    url = submit(client, user, image=PNG, filename="x.png").json()["image_url"]
    r = client.get(url)
    assert r.status_code == 200 and r.content == PNG


def test_public_reports_never_leak_the_submitter(client, user):
    headers, _ = make_user(client, "named@example.com", "Named Person")
    submit(client, headers)
    text = client.get("/reports").text
    assert "user_id" not in text and "Named Person" not in text and "named@example.com" not in text


def test_anonymous_report_is_stored_without_the_user(client, user, db):
    from app.models import PollutionReport

    submit(client, user, anonymous="true")
    submit(client, user)  # not anonymous
    reports = db.query(PollutionReport).order_by(PollutionReport.id).all()
    assert reports[0].user_id is None
    assert reports[1].user_id is not None


def test_report_pinned_by_coordinates_snaps_to_nearest_location(client, user):
    # Right next to Kirtipur (id 2)
    r = client.post(
        "/reports", data={"category": "dust", "latitude": "27.682", "longitude": "85.290"}, headers=user
    )
    assert r.status_code == 201
    assert r.json()["location_id"] == 2


def test_report_far_outside_the_valley_is_rejected(client, user):
    r = client.post("/reports", data={"category": "dust", "latitude": "40.0", "longitude": "-74.0"}, headers=user)
    assert r.status_code == 422


def test_report_location_validation(client, user):
    assert client.post("/reports", data={"category": "dust"}, headers=user).status_code == 422
    assert client.post("/reports", data={"category": "dust", "latitude": "27.7"}, headers=user).status_code == 422
    assert client.post("/reports", data={"category": "dust", "location_id": "999"}, headers=user).status_code == 404
    assert client.post("/reports", data={"category": "dust", "latitude": "95", "longitude": "85"}, headers=user).status_code == 422


def test_report_field_validation(client, user):
    assert submit(client, user, category="alien_invasion").status_code == 422
    assert submit(client, user, severity="apocalyptic").status_code == 422
    assert submit(client, user, description="x" * 2001).status_code == 422


def test_accepts_png_and_webp(client, user):
    assert submit(client, user, image=PNG, filename="a.png").status_code == 201
    assert submit(client, user, image=WEBP, filename="a.webp").status_code == 201


# --- upload safety ----------------------------------------------------------------


def test_upload_type_is_decided_by_content_not_filename_or_header(client, user):
    before = len(uploaded_files())
    # A script pretending to be a .jpg with an image/jpeg header.
    r = submit(client, user, image=b"<?php system($_GET['c']); ?>", filename="evil.jpg")
    assert r.status_code == 415
    assert len(uploaded_files()) == before  # nothing was written


def test_real_image_with_a_dangerous_filename_is_stored_under_a_safe_name(client, user):
    r = submit(client, user, image=JPEG, filename="../../../etc/passwd.php")
    assert r.status_code == 201
    name = r.json()["image_url"].removeprefix("/uploads/")
    assert "/" not in name and ".." not in name and name.endswith(".jpg")
    assert Path(get_settings().upload_dir, name).exists()


def test_oversized_upload_is_rejected(client, user):
    too_big = JPEG + b"\x00" * (get_settings().max_upload_mb * 1024 * 1024)
    before = len(uploaded_files())
    assert submit(client, user, image=too_big).status_code == 413
    assert len(uploaded_files()) == before


def test_empty_file_part_is_treated_as_no_image(client, user):
    r = client.post(
        "/reports",
        data={"category": "dust", "location_id": "1"},
        files={"image": ("", io.BytesIO(b""), "application/octet-stream")},
        headers=user,
    )
    assert r.status_code == 201 and r.json()["image_url"] is None


# --- public list ------------------------------------------------------------------


def test_public_list_filters_by_proximity(client, user):
    submit(client, user, location_id="1")  # Kalanki
    submit(client, user, location_id="4")  # Sankhu, ~19 km east
    near_kalanki = client.get("/reports", params={"lat": 27.693, "lng": 85.281, "radius_km": 3}).json()
    assert [r["location_id"] for r in near_kalanki] == [1]
    assert len(client.get("/reports").json()) == 2


def test_public_list_needs_both_coordinates(client):
    assert client.get("/reports", params={"lat": 27.7}).status_code == 422


# --- admin ------------------------------------------------------------------------


def test_every_admin_route_is_403_for_non_admins_and_401_for_guests(client, user):
    routes = [
        ("get", "/admin/reports"),
        ("patch", "/admin/reports/1"),
        ("get", "/admin/stats"),
        ("get", "/admin/audit-log"),
    ]
    for method, path in routes:
        kwargs = {"json": {"verification_status": "verified"}} if method == "patch" else {}
        assert getattr(client, method)(path, headers=user, **kwargs).status_code == 403, path
        assert getattr(client, method)(path, **kwargs).status_code == 401, path


def test_admin_moderates_a_report_from_unverified_to_verified(client, user, admin):
    report_id = submit(client, user).json()["id"]

    queue = client.get("/admin/reports", headers=admin).json()
    assert [r["id"] for r in queue] == [report_id]
    assert queue[0]["user_id"] is not None  # moderators can see the submitter

    r = client.patch(f"/admin/reports/{report_id}", json={"verification_status": "verified"}, headers=admin)
    assert r.status_code == 200 and r.json()["verification_status"] == "verified"

    assert client.get("/admin/reports", headers=admin).json() == []  # left the queue
    public = client.get("/reports").json()
    assert public[0]["id"] == report_id and public[0]["verification_status"] == "verified"


def test_rejected_and_flagged_reports_disappear_from_the_public_list(client, user, admin):
    rejected = submit(client, user).json()["id"]
    flagged = submit(client, user).json()["id"]
    kept = submit(client, user).json()["id"]
    client.patch(f"/admin/reports/{rejected}", json={"verification_status": "rejected"}, headers=admin)
    client.patch(f"/admin/reports/{flagged}", json={"verification_status": "flagged"}, headers=admin)
    assert [r["id"] for r in client.get("/reports").json()] == [kept]
    # ...but moderators can still find them.
    assert [r["id"] for r in client.get("/admin/reports", params={"status": "rejected"}, headers=admin).json()] == [rejected]


def test_moderation_validation(client, user, admin):
    report_id = submit(client, user).json()["id"]
    assert client.patch(f"/admin/reports/{report_id}", json={"verification_status": "deleted"}, headers=admin).status_code == 422
    assert client.patch("/admin/reports/999", json={"verification_status": "verified"}, headers=admin).status_code == 404


def test_admin_actions_are_audit_logged(client, user, admin):
    report_id = submit(client, user).json()["id"]
    client.patch(f"/admin/reports/{report_id}", json={"verification_status": "verified"}, headers=admin)
    client.patch(f"/admin/reports/{report_id}", json={"verification_status": "rejected"}, headers=admin)

    log = client.get("/admin/audit-log", headers=admin).json()
    assert [e["action"] for e in log] == ["report.rejected", "report.verified"]  # newest first
    assert log[0]["detail"] == "verified -> rejected"
    assert log[0]["target_type"] == "pollution_report" and log[0]["target_id"] == report_id
    assert log[0]["actor_id"] is not None


def test_admin_can_list_every_status_at_once(client, user, admin):
    ids = [submit(client, user).json()["id"] for _ in range(3)]
    client.patch(f"/admin/reports/{ids[0]}", json={"verification_status": "verified"}, headers=admin)
    client.patch(f"/admin/reports/{ids[1]}", json={"verification_status": "rejected"}, headers=admin)
    everything = client.get("/admin/reports", params={"status": "all"}, headers=admin).json()
    assert {r["id"] for r in everything} == set(ids)
    assert client.get("/admin/reports", params={"status": "bogus"}, headers=admin).status_code == 422


def test_admin_stats(client, user, admin):
    a = submit(client, user, category="dust").json()["id"]
    submit(client, user, category="dust")
    submit(client, user, category="industrial")
    client.patch(f"/admin/reports/{a}", json={"verification_status": "flagged"}, headers=admin)

    stats = client.get("/admin/stats", headers=admin).json()
    assert stats["users"] == 2  # the user + the admin
    assert stats["reports"] == 3
    assert stats["pending"] == 2 and stats["flagged"] == 1
    assert stats["reports_by_category"] == {"dust": 2, "industrial": 1}
