import pytest

from app.services.aqi import pm25_to_aqi


@pytest.mark.parametrize(
    "pm25, expected",
    [
        (0.0, 0),
        (9.0, 50),
        (9.1, 51),
        (12.0, 56),
        (35.4, 100),
        (35.5, 101),
        (55.4, 150),
        (55.5, 151),
        (125.4, 200),
        (125.5, 201),
        (225.4, 300),
        (225.5, 301),
        (325.4, 500),
        (900.0, 500),
    ],
)
def test_pm25_to_aqi_epa_breakpoints(pm25, expected):
    assert pm25_to_aqi(pm25) == expected


def test_pm25_to_aqi_truncates_to_one_decimal_per_epa():
    # 9.09 truncates to 9.0 (Good, 50), it must not round up into Moderate.
    assert pm25_to_aqi(9.09) == 50


@pytest.mark.parametrize("bad", [None, -0.999, -5])
def test_pm25_to_aqi_no_data_is_none(bad):
    assert pm25_to_aqi(bad) is None
