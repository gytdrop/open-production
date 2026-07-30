"""Tests for ReviewerAgent — Appendix J of open-production-plan.md."""
from __future__ import annotations

import pytest

from agents.reviewer import BLOCKING_THRESHOLD, WARN_THRESHOLD, ReviewerAgent


@pytest.fixture
def reviewer():
    return ReviewerAgent()


@pytest.fixture
def clean_result():
    """A generation result that passes all checks."""
    return {
        "shot_id": "shot-001",
        "attributes": ["red_scarf", "silver_locket", "dark_coat"],
        "quality_score": 0.90,
        "metadata": {"framing": "medium", "mood": "neutral", "color_temp_k": 5600},
    }


@pytest.fixture
def production_with_contract():
    """A minimal production state with one character that has a ConsistencyContract."""
    return {
        "state": "DRAFT",
        "intent": {"topic": "Test topic", "tone": "neutral"},
        "creative_direction": "advocate",
        "characters": [
            {
                "id": "char-elena",
                "name": "Elena",
                "consistency_contract": {
                    "required_attributes": ["red_scarf", "silver_locket"],
                    "prohibited_attributes": [],
                    "variance_tolerance": 0.15,
                },
            }
        ],
    }


# ---------------------------------------------------------------------------
# Test 1: clean result → pass
# ---------------------------------------------------------------------------

def test_reviewer_pass_on_clean_result(reviewer, clean_result, production_with_contract):
    """A result satisfying all contracts returns verdict='pass' and blocking=False."""
    out = reviewer.run({
        "shot_id": "shot-001",
        "generation_result": clean_result,
        "production": production_with_contract,
    })
    assert out["verdict"] == "pass"
    assert out["blocking"] is False
    assert out["score"] >= WARN_THRESHOLD


# ---------------------------------------------------------------------------
# Test 2: missing required attribute → fail + blocking
# ---------------------------------------------------------------------------

def test_reviewer_fail_on_missing_required_attribute(reviewer, production_with_contract):
    """A generation missing a required_attribute returns verdict='fail' and blocking=True."""
    bad_result = {
        "attributes": ["silver_locket"],  # red_scarf missing
        "quality_score": 0.85,
        "metadata": {},
    }
    out = reviewer.run({
        "shot_id": "shot-002",
        "generation_result": bad_result,
        "production": production_with_contract,
    })
    assert out["verdict"] == "fail"
    assert out["blocking"] is True
    cc_checks = [c for c in out["checks"] if c["check_type"] == "consistency_contract"]
    assert any(c["result"] == "fail" for c in cc_checks)
    assert any("red_scarf" in c["detail"] for c in cc_checks)


# ---------------------------------------------------------------------------
# Test 3: low quality score → warn
# ---------------------------------------------------------------------------

def test_reviewer_warn_on_low_quality(reviewer):
    """A generation with a mediocre quality_score (0.50) returns warn but not blocking."""
    result = {"attributes": [], "quality_score": 0.50, "metadata": {}}
    production = {"state": "DRAFT", "characters": []}
    out = reviewer.run({
        "shot_id": "shot-003",
        "generation_result": result,
        "production": production,
        "check_types": ["technical_quality"],
    })
    assert out["verdict"] == "warn"
    assert out["blocking"] is False
    assert out["score"] < WARN_THRESHOLD


# ---------------------------------------------------------------------------
# Test 4: very low quality score → fail + blocking
# ---------------------------------------------------------------------------

def test_reviewer_fail_on_very_low_quality(reviewer):
    """A generation with quality_score < 0.40 is blocking."""
    result = {"attributes": [], "quality_score": 0.30, "metadata": {}}
    production = {"state": "DRAFT", "characters": []}
    out = reviewer.run({
        "generation_result": result,
        "production": production,
        "check_types": ["technical_quality"],
    })
    assert out["verdict"] == "fail"
    assert out["blocking"] is True


# ---------------------------------------------------------------------------
# Test 5: empty contract → skip + pass
# ---------------------------------------------------------------------------

def test_reviewer_pass_with_no_contracts(reviewer, clean_result):
    """Production with no ConsistencyContracts on characters passes automatically."""
    production = {
        "state": "DRAFT",
        "characters": [{"id": "char-x", "name": "X"}],  # no consistency_contract key
    }
    out = reviewer.run({
        "generation_result": clean_result,
        "production": production,
        "check_types": ["consistency_contract"],
    })
    assert out["verdict"] == "pass"
    assert out["blocking"] is False


# ---------------------------------------------------------------------------
# Test 6: wrong production state → stage_gate fail
# ---------------------------------------------------------------------------

def test_reviewer_fail_on_bad_stage(reviewer, clean_result):
    """A production in state='ARCHIVED' blocks generation at the stage_gate check."""
    production = {"state": "ARCHIVED", "characters": []}
    out = reviewer.run({
        "generation_result": clean_result,
        "production": production,
        "check_types": ["stage_gate"],
    })
    assert out["verdict"] == "fail"
    assert out["blocking"] is True
    sg_checks = [c for c in out["checks"] if c["check_type"] == "stage_gate"]
    assert sg_checks[0]["result"] == "fail"


# ---------------------------------------------------------------------------
# Test 7: empty input never raises (K.11 rule 4)
# ---------------------------------------------------------------------------

def test_reviewer_safe_on_empty_input(reviewer):
    """run({}) must return a valid dict, never raise."""
    out = reviewer.run({})
    assert "verdict" in out
    assert "blocking" in out
    assert isinstance(out["checks"], list)
