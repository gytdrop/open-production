"""Tests for EnvironmentArtistAgent — Appendix K.4 of open-production-plan.md."""
from __future__ import annotations

import pytest

from agents.environment_artist import EnvironmentArtistAgent


@pytest.fixture
def artist():
    return EnvironmentArtistAgent()


def test_env_artist_returns_three_proposals_interior(artist):
    """create operation with interior type returns 3 proposals."""
    out = artist.run({
        "operation": "create",
        "location_name": "Elena's office",
        "location_type": "interior",
    })
    assert "proposals" in out
    assert len(out["proposals"]) == 3


def test_env_artist_returns_proposals_exterior(artist):
    """Exterior location type selects the exterior archetype set."""
    out = artist.run({
        "operation": "create",
        "location_name": "City street",
        "location_type": "exterior",
    })
    assert len(out["proposals"]) >= 1
    # Exterior proposals should mention outdoor characteristics
    combined = " ".join(str(p) for p in out["proposals"]).lower()
    assert any(w in combined for w in ("exterior", "natural", "sky", "urban", "landscape"))


def test_env_artist_proposals_have_required_fields(artist):
    """Each proposal must have visual_description, lighting_presets, and time_of_day_variants."""
    out = artist.run({"operation": "create", "location_type": "interior"})
    for p in out["proposals"]:
        assert "visual_description" in p
        assert "lighting_presets" in p
        assert "time_of_day_variants" in p


def test_env_artist_safe_on_empty_input(artist):
    """run({}) must return proposals and never raise (K.11 rule 4)."""
    out = artist.run({})
    assert "proposals" in out
    assert len(out["proposals"]) >= 1


def test_env_artist_review_pass_on_matching_contract(artist):
    """review operation passes when generation satisfies the contract."""
    out = artist.run({
        "operation": "review",
        "environment_id": "env-studio",
        "generation_result": {"attributes": ["warm_light", "interior_setting"]},
        "consistency_contract": {
            "subject_id": "env-studio",
            "required_attributes": ["warm_light"],
            "prohibited_attributes": [],
        },
    })
    assert out["consistent"] is True
    assert out["severity"] == "pass"


def test_env_artist_review_fail_on_missing_attribute(artist):
    """review operation fails when a required attribute is missing from the generation."""
    out = artist.run({
        "operation": "review",
        "environment_id": "env-rooftop",
        "generation_result": {"attributes": ["wind", "overcast"]},
        "consistency_contract": {
            "subject_id": "env-rooftop",
            "required_attributes": ["city_skyline", "overcast"],
            "prohibited_attributes": [],
        },
    })
    assert out["consistent"] is False
    assert out["severity"] == "fail"
    assert any("city_skyline" in issue for issue in out["issues"])


def test_env_artist_review_skip_when_no_contract(artist):
    """review with no contract returns pass and skip message."""
    out = artist.run({
        "operation": "review",
        "environment_id": "env-x",
        "generation_result": {"attributes": ["anything"]},
        "consistency_contract": {},
    })
    assert out["consistent"] is True
    assert out["severity"] == "pass"
