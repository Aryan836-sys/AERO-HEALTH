"""Pure tests for the advisory engine -- no DB, no HTTP."""
from datetime import datetime, timedelta, timezone

from app.services.advisory import (
    LEVELS,
    ProfileInput,
    ReadingInput,
    evaluate_advisory,
)

NOW = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)


def reading(aqi, pollutant="pm25", age_hours=0.5):
    return ReadingInput(aqi, pollutant, NOW - timedelta(hours=age_hours))


def run(aqi, profile=None, **kw):
    return evaluate_advisory(reading(aqi), profile, now=NOW, **kw)


def level_index(result):
    return LEVELS.index(result.risk_level)


CHILD_WITH_ASTHMA = ProfileInput(age_group="child", asthma=True)
HEALTHY_ADULT = ProfileInput(age_group="adult")


def test_child_with_asthma_is_higher_risk_than_healthy_adult_at_same_aqi():
    """The demo moment: identical air, different people, different advice."""
    for aqi in (110, 130, 160, 220):
        child = run(aqi, CHILD_WITH_ASTHMA)
        adult = run(aqi, HEALTHY_ADULT)
        assert level_index(child) > level_index(adult), aqi


def test_each_risk_factor_alone_raises_the_level_above_a_healthy_adult():
    factors = [
        ProfileInput(asthma=True),
        ProfileInput(respiratory_condition=True),
        ProfileInput(heart_condition=True),
        ProfileInput(pregnancy_status=True),
        ProfileInput(age_group="child"),
        ProfileInput(age_group="elderly"),
    ]
    baseline = level_index(run(130, HEALTHY_ADULT))
    for profile in factors:
        assert level_index(run(130, profile)) > baseline, profile


def test_reasons_are_always_present_and_explain_the_result():
    result = run(160, CHILD_WITH_ASTHMA)
    codes = [r.code for r in result.reasons]
    assert "aqi_category" in codes
    assert "profile_asthma" in codes
    assert "profile_child" in codes
    assert any("asthma" in r.message for r in result.reasons)
    assert any("160" in r.message and "Unhealthy" in r.message for r in result.reasons)


def test_main_pollutant_is_reported_as_a_reason():
    result = run(160)
    assert any(r.code == "main_pollutant" and "pm25" in r.message for r in result.reasons)


def test_no_profile_still_gives_a_recommendation_with_reasons():
    result = run(160, None)
    assert result.recommendation
    assert result.reasons
    assert result.personalized is False


def test_disclaimer_is_attached_to_every_result():
    for aqi in (10, 80, 130, 180, 250, 400):
        assert "not medical advice" in run(aqi).disclaimer


def test_good_air_stays_low_even_with_risk_factors_and_says_why():
    result = run(30, CHILD_WITH_ASTHMA)
    assert result.risk_level == "low"
    assert any(r.code == "no_adjustment" for r in result.reasons)


def test_level_never_decreases_as_aqi_rises_for_a_fixed_profile():
    for profile in (None, HEALTHY_ADULT, CHILD_WITH_ASTHMA):
        levels = [level_index(run(aqi, profile)) for aqi in range(0, 501, 10)]
        assert levels == sorted(levels)


def test_level_is_capped_at_the_top():
    worst = ProfileInput(
        age_group="child", asthma=True, heart_condition=True, outdoor_worker=True
    )
    result = run(500, worst, activity="high", prolonged_exposure=True)
    assert result.risk_level == LEVELS[-1]


def test_sensitivity_bonus_is_capped_and_explained():
    everything = ProfileInput(
        age_group="elderly", asthma=True, heart_condition=True, respiratory_condition=True
    )
    # USG base is 1; asthma+heart+respiratory+elderly is 4 points but capped at +2.
    result = run(130, everything)
    assert level_index(result) == 3
    assert any(r.code == "sensitivity_capped" for r in result.reasons)


def test_intense_activity_raises_level_once_air_is_unhealthy_for_sensitive():
    assert level_index(run(130, activity="high")) > level_index(run(130))
    # ...but not when the air is fine.
    assert level_index(run(40, activity="high")) == level_index(run(40))


def test_outdoor_worker_and_prolonged_exposure_add_reasons():
    profile = ProfileInput(outdoor_worker=True)
    result = run(130, profile, prolonged_exposure=True)
    codes = [r.code for r in result.reasons]
    assert "outdoor_worker" in codes
    assert "prolonged_exposure" in codes


def test_profile_activity_level_is_used_when_request_gives_none():
    result = run(130, ProfileInput(activity_level="high"))
    assert any(r.code == "intense_activity" for r in result.reasons)


def test_group_tips_are_added_for_present_factors():
    result = run(160, ProfileInput(asthma=True))
    assert "inhaler" in result.recommendation


def test_stale_reading_adds_a_caveat():
    old = evaluate_advisory(reading(120, age_hours=8), None, now=NOW)
    fresh = evaluate_advisory(reading(120, age_hours=1), None, now=NOW)
    assert any(r.code == "stale_reading" for r in old.reasons)
    assert not any(r.code == "stale_reading" for r in fresh.reasons)


def test_naive_recorded_at_is_treated_as_utc():
    naive = ReadingInput(120, "pm25", datetime(2026, 9, 18, 11, 0))
    result = evaluate_advisory(naive, None, now=NOW)
    assert result.aqi == 120
