from dataclasses import dataclass

import pytest

from app.services.advisory_engine import (
    AdvisoryError,
    generate_advisory,
    get_aqi_category,
)


@dataclass
class FakeProfile:
    age_group: str | None = None
    asthma: bool = False
    respiratory_condition: bool = False
    heart_condition: bool = False
    pregnancy_status: bool = False
    outdoor_worker: bool = False
    activity_level: str | None = None


@pytest.mark.parametrize(
    "aqi,expected_category,expected_severity",
    [
        (0, "Good", 1),
        (50, "Good", 1),
        (51, "Moderate", 2),
        (100, "Moderate", 2),
        (101, "Unhealthy for Sensitive Groups", 3),
        (150, "Unhealthy for Sensitive Groups", 3),
        (151, "Unhealthy", 4),
        (200, "Unhealthy", 4),
        (201, "Very Unhealthy", 5),
        (300, "Very Unhealthy", 5),
        (301, "Hazardous", 6),
        (500, "Hazardous", 6),
    ],
)
def test_get_aqi_category_boundaries(aqi, expected_category, expected_severity):
    category, severity = get_aqi_category(aqi)
    assert category == expected_category
    assert severity == expected_severity


def test_get_aqi_category_none_raises():
    with pytest.raises(AdvisoryError):
        get_aqi_category(None)


def test_get_aqi_category_out_of_range_raises():
    with pytest.raises(AdvisoryError):
        get_aqi_category(501)
    with pytest.raises(AdvisoryError):
        get_aqi_category(-1)


def test_generate_advisory_no_profile_gives_base_recommendation_only():
    advisory = generate_advisory(30)
    assert advisory.aqi_category == "Good"
    assert len(advisory.recommendations) == 1


def test_generate_advisory_asthma_profile_adds_guidance_at_moderate():
    profile = FakeProfile(asthma=True)
    advisory = generate_advisory(75, profile)  # Moderate, severity 2
    assert advisory.aqi_category == "Moderate"
    assert len(advisory.recommendations) == 2  # base + asthma rule kicks in at severity 2


def test_generate_advisory_asthma_profile_no_extra_guidance_at_good():
    profile = FakeProfile(asthma=True)
    advisory = generate_advisory(20)  # Good, severity 1 -- below asthma's min_severity of 2
    assert len(advisory.recommendations) == 1


def test_generate_advisory_multiple_conditions_stack():
    profile = FakeProfile(asthma=True, heart_condition=True, pregnancy_status=True)
    advisory = generate_advisory(180, profile)  # Unhealthy, severity 4
    assert len(advisory.recommendations) == 5


def test_generate_advisory_child_age_group():
    profile = FakeProfile(age_group="child")
    advisory = generate_advisory(180, profile)  # Unhealthy, severity 4 >= child's min_severity of 3
    assert any("Children" in r for r in advisory.recommendations)


def test_generate_advisory_elderly_not_triggered_below_threshold():
    profile = FakeProfile(age_group="elderly")
    advisory = generate_advisory(60)  # Moderate, severity 2 -- below elderly's min_severity of 3
    assert not any("Older adults" in r for r in advisory.recommendations)


def test_generate_advisory_null_aqi_raises():
    with pytest.raises(AdvisoryError):
        generate_advisory(None)
