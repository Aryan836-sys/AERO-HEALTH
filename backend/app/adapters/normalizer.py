"""Day 5: cross-source validation, run on every reading before insert_reading().

Each adapter (waqi, openaq, openweather) already extracts its own
aqi_readings-shaped dict. This is the one shared checkpoint that enforces
the rules the model comments document, regardless of which adapter a
reading came from -- so a future bug in one adapter can't silently corrupt
the scale-safety guarantee:

- `aqi` (US EPA 0-500) and `owm_aqi_index` (OWM's own 1-5 index) must never
  both be set on the same reading, and must never be confused for each other.
- `source` must be one of the values models/aqi_reading.py documents.
- `reliability_status` must be one of the values it documents.
- `recorded_at`/`fetched_at` must be timezone-aware (naive datetimes silently
  become wrong the moment they cross a timezone boundary).
"""
from datetime import datetime
from typing import Any

_VALID_SOURCES = {"waqi", "openaq", "openweathermap", "community", "opendata_nepal_historical"}
_VALID_RELIABILITY = {"official", "sensor", "community", "modelled"}


class NormalizationError(Exception):
    """Raised when a reading violates the shared cross-source contract."""


def normalize_reading(fields: dict[str, Any]) -> dict[str, Any]:
    """Validate (not transform) an adapter's extracted fields.

    Returns the same dict unchanged if it's valid -- this never invents or
    corrects values, it only refuses to pass through a reading that would
    violate the scale-safety rule or is otherwise malformed.
    """
    source = fields.get("source")
    if source not in _VALID_SOURCES:
        raise NormalizationError(f"Unknown source: {source!r}")

    reliability = fields.get("reliability_status")
    if reliability not in _VALID_RELIABILITY:
        raise NormalizationError(f"Unknown reliability_status: {reliability!r}")

    aqi = fields.get("aqi")
    owm_index = fields.get("owm_aqi_index")

    if aqi is not None and owm_index is not None:
        raise NormalizationError(
            "A reading cannot have both `aqi` (US EPA 0-500) and "
            "`owm_aqi_index` (OWM 1-5) set -- scale-safety rule violation."
        )

    if source == "openweathermap" and aqi is not None:
        raise NormalizationError("openweathermap readings must never set `aqi` directly.")

    if source in ("openaq",) and aqi is not None:
        raise NormalizationError("openaq readings must never set `aqi` -- source gives concentrations only.")

    if owm_index is not None and owm_index not in (1, 2, 3, 4, 5):
        raise NormalizationError(f"owm_aqi_index out of range: {owm_index!r}")

    for key in ("recorded_at", "fetched_at"):
        value = fields.get(key)
        if not isinstance(value, datetime):
            raise NormalizationError(f"{key} must be a datetime, got {value!r}")
        if value.tzinfo is None:
            raise NormalizationError(f"{key} must be timezone-aware, got naive datetime {value!r}")

    return fields
