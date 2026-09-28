import pytest

from app.adapters.epa_aqi import compute_aqi_and_dominant


# Reference points taken directly from EPA's published breakpoint tables --
# each is a band edge, where the AQI value is exact, not interpolated.
@pytest.mark.parametrize(
    "pm25,expected_aqi",
    [
        (0.0, 0),
        (9.0, 50),
        (9.1, 51),
        (35.4, 100),
        (35.5, 101),
        (125.4, 200),
        (225.5, 301),
        (325.4, 500),
    ],
)
def test_pm25_breakpoint_edges(pm25, expected_aqi):
    aqi, dominant = compute_aqi_and_dominant({"pm25": pm25, "pm10": None})
    assert aqi == expected_aqi
    assert dominant == "pm25"


@pytest.mark.parametrize(
    "pm10,expected_aqi",
    [
        (0, 0),
        (54, 50),
        (55, 51),
        (154, 100),
        (604, 500),
    ],
)
def test_pm10_breakpoint_edges(pm10, expected_aqi):
    aqi, dominant = compute_aqi_and_dominant({"pm25": None, "pm10": pm10})
    assert aqi == expected_aqi
    assert dominant == "pm10"


def test_picks_the_higher_sub_index_as_dominant():
    """PM10 of 54 -> AQI 50 ("Good"); PM2.5 of 40 -> AQI ~102 (USG). The
    dominant pollutant must be whichever one is actually worse, not just
    whichever key happens to be checked first."""
    aqi, dominant = compute_aqi_and_dominant({"pm25": 40, "pm10": 54})
    assert dominant == "pm25"
    assert aqi > 100


def test_neither_pollutant_present_returns_none_not_zero():
    """Missing data must stay None, never silently become 0 ('Good') --
    that would be exactly the misrepresentation this module exists to fix."""
    aqi, dominant = compute_aqi_and_dominant({"pm25": None, "pm10": None})
    assert aqi is None
    assert dominant is None


def test_concentration_above_top_band_caps_at_500():
    aqi, dominant = compute_aqi_and_dominant({"pm25": 1000.0, "pm10": None})
    assert aqi == 500


def test_negative_concentration_is_rejected_not_computed():
    """A negative concentration is a bad-data sentinel (see openaq.py's
    extract_reading), never a real reading -- must not produce a fake AQI."""
    aqi, dominant = compute_aqi_and_dominant({"pm25": -5.0, "pm10": None})
    assert aqi is None
    assert dominant is None