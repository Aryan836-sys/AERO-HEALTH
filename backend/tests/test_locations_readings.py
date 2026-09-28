READING_HONESTY_FIELDS = {"source", "reliability_status", "recorded_at"}


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_every_route_group_is_in_openapi(client):
    paths = client.get("/openapi.json").json()["paths"]
    for prefix in ("/auth", "/locations", "/readings", "/profile", "/advisory",
                   "/favorites", "/alerts", "/reports", "/admin"):
        assert any(p.startswith(prefix) for p in paths), prefix


def test_list_locations_includes_latest_reading_or_null(client):
    r = client.get("/locations")
    assert r.status_code == 200
    by_name = {loc["area_name"]: loc for loc in r.json()}
    assert set(by_name) == {"Kalanki", "Kirtipur", "Pulchowk", "Sankhu"}

    kalanki = by_name["Kalanki"]
    assert kalanki["latitude"] == 27.693 and kalanki["longitude"] == 85.281
    assert kalanki["latest_reading"]["aqi"] == 160  # newest, not the older ones
    assert by_name["Sankhu"]["latest_reading"] is None  # no readings: null, not invented


def test_reading_carries_honesty_fields_and_category(client):
    reading = client.get("/locations/1").json()["latest_reading"]
    assert READING_HONESTY_FIELDS <= reading.keys()
    assert reading["source"] == "waqi"
    assert reading["reliability_status"] == "official"
    assert reading["aqi_category"] == "Unhealthy"


def test_reading_without_an_aqi_has_no_category_and_no_fake_value(client):
    reading = client.get("/locations/3").json()["latest_reading"]
    assert reading["aqi"] is None
    assert reading["aqi_category"] is None
    assert reading["pm25"] == 30.0


def test_get_one_location_and_404(client):
    assert client.get("/locations/2").json()["area_name"] == "Kirtipur"
    r = client.get("/locations/9999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Location not found"


def test_compare_returns_both_sides(client):
    r = client.get("/locations/compare", params={"a": 1, "b": 2})
    assert r.status_code == 200
    body = r.json()
    assert body["a"]["area_name"] == "Kalanki" and body["a"]["latest_reading"]["aqi"] == 160
    assert body["b"]["area_name"] == "Kirtipur" and body["b"]["latest_reading"]["aqi"] == 40


def test_compare_validation(client):
    assert client.get("/locations/compare", params={"a": 1, "b": 1}).status_code == 400
    assert client.get("/locations/compare", params={"a": 1, "b": 999}).status_code == 404
    assert client.get("/locations/compare", params={"a": 1}).status_code == 422


def test_readings_windows(client):
    counts = {}
    for window in ("24h", "7d", "30d"):
        r = client.get("/readings/1", params={"range": window})
        assert r.status_code == 200
        rows = r.json()
        counts[window] = len(rows)
        times = [row["recorded_at"] for row in rows]
        assert times == sorted(times)  # oldest first, chart-ready
        for row in rows:
            assert READING_HONESTY_FIELDS <= row.keys()
    # seeded at 0.5h, 2h, 30h, 8d ago
    assert counts == {"24h": 2, "7d": 3, "30d": 4}


def test_readings_default_range_is_24h(client):
    assert len(client.get("/readings/1").json()) == 2


def test_readings_bad_range_and_unknown_location(client):
    assert client.get("/readings/1", params={"range": "1y"}).status_code == 422
    assert client.get("/readings/999").status_code == 404


def test_readings_empty_window_is_an_empty_list(client):
    assert client.get("/readings/4").json() == []
