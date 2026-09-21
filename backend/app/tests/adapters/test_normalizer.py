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
