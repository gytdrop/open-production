"""Tests for ColoristAgent — Appendix K.9 of open-production-plan.md."""
from __future__ import annotations

import pytest

from agents.colorist import ColoristAgent


@pytest.fixture
def colorist():
    return ColoristAgent()


def test_colorist_returns_three_proposals(colorist):
    """ColoristAgent always returns exactly 3 proposals."""
    out = colorist.run({
        "scene_id": "scene_001",
        "emotional_intent": "oppressive institutional cold",
        "reference_frames": [],
        "shots": [{"id": "shot-001"}, {"id": "shot-002"}],
    })
    assert "proposals" in out
    assert len(out["proposals"]) == 3


def test_colorist_proposals_have_required_fields(colorist):
    """Each proposal must have look_name, reference_frame, primary, creative, rationale."""
    out = colorist.run({
        "scene_id": "scene_002",
        "emotional_intent": "warm intimate reunion",
        "reference_frames": [],
        "shots": [],
    })
    for p in out["proposals"]:
        assert "look_name" in p
        assert "reference_frame" in p
        assert "primary" in p
        assert "creative" in p
        assert "rationale" in p


def test_colorist_cold_intent_routes_to_cold_grade(colorist):
    """A cold emotional intent should produce cold-grade proposals."""
    out = colorist.run({
        "scene_id": "scene_003",
        "emotional_intent": "clinical cold alienation",
        "reference_frames": [],
        "shots": [],
    })
    look_names = [p["look_name"].lower() for p in out["proposals"]]
    cold_keywords = {"cold", "teal", "bleach", "clinical", "institutional", "moonlight"}
    assert any(any(k in name for k in cold_keywords) for name in look_names)


def test_colorist_warm_intent_routes_to_warm_grade(colorist):
    """A warm emotional intent should produce warm-grade proposals."""
    out = colorist.run({
        "scene_id": "scene_004",
        "emotional_intent": "warm nostalgic hope",
        "reference_frames": [],
        "shots": [],
    })
    look_names = [p["look_name"].lower() for p in out["proposals"]]
    warm_keywords = {"golden", "warm", "candle", "amber", "memory"}
    assert any(any(k in name for k in warm_keywords) for name in look_names)


def test_colorist_no_emotional_promise_sets_needs_flag(colorist):
    """needs_emotional_promise is True when emotional_intent is empty."""
    out = colorist.run({
        "scene_id": "scene_005",
        "emotional_intent": "",
        "reference_frames": [],
        "shots": [],
    })
    assert out["needs_emotional_promise"] is True


def test_colorist_with_emotional_intent_clears_needs_flag(colorist):
    """needs_emotional_promise is False when emotional_intent is supplied."""
    out = colorist.run({
        "scene_id": "scene_006",
        "emotional_intent": "oppressive cold",
        "reference_frames": [],
        "shots": [],
    })
    assert out["needs_emotional_promise"] is False


def test_colorist_reference_frame_injected_into_first_proposal(colorist):
    """A supplied reference_frame URI replaces the first proposal's reference_frame."""
    uri = "https://example.com/ref-frame-001.jpg"
    out = colorist.run({
        "scene_id": "scene_007",
        "emotional_intent": "warm",
        "reference_frames": [uri],
        "shots": [],
    })
    assert out["proposals"][0]["reference_frame"] == uri


def test_colorist_shot_count_annotated_on_proposals(colorist):
    """Each proposal carries a shot_count annotation equal to len(shots)."""
    shots = [{"id": f"shot-{i}"} for i in range(4)]
    out = colorist.run({
        "scene_id": "scene_008",
        "emotional_intent": "neutral",
        "reference_frames": [],
        "shots": shots,
    })
    for p in out["proposals"]:
        assert p["shot_count"] == 4


def test_colorist_safe_on_empty_input(colorist):
    """run({}) must return a valid dict and never raise (K.11 rule 4)."""
    out = colorist.run({})
    assert "proposals" in out
    assert len(out["proposals"]) == 3
