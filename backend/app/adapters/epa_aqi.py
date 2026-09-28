"""Day 6 follow-up: compute a real US EPA AQI from raw pollutant
concentrations, for sources that only give concentrations (OpenAQ), not a
ready-made AQI number.

Why this exists: without it, a reading with real elevated PM2.5 but no
`aqi` value gets displayed by the frontend as `aqi: 0` ("Good") --
see FrontendReading.from_reading()'s `aqi=reading.aqi if ... else 0`. That
silently misrepresents genuinely unhealthy air as clean. This module
closes that gap using the same EPA breakpoint method WAQI itself uses
internally, so a computed AQI here is consistent with what WAQI would
report for the same concentration.

Scope: PM2.5 and PM10 only, both already in µg/m³ -- the exact unit the
EPA breakpoint tables use, so no unit conversion is needed and no
conversion-error risk. O3/NO2/SO2/CO breakpoints are defined in ppb/ppm,
not µg/m³; converting those correctly needs each gas's molar mass and
adds real risk of a subtly wrong AQI (worse than not computing one), so
they're deliberately left out of AQI computation for now -- a documented
limitation, not an oversight. Their raw concentrations still pass through
to the `pollutants` fields untouched.

Breakpoints: EPA's 2024-revised PM2.5 table (effective May 2024) and the
unchanged PM10 table. Source: US EPA, "Technical Assistance Document for
the Reporting of Daily Air Quality" (2024 revision).
"""

# Each row: (conc_low, conc_high, aqi_low, aqi_high)
_PM25_BREAKPOINTS = [
    (0.0, 9.0, 0, 50),
    (9.1, 35.4, 51, 100),
    (35.5, 55.4, 101, 150),
    (55.5, 125.4, 151, 200),
    (125.5, 225.4, 201, 300),
    (225.5, 325.4, 301, 500),
]

_PM10_BREAKPOINTS = [
    (0, 54, 0, 50),
    (55, 154, 51, 100),
    (155, 254, 101, 150),
    (255, 354, 151, 200),
    (355, 424, 201, 300),
    (425, 604, 301, 500),
]

_TABLES = {"pm25": _PM25_BREAKPOINTS, "pm10": _PM10_BREAKPOINTS}


def _aqi_for_concentration(concentration: float, table: list[tuple[float, float, int, int]]) -> int | None:
    """Linear-interpolate within whichever breakpoint band the
    concentration falls in. Returns None if it's above the table's top
    band (off the EPA scale entirely) or negative (not a real reading)."""
    if concentration < 0:
        return None

    for conc_low, conc_high, aqi_low, aqi_high in table:
        if conc_low <= concentration <= conc_high:
            aqi = ((aqi_high - aqi_low) / (conc_high - conc_low)) * (concentration - conc_low) + aqi_low
            return round(aqi)

    top_conc_high = table[-1][1]
    if concentration > top_conc_high:
        return 500  # EPA convention: anything above the top band caps at 500 (Hazardous)

    return None


def compute_aqi_and_dominant(pollutants: dict[str, float | None]) -> tuple[int | None, str | None]:
    """Given a reading's pm25/pm10 concentrations (µg/m³), compute each
    pollutant's own AQI sub-index and return the highest one plus which
    pollutant produced it -- the same "dominant pollutant" convention
    WAQI and AirNow both use.

    Returns (None, None) if neither pollutant is present, so callers can
    tell "nothing to compute" apart from "computed and it's 0".
    """
    best_aqi: int | None = None
    best_pollutant: str | None = None

    for key, table in _TABLES.items():
        value = pollutants.get(key)
        if value is None:
            continue
        sub_index = _aqi_for_concentration(value, table)
        if sub_index is None:
            continue
        if best_aqi is None or sub_index > best_aqi:
            best_aqi = sub_index
            best_pollutant = key

    return best_aqi, best_pollutant