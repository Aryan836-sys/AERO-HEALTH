from unittest.mock import MagicMock, patch
from urllib.error import URLError

import pytest

from app.adapters.openaq import OpenAqError
from app.adapters.reliability import (
    ReliabilityError,
    get_reading_with_fallback,
    nearest_openaq_location,
    retry_with_backoff,
)
from app.adapters.waqi import WaqiFeedError


# ---- retry_with_backoff ----------------------------------------------------

def test_retry_with_backoff_returns_on_first_success():
    fn = MagicMock(return_value="ok")
    assert retry_with_backoff(fn, "arg") == "ok"
    fn.assert_called_once_with("arg")


def test_retry_with_backoff_retries_then_succeeds():
    fn = MagicMock(side_effect=[URLError("boom"), "ok"])
    with patch("app.adapters.reliability.time.sleep") as sleep:
        assert retry_with_backoff(fn, retries=2, base_delay_seconds=1.0) == "ok"
    assert fn.call_count == 2
    sleep.assert_called_once_with(1.0)  # first retry waits base_delay * 2**0


def test_retry_with_backoff_gives_up_after_exhausting_retries():
    fn = MagicMock(side_effect=URLError("still down"))
    with patch("app.adapters.reliability.time.sleep"):
        with pytest.raises(ReliabilityError):
            retry_with_backoff(fn, retries=2, base_delay_seconds=0.01)
    assert fn.call_count == 3  # initial attempt + 2 retries


def test_retry_with_backoff_does_not_retry_adapter_errors():
    """A WaqiFeedError means the *response* was bad, not the network -- a
    retry would just get the same bad response again, so it must not be
    swallowed and retried like a network failure."""
    fn = MagicMock(side_effect=WaqiFeedError("bad payload"))
    with pytest.raises(WaqiFeedError):
        retry_with_backoff(fn)
    fn.assert_called_once()


# ---- nearest_openaq_location ------------------------------------------------

def _fake_openaq_locations_response(results):
    mock_resp = MagicMock()
    mock_resp.__enter__.return_value.read.return_value = None
    return results


@patch("app.adapters.reliability.urlopen")
def test_nearest_openaq_location_picks_the_closest(mock_urlopen):
    import json
    import io

    payload = {
        "results": [
            {"id": 111, "coordinates": {"latitude": 27.9, "longitude": 85.9}},  # far
            {"id": 222, "coordinates": {"latitude": 27.701, "longitude": 85.301}},  # close
        ]
    }
    mock_urlopen.return_value.__enter__.return_value = io.BytesIO(
        json.dumps(payload).encode()
    )
    result = nearest_openaq_location(27.7, 85.3)
    assert result == "222"


@patch("app.adapters.reliability.urlopen")
def test_nearest_openaq_location_returns_none_when_empty(mock_urlopen):
    import json
    import io

    mock_urlopen.return_value.__enter__.return_value = io.BytesIO(
        json.dumps({"results": []}).encode()
    )
    assert nearest_openaq_location(27.7, 85.3) is None


# ---- get_reading_with_fallback ---------------------------------------------

def _mock_location():
    loc = MagicMock()
    loc.id = 1
    loc.source_station_id = "9285"
    # to_shape(loc.geometry) is patched separately below
    return loc


@patch("app.adapters.reliability.to_shape")
@patch("app.adapters.reliability.get_waqi_reading")
def test_fallback_uses_waqi_when_it_succeeds(mock_waqi, mock_to_shape):
    mock_to_shape.return_value = MagicMock(y=27.7, x=85.3)
    mock_waqi.return_value = {"aqi": 100, "source": "waqi"}

    result = get_reading_with_fallback(MagicMock(), _mock_location())

    assert result["tier"] == "waqi"
    assert result["fresh"] is True
    assert result["fields"]["aqi"] == 100


@patch("app.adapters.reliability.to_shape")
@patch("app.adapters.reliability.get_openaq_reading")
@patch("app.adapters.reliability.nearest_openaq_location")
@patch("app.adapters.reliability.get_waqi_reading")
def test_fallback_tries_openaq_when_waqi_fails(
    mock_waqi, mock_nearest, mock_openaq, mock_to_shape
):
    mock_to_shape.return_value = MagicMock(y=27.7, x=85.3)
    mock_waqi.side_effect = WaqiFeedError("can not connect")
    mock_nearest.return_value = "999"
    mock_openaq.return_value = {"aqi": None, "pm25": 30.0, "source": "openaq"}

    result = get_reading_with_fallback(MagicMock(), _mock_location())

    assert result["tier"] == "openaq"
    assert result["fresh"] is True
    assert result["fields"]["pm25"] == 30.0


@patch("app.adapters.reliability.get_latest_reading")
@patch("app.adapters.reliability.to_shape")
@patch("app.adapters.reliability.nearest_openaq_location")
@patch("app.adapters.reliability.get_waqi_reading")
def test_fallback_reuses_stale_cache_when_both_sources_fail(
    mock_waqi, mock_nearest, mock_to_shape, mock_get_latest
):
    mock_to_shape.return_value = MagicMock(y=27.7, x=85.3)
    mock_waqi.side_effect = WaqiFeedError("can not connect")
    mock_nearest.return_value = None  # no OpenAQ station nearby
    stale_reading = MagicMock()
    mock_get_latest.return_value = stale_reading

    result = get_reading_with_fallback(MagicMock(), _mock_location())

    assert result["tier"] == "stale_cache"
    assert result["fresh"] is False
    assert result["stale_reading"] is stale_reading


@patch("app.adapters.reliability.get_latest_reading")
@patch("app.adapters.reliability.to_shape")
@patch("app.adapters.reliability.nearest_openaq_location")
@patch("app.adapters.reliability.get_waqi_reading")
def test_fallback_reports_unavailable_when_nothing_works(
    mock_waqi, mock_nearest, mock_to_shape, mock_get_latest
):
    mock_to_shape.return_value = MagicMock(y=27.7, x=85.3)
    mock_waqi.side_effect = WaqiFeedError("can not connect")
    mock_nearest.return_value = None
    mock_get_latest.return_value = None  # nothing cached either

    result = get_reading_with_fallback(MagicMock(), _mock_location())

    assert result["tier"] == "unavailable"
    assert result["fresh"] is False
    assert result["stale_reading"] is None