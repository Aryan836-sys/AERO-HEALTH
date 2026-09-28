"""US EPA AQI categories -- the single place that maps a number to a label.

The bands are the EPA's; every place that shows or reasons about a category
(reading responses, the advisory engine) goes through `aqi_category`.
"""
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

CATEGORIES = [
    (50, "Good"),
    (100, "Moderate"),
    (150, "Unhealthy for Sensitive Groups"),
    (200, "Unhealthy"),
    (300, "Very Unhealthy"),
]
HAZARDOUS = "Hazardous"

# US EPA PM2.5 breakpoints (May 2024 revision): (conc_low, conc_high, aqi_low, aqi_high).
PM25_BREAKPOINTS = [
    (Decimal("0.0"), Decimal("9.0"), 0, 50),
    (Decimal("9.1"), Decimal("35.4"), 51, 100),
    (Decimal("35.5"), Decimal("55.4"), 101, 150),
    (Decimal("55.5"), Decimal("125.4"), 151, 200),
    (Decimal("125.5"), Decimal("225.4"), 201, 300),
    (Decimal("225.5"), Decimal("325.4"), 301, 500),
]


def pm25_to_aqi(pm25: float | None) -> int | None:
    """EPA AQI computed from a PM2.5 concentration in µg/m³ -- for sources
    (OpenAQ) that give raw concentrations, never an AQI. The result is a
    *computed* AQI, not one a source published; None for missing/negative input.
    """
    if pm25 is None or pm25 < 0:
        return None
    conc = Decimal(str(pm25)).quantize(Decimal("0.1"), rounding=ROUND_DOWN)
    for c_low, c_high, i_low, i_high in PM25_BREAKPOINTS:
        if conc <= c_high:
            index = (Decimal(i_high - i_low) / (c_high - c_low)) * (conc - c_low) + i_low
            return int(index.quantize(Decimal(1), rounding=ROUND_HALF_UP))
    return 500


def aqi_category(aqi: int | None) -> str | None:
    """The EPA category for `aqi`, or None when there is no AQI (e.g. a
    source that only gave raw concentrations) -- never guessed."""
    if aqi is None:
        return None
    for upper, name in CATEGORIES:
        if aqi <= upper:
            return name
    return HAZARDOUS
