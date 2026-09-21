"""Day 6: rule-based health advisories from an AQI value + optional health profile.

Categories and breakpoints are the real US EPA AQI scale (the same 0-500
scale stored in aqi_readings.aqi -- see that model's "Scale-safety rule").
Never runs on owm_aqi_index (OWM's different 1-5 scale) or a null aqi --
both raise, since an advisory needs a real EPA-scale number to mean anything.

`app.models.health_advisory.HealthAdvisory` documents this logic as
"optional to persist; may live in code" -- this lives in code. The model
stays available if the team later wants to move these rules into the DB
without an API contract change.
"""
from dataclasses import dataclass, field
from typing import Optional

# (max_aqi_inclusive, category, severity 1-6)
_AQI_BREAKPOINTS = [
    (50, "Good", 1),
    (100, "Moderate", 2),
    (150, "Unhealthy for Sensitive Groups", 3),
    (200, "Unhealthy", 4),
    (300, "Very Unhealthy", 5),
    (500, "Hazardous", 6),
]

_BASE_RECOMMENDATIONS = {
    "Good": "Air quality is satisfactory. Enjoy normal outdoor activities.",
    "Moderate": "Air quality is acceptable. Unusually sensitive people should "
    "consider reducing prolonged or heavy outdoor exertion.",
    "Unhealthy for Sensitive Groups": "Sensitive groups should reduce prolonged "
    "or heavy outdoor exertion. Everyone else can continue normal activities.",
    "Unhealthy": "Everyone should reduce prolonged or heavy outdoor exertion. "
    "Sensitive groups should avoid it.",
    "Very Unhealthy": "Everyone should avoid prolonged or heavy outdoor exertion. "
    "Sensitive groups should stay indoors.",
    "Hazardous": "Everyone should avoid all outdoor exertion. Remain indoors "
    "with windows closed if possible.",
}

# Extra guidance for a profile flag, keyed by the minimum severity it kicks in at.
_PROFILE_RULES = [
    ("asthma", 2, "Keep rescue medication accessible; watch for early symptoms."),
    ("asthma", 4, "Consider staying indoors and using an air purifier if available."),
    ("respiratory_condition", 2, "Monitor your breathing; limit exertion if symptoms appear."),
    ("respiratory_condition", 4, "Avoid outdoor exertion entirely; keep windows closed."),
    ("heart_condition", 3, "Avoid strenuous outdoor activity; watch for chest discomfort or unusual fatigue."),
    ("pregnancy_status", 3, "Limit time outdoors; prioritize well-ventilated indoor spaces."),
    ("outdoor_worker", 2, "Take more frequent indoor breaks during your shift."),
    ("outdoor_worker", 4, "Wear a properly fitted N95/KN95 mask if outdoor work cannot be postponed."),
]

_AGE_GROUP_RULES = [
    ("child", 3, "Children should limit vigorous outdoor play."),
    ("elderly", 3, "Older adults should limit prolonged outdoor activity."),
]


class AdvisoryError(Exception):
    """Raised when an advisory can't be generated from the given input."""


@dataclass
class Advisory:
    aqi: int
    aqi_category: str
    severity: int
    recommendations: list[str] = field(default_factory=list)


def get_aqi_category(aqi: int) -> tuple[str, int]:
    """(category, severity 1-6) for a real US EPA 0-500 aqi value."""
    if aqi is None:
        raise AdvisoryError("Cannot categorize a null aqi value.")
    if not (0 <= aqi <= 500):
        raise AdvisoryError(f"aqi out of the valid US EPA range (0-500): {aqi!r}")

    for max_inclusive, category, severity in _AQI_BREAKPOINTS:
        if aqi <= max_inclusive:
            return category, severity

    raise AdvisoryError(f"Unreachable: aqi {aqi} matched no breakpoint.")  # pragma: no cover


def generate_advisory(aqi: int, profile: Optional[object] = None) -> Advisory:
    """Build an Advisory for this aqi, tailored to `profile` if given.

    `profile` is expected to be a HealthProfile instance (or anything with
    the same boolean/str attributes) -- duck-typed rather than imported
    directly, so this stays usable in a unit test without a DB session.
    """
    category, severity = get_aqi_category(aqi)
    recommendations = [_BASE_RECOMMENDATIONS[category]]

    if profile is not None:
        for attr, min_severity, message in _PROFILE_RULES:
            if getattr(profile, attr, False) and severity >= min_severity:
                recommendations.append(message)

        age_group = getattr(profile, "age_group", None)
        for group, min_severity, message in _AGE_GROUP_RULES:
            if age_group == group and severity >= min_severity:
                recommendations.append(message)

    return Advisory(
        aqi=aqi, aqi_category=category, severity=severity, recommendations=recommendations
    )
