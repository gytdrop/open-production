"""Tests for ShotDesignerAgent — Appendix K.1 of open-production-plan.md."""
from __future__ import annotations

import pytest

from agents.shot_designer import ShotDesignerAgent


@pytest.fixture
def designer():
    return ShotDesignerAgent()


def test_shot_designer_returns_three_proposals(designer):
    """ShotDesignerAgent always returns exactly 3 proposals."""
    out = designer.run({"shot_id": "s1", "shot_intent": "tense confrontation"})
    assert "proposals" in out
    assert len(out["proposals"]) == 3


def test_shot_designer_proposals_have_required_fields(designer):
    """Each proposal must have label, rationale, camera, lighting, and risk."""
    out = designer.run({"shot_id": "s1", "shot_intent": "warm reunion scene"})
    for p in out["proposals"]:
        assert "label" in p
        assert "rationale" in p
        assert "camera" in p
        assert "lighting" in p
        assert "risk" in p


def test_shot_designer_camera_has_framing(designer):
    """Each camera spec must include a framing key."""
    out = designer.run({"shot_id": "s2", "shot_intent": "neutral dialogue"})
    for p in out["proposals"]:
        assert "framing" in p["camera"]


def test_shot_designer_safe_on_empty_input(designer):
    """run({}) must return 3 proposals, never raise (K.11 rule 4)."""
    out = designer.run({})
    assert len(out["proposals"]) == 3


def test_shot_designer_tense_intent_uses_tense_template(designer):
    """Tense intent should produce proposals suited for tense scenes."""
    out = designer.run({"shot_id": "s3", "shot_intent": "protagonist cornered by danger"})
    labels = [p["label"] for p in out["proposals"]]
    # At least one label should reference a high/dutch/low angle (tense template)
    tense_keywords = {"high", "dutch", "low", "surveillance"}
    assert any(any(k in lbl.lower() for k in tense_keywords) for lbl in labels)
