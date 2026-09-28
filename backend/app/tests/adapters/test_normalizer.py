from datetime import datetime, timezone

import pytest

from app.adapters.normalizer import NormalizationError, normalize_reading

_UTC_NOW = datetime.now(timezone.utc)


def _base(**overrides):
    fields = {
        "aqi": None,
        "owm_aqi_index": None,
        "source": "waqi",
        "reliability_status": "official",
        "recorded_at": _UTC_NOW,
        "fetched_at": _UTC_NOW,
    }
    fields.update(overrides)
    return fields


def test_valid_waqi_reading_passes():
    reading = normalize_reading(_base(aqi=121, source="waqi", reliability_status="official"))
    assert reading["aqi"] == 121


def test_valid_openweathermap_reading_passes():
    reading = normalize_reading(
        _base(owm_aqi_index=4, source="openweathermap", reliability_status="modelled")
    )
    assert reading["owm_aqi_index"] == 4


def test_both_aqi_and_owm_index_set_raises():
    """The core scale-safety rule: these two scales must never coexist."""
    with pytest.raises(NormalizationError):
        normalize_reading(_base(aqi=121, owm_aqi_index=4, source="waqi"))


def test_openweathermap_setting_aqi_raises():
    with pytest.raises(NormalizationError):
        normalize_reading(_base(aqi=121, source="openweathermap", reliability_status="modelled"))


def test_openaq_setting_aqi_raises():
    with pytest.raises(NormalizationError):
        normalize_reading(_base(aqi=50, source="openaq", reliability_status="sensor"))


def test_unknown_source_raises():
    with pytest.raises(NormalizationError):
        normalize_reading(_base(source="made_up_source"))


def test_unknown_reliability_raises():
    with pytest.raises(NormalizationError):
        normalize_reading(_base(reliability_status="made_up"))


def test_invalid_owm_index_range_raises():
    with pytest.raises(NormalizationError):
        normalize_reading(_base(owm_aqi_index=9, source="openweathermap", reliability_status="modelled"))


def test_naive_datetime_raises():
    with pytest.raises(NormalizationError):
        normalize_reading(_base(recorded_at=datetime(2026, 9, 19, 12, 0)))  # no tzinfo


def test_openaq_reading_gets_a_computed_aqi_from_pm25():
    """The real bug this closes: an OpenAQ reading with elevated PM2.5 but
    no `aqi` must not pass through as `aqi: None` (which the frontend
    then displays as 0 / "Good") -- normalize_reading() computes a real
    one from the concentration OpenAQ actually gave us."""
    reading = normalize_reading(
        _base(aqi=None, source="openaq", reliability_status="sensor", pm25=40.0, pm10=None)
    )
    assert reading["aqi"] is not None
    assert reading["aqi"] > 100  # 40 ug/m3 PM2.5 is Unhealthy for Sensitive Groups
    assert reading["main_pollutant"] == "pm25"


def test_openaq_reading_with_no_pollutants_stays_null_not_zero():
    """No pm25/pm10 at all -- nothing to compute from, so `aqi` must stay
    None rather than becoming a fabricated 0."""
    reading = normalize_reading(
        _base(aqi=None, source="openaq", reliability_status="sensor", pm25=None, pm10=None)
    )
    assert reading["aqi"] is None
    assert reading.get("main_pollutant") is None