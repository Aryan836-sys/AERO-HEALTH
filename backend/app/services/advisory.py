"""The explainable advisory engine -- pure logic, no database, no HTTP.

Design: the rules are *data* (the tables below), and `evaluate_advisory`
only walks them. Every rule that changes the outcome appends a human-readable
reason, so the result is always defensible: "why is this HIGH for me?" is
answered by `result.reasons`, never by a black box.

How the level is built:
  1. Base score from the AQI category alone (what a healthy adult faces).
  2. Sensitivity points from the profile (asthma, child, ...) raise it --
     but only once AQI is above "Good", and capped so the label stays sane.
  3. Exposure (intense activity, outdoor work, long time outside) raises it
     by one more step, but only once AQI reaches Unhealthy-for-Sensitive.
  4. Clamp to the top level.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.services.aqi import aqi_category

DISCLAIMER = (
    "This is general guidance based on air-quality data, not medical advice. "
    "If you have a health condition or symptoms, follow your doctor's advice."
)

LEVELS = ["low", "moderate", "high", "very_high", "severe"]

# Rule table 1: base score per AQI category, for a healthy adult.
BASE_SCORE = {
    "Good": 0,
    "Moderate": 0,
    "Unhealthy for Sensitive Groups": 1,
    "Unhealthy": 2,
    "Very Unhealthy": 3,
    "Hazardous": 4,
}

# Rule table 2: recommendation per level.
RECOMMENDATIONS = {
    "low": "Air quality is acceptable. Normal outdoor activity is fine.",
    "moderate": (
        "Consider shorter or lighter outdoor activity, and watch for symptoms "
        "such as coughing or shortness of breath."
    ),
    "high": (
        "Reduce prolonged or intense outdoor activity. Prefer indoor spaces "
        "and consider wearing a well-fitted N95/FFP2 mask outdoors."
    ),
    "very_high": (
        "Avoid outdoor exertion. Stay indoors with windows closed if you can, "
        "and wear an N95/FFP2 mask if you must go out."
    ),
    "severe": (
        "Stay indoors. Avoid all outdoor activity, keep windows closed, and "
        "seek medical help if you have trouble breathing."
    ),
}

# Rule table 3: profile factors that make the same air riskier.
# code -> (sensitivity points, explanation)
SENSITIVITY = {
    "asthma": (1, "Your profile includes asthma, which makes polluted air riskier for you."),
    "respiratory_condition": (
        1,
        "Your profile includes a respiratory condition, which makes polluted air riskier for you.",
    ),
    "heart_condition": (
        1,
        "Your profile includes a heart condition, which makes polluted air riskier for you.",
    ),
    "child": (1, "Children breathe faster and their lungs are still developing."),
    "elderly": (1, "Older adults are more sensitive to air pollution."),
    "pregnancy": (1, "Pregnancy increases sensitivity to air pollution."),
}

# Rule table 4: extra, group-specific advice appended to the recommendation.
GROUP_TIPS = {
    "asthma": "Keep your quick-relief inhaler with you.",
    "respiratory_condition": "Follow your usual respiratory care plan.",
    "heart_condition": "Stop and rest if you feel chest discomfort or unusual fatigue.",
    "child": "Keep children's outdoor play short and indoors where possible.",
    "elderly": "Avoid strenuous outdoor tasks.",
    "pregnancy": "Limit time near heavy traffic and smoke.",
}

# Sensitivity can add at most this many levels, by AQI band.
MAX_SENSITIVITY_BONUS_MODERATE = 1  # AQI 51-100: only "unusually sensitive" people
MAX_SENSITIVITY_BONUS = 2  # AQI 101+
EXPOSURE_BONUS = 1
EXPOSURE_MIN_AQI = 101
STALE_AFTER_HOURS = 3


@dataclass
class ReadingInput:
    aqi: int
    main_pollutant: str | None
    recorded_at: datetime


@dataclass
class ProfileInput:
    age_group: str | None = None
    asthma: bool = False
    respiratory_condition: bool = False
    heart_condition: bool = False
    pregnancy_status: bool = False
    outdoor_worker: bool = False
    activity_level: str | None = None


@dataclass
class Reason:
    code: str
    message: str


@dataclass
class AdvisoryResult:
    aqi: int
    aqi_category: str
    risk_level: str
    recommendation: str
    reasons: list[Reason] = field(default_factory=list)
    disclaimer: str = DISCLAIMER
    personalized: bool = False


def _sensitivity_factors(profile: ProfileInput | None) -> list[str]:
    if profile is None:
        return []
    factors = []
    if profile.asthma:
        factors.append("asthma")
    if profile.respiratory_condition:
        factors.append("respiratory_condition")
    if profile.heart_condition:
        factors.append("heart_condition")
    if profile.age_group == "child":
        factors.append("child")
    if profile.age_group == "elderly":
        factors.append("elderly")
    if profile.pregnancy_status:
        factors.append("pregnancy")
    return factors


def evaluate_advisory(
    reading: ReadingInput,
    profile: ProfileInput | None = None,
    activity: str | None = None,
    prolonged_exposure: bool = False,
    now: datetime | None = None,
) -> AdvisoryResult:
    category = aqi_category(reading.aqi)
    reasons = [Reason("aqi_category", f"AQI is {reading.aqi} ({category}).")]

    if reading.main_pollutant:
        reasons.append(
            Reason(
                "main_pollutant",
                f"The dominant pollutant is {reading.main_pollutant}.",
            )
        )

    score = BASE_SCORE[category]
    factors = _sensitivity_factors(profile)

    # --- profile sensitivity --------------------------------------------
    if reading.aqi > 50 and factors:
        cap = (
            MAX_SENSITIVITY_BONUS_MODERATE
            if reading.aqi <= 100
            else MAX_SENSITIVITY_BONUS
        )
        points = sum(SENSITIVITY[f][0] for f in factors)
        bonus = min(points, cap)
        score += bonus
        for factor in factors:
            reasons.append(Reason(f"profile_{factor}", SENSITIVITY[factor][1]))
        if points > cap:
            reasons.append(
                Reason(
                    "sensitivity_capped",
                    "Several risk factors apply; the level is raised by at most "
                    f"{cap} step{'s' if cap != 1 else ''} at this AQI.",
                )
            )
    elif factors:
        reasons.append(
            Reason(
                "no_adjustment",
                "Air quality is Good, so your profile risk factors did not "
                "raise the level.",
            )
        )

    # --- exposure ---------------------------------------------------------
    effective_activity = activity or (profile.activity_level if profile else None)
    exposure = []
    if effective_activity == "high":
        exposure.append(("intense_activity", "You plan intense physical activity, which increases how much polluted air you breathe in."))
    if profile is not None and profile.outdoor_worker:
        exposure.append(("outdoor_worker", "You work outdoors, so your exposure is longer."))
    if prolonged_exposure:
        exposure.append(("prolonged_exposure", "You expect to be outside for a long time."))
    if exposure and reading.aqi >= EXPOSURE_MIN_AQI:
        score += EXPOSURE_BONUS
        reasons.extend(Reason(code, message) for code, message in exposure)

    # --- assemble -----------------------------------------------------------
    level = LEVELS[min(score, len(LEVELS) - 1)]
    recommendation = RECOMMENDATIONS[level]
    if level != "low":
        tips = [GROUP_TIPS[f] for f in factors]
        if tips:
            recommendation = f"{recommendation} {' '.join(tips)}"

    # Honesty caveat: an old reading may not reflect the air right now.
    current = now or datetime.now(timezone.utc)
    recorded = reading.recorded_at
    if recorded.tzinfo is None:
        recorded = recorded.replace(tzinfo=timezone.utc)
    age_hours = (current - recorded).total_seconds() / 3600
    if age_hours > STALE_AFTER_HOURS:
        reasons.append(
            Reason(
                "stale_reading",
                f"The latest reading is about {round(age_hours)} hours old, so "
                "current conditions may differ.",
            )
        )

    return AdvisoryResult(
        aqi=reading.aqi,
        aqi_category=category,
        risk_level=level,
        recommendation=recommendation,
        reasons=reasons,
        personalized=bool(factors) or bool(exposure),
    )
