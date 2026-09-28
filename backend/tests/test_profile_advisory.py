import pytest

from tests.conftest import make_user

CHILD_ASTHMA = {"age_group": "child", "asthma": True}
HEALTHY_ADULT = {"age_group": "adult"}


def test_profile_requires_auth(client):
    for method in ("get", "post", "put", "delete"):
        r = getattr(client, method)("/profile") if method in ("get", "delete") else getattr(client, method)("/profile", json={})
        assert r.status_code == 401, method


def test_no_profile_yet_is_404(client, user):
    assert client.get("/profile", headers=user).status_code == 404


def test_profile_create_read_update(client, user):
    r = client.post("/profile", json=CHILD_ASTHMA, headers=user)
    assert r.status_code == 201
    assert r.json()["asthma"] is True and r.json()["age_group"] == "child"

    assert client.get("/profile", headers=user).json()["asthma"] is True

    r = client.put("/profile", json={"age_group": "adult", "heart_condition": True}, headers=user)
    assert r.status_code == 200
    body = r.json()
    assert body["age_group"] == "adult" and body["heart_condition"] is True
    assert body["asthma"] is False  # PUT replaces


def test_profile_is_entirely_optional(client, user):
    r = client.post("/profile", json={}, headers=user)
    assert r.status_code == 201
    assert r.json()["age_group"] is None and r.json()["asthma"] is False


def test_profile_duplicate_post_and_put_before_post(client, user):
    assert client.put("/profile", json={}, headers=user).status_code == 404
    client.post("/profile", json={}, headers=user)
    assert client.post("/profile", json={}, headers=user).status_code == 409


def test_profile_validation(client, user):
    assert client.post("/profile", json={"age_group": "toddler"}, headers=user).status_code == 422
    assert client.post("/profile", json={"activity_level": "extreme"}, headers=user).status_code == 422


def test_profile_delete(client, user):
    client.post("/profile", json=CHILD_ASTHMA, headers=user)
    assert client.delete("/profile", headers=user).status_code == 204
    assert client.get("/profile", headers=user).status_code == 404


def test_users_only_ever_see_their_own_profile(client, user, other_user):
    client.post("/profile", json=CHILD_ASTHMA, headers=user)
    # Other user has none -- and there's no field to address someone else's.
    assert client.get("/profile", headers=other_user).status_code == 404
    # A smuggled user_id in the body is ignored, not honoured.
    r = client.post("/profile", json={**HEALTHY_ADULT, "user_id": 1}, headers=other_user)
    assert r.status_code == 201
    assert client.get("/profile", headers=user).json()["age_group"] == "child"
    assert client.get("/profile", headers=other_user).json()["age_group"] == "adult"


# --- advisory -----------------------------------------------------------------


def advise(client, headers, location_id=1, **extra):
    return client.post("/advisory", json={"location_id": location_id, **extra}, headers=headers)


def test_guest_gets_the_general_advisory(client):
    r = client.post("/advisory", json={"location_id": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["personalized"] is False and body["reasons"] and body["disclaimer"]


def test_invalid_token_on_advisory_is_401_not_silently_a_guest(client):
    r = client.post("/advisory", json={"location_id": 1}, headers={"Authorization": "Bearer junk"})
    assert r.status_code == 401


def test_advisory_returns_recommendation_with_reasons(client, user):
    r = advise(client, user)
    assert r.status_code == 200
    body = r.json()
    assert body["aqi"] == 160 and body["aqi_category"] == "Unhealthy"
    assert body["recommendation"]
    assert len(body["reasons"]) >= 1
    assert all({"code", "message"} <= reason.keys() for reason in body["reasons"])
    assert "not medical advice" in body["disclaimer"]
    # honesty fields travel with the advice
    assert body["source"] == "waqi" and body["reliability_status"] == "official"
    assert body["recorded_at"]


def test_child_with_asthma_gets_higher_risk_than_healthy_adult_via_api(client):
    levels = ["low", "moderate", "high", "very_high", "severe"]
    child, _ = make_user(client, "child@example.com")
    adult, _ = make_user(client, "adult@example.com")
    client.post("/profile", json=CHILD_ASTHMA, headers=child)
    client.post("/profile", json=HEALTHY_ADULT, headers=adult)

    for location_id in (1,):
        c = advise(client, child, location_id).json()
        a = advise(client, adult, location_id).json()
        assert levels.index(c["risk_level"]) > levels.index(a["risk_level"])
        assert c["personalized"] is True and a["personalized"] is False
        assert any(r["code"] == "profile_asthma" for r in c["reasons"])
        assert not any(r["code"] == "profile_asthma" for r in a["reasons"])


def test_advisory_uses_the_callers_own_profile_only(client, user, other_user):
    client.post("/profile", json=CHILD_ASTHMA, headers=user)
    mine = advise(client, user).json()
    theirs = advise(client, other_user).json()  # no profile
    assert mine["risk_level"] != theirs["risk_level"]
    # Someone else's stored profile is never reachable: there's no user id
    # in the request, and other_user's answer is unaffected by user's profile.
    assert theirs["personalized"] is False


def test_what_if_profile_is_used_for_the_calculation_but_never_saved(client, user):
    levels = ["low", "moderate", "high", "very_high", "severe"]
    adult = advise(client, user, profile=HEALTHY_ADULT).json()
    child = advise(client, user, profile=CHILD_ASTHMA).json()
    assert levels.index(child["risk_level"]) > levels.index(adult["risk_level"])
    assert child["personalized"] is True
    # Nothing was persisted.
    assert client.get("/profile", headers=user).status_code == 404


def test_what_if_profile_works_for_guests_and_overrides_a_stored_profile(client, user):
    guest = client.post("/advisory", json={"location_id": 1, "profile": CHILD_ASTHMA}).json()
    assert guest["personalized"] is True
    client.post("/profile", json=CHILD_ASTHMA, headers=user)
    override = advise(client, user, profile=HEALTHY_ADULT).json()
    stored = advise(client, user).json()
    levels = ["low", "moderate", "high", "very_high", "severe"]
    assert levels.index(stored["risk_level"]) > levels.index(override["risk_level"])


def test_what_if_profile_is_validated(client):
    r = client.post("/advisory", json={"location_id": 1, "profile": {"age_group": "toddler"}})
    assert r.status_code == 422


def test_advisory_activity_and_exposure_options(client, user):
    base = advise(client, user).json()
    intense = advise(client, user, activity="high", prolonged_exposure=True).json()
    levels = ["low", "moderate", "high", "very_high", "severe"]
    assert levels.index(intense["risk_level"]) > levels.index(base["risk_level"])
    assert advise(client, user, activity="extreme").status_code == 422


def test_advisory_skips_readings_without_an_aqi(client, user):
    # Pulchowk's only reading has no AQI -> nothing to score, and we say so.
    r = advise(client, user, location_id=3)
    assert r.status_code == 404
    assert "AQI" in r.json()["detail"]


def test_advisory_unknown_location_and_no_readings(client, user):
    assert advise(client, user, location_id=999).status_code == 404
    assert advise(client, user, location_id=4).status_code == 404


@pytest.mark.parametrize("location_id,expected", [(1, "Unhealthy"), (2, "Good")])
def test_advisory_tracks_the_locations_air(client, user, location_id, expected):
    assert advise(client, user, location_id).json()["aqi_category"] == expected
