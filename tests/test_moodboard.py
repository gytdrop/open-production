"""Tests for MoodboardAgent — Pipeline Stage 4 of open-production-plan.md."""
from __future__ import annotations

import pytest

from agents.moodboard import MoodboardAgent


@pytest.fixture
def agent():
    return MoodboardAgent()


# ── assemble operation ───────────────────────────────────────────────────────

def test_assemble_returns_three_proposals(agent):
    """assemble operation always returns exactly 3 proposals."""
    out = agent.run({
        "operation": "assemble",
        "scene_id": "scene_0001",
        "style_tokens": ["warm_amber_palette", "soft_directional_light"],
        "emotional_promise": "quiet intimacy",
    })
    assert "proposals" in out
    assert len(out["proposals"]) == 3


def test_assemble_proposals_have_required_fields(agent):
    """Each proposal must have emotional_promise, tonal_palette, visual_motifs, rationale."""
    out = agent.run({
        "scene_id": "scene_0001",
        "style_tokens": ["flat_overcast_light"],
    })
    for p in out["proposals"]:
        assert "emotional_promise" in p
        assert "tonal_palette" in p
        assert isinstance(p["tonal_palette"], list)
        assert "visual_motifs" in p
        assert "rationale" in p


def test_assemble_dark_tokens_route_to_dark_family(agent):
    """Dark/shadow style tokens should produce dark-family moodboard proposals."""
    out = agent.run({
        "scene_id": "scene_0002",
        "style_tokens": ["deep_shadow", "cold_desaturated", "night_urban"],
    })
    promises = [p["emotional_promise"].lower() for p in out["proposals"]]
    dark_keywords = ("dread", "night", "grief", "shadow", "threatening", "oppressive", "silence")
    assert any(any(k in promise for k in dark_keywords) for promise in promises)


def test_assemble_warm_tokens_route_to_bright_family(agent):
    """Warm/golden style tokens should produce bright-family moodboard proposals."""
    out = agent.run({
        "scene_id": "scene_0003",
        "style_tokens": ["warm_amber_palette", "golden_hour"],
        "emotional_promise": "hope and vitality",
    })
    promises = [p["emotional_promise"].lower() for p in out["proposals"]]
    bright_keywords = ("vitality", "joy", "hope", "golden", "morning", "quiet")
    assert any(any(k in promise for k in bright_keywords) for promise in promises)


def test_assemble_no_tokens_sets_needs_style_tokens_flag(agent):
    """needs_style_tokens is True when no style_tokens are supplied."""
    out = agent.run({
        "scene_id": "scene_0004",
        "style_tokens": [],
    })
    assert out["needs_style_tokens"] is True


def test_assemble_with_tokens_clears_needs_style_tokens_flag(agent):
    """needs_style_tokens is False when style_tokens are supplied."""
    out = agent.run({
        "scene_id": "scene_0005",
        "style_tokens": ["warm_amber_palette"],
    })
    assert out["needs_style_tokens"] is False


def test_assemble_approved_references_injected_into_proposals(agent):
    """Approved reference URIs are attached to every proposal's references list."""
    uris = ["https://example.com/ref-001.jpg", "https://example.com/ref-002.jpg"]
    out = agent.run({
        "scene_id": "scene_0006",
        "style_tokens": ["flat_overcast_light"],
        "approved_references": uris,
    })
    for p in out["proposals"]:
        assert p["references"] == uris


def test_assemble_scene_id_in_proposals(agent):
    """Each proposal carries the scene_id from the input."""
    out = agent.run({
        "scene_id": "scene_0007",
        "style_tokens": ["natural_texture"],
    })
    for p in out["proposals"]:
        assert p["scene_id"] == "scene_0007"


def test_assemble_scene_id_in_root_output(agent):
    """scene_id is present at the top level of the output dict."""
    out = agent.run({"scene_id": "scene_0008", "style_tokens": ["a"]})
    assert out["scene_id"] == "scene_0008"


def test_assemble_safe_on_empty_input(agent):
    """run({}) must return valid proposals and never raise (K.11 rule 4)."""
    out = agent.run({})
    assert "proposals" in out
    assert len(out["proposals"]) == 3


# ── lock operation ───────────────────────────────────────────────────────────

def test_lock_returns_mood_spec_with_locked_true(agent):
    """lock operation returns a mood_spec dict with locked=True."""
    out = agent.run({
        "operation": "lock",
        "scene_id": "scene_0009",
        "chosen_proposal": {
            "emotional_promise": "Oppressive dread building to revelation",
            "tonal_palette": ["deep shadow", "desaturated cool"],
            "references": ["https://example.com/r1.jpg"],
        },
    })
    assert out["locked"] is True
    assert out["mood_spec"]["locked"] is True


def test_lock_mood_spec_carries_emotional_promise(agent):
    """The locked mood_spec preserves the emotional_promise from the chosen proposal."""
    out = agent.run({
        "operation": "lock",
        "scene_id": "scene_0010",
        "chosen_proposal": {
            "emotional_promise": "Vitality and forward movement",
            "tonal_palette": ["warm amber"],
            "references": [],
        },
    })
    assert out["mood_spec"]["emotional_promise"] == "Vitality and forward movement"


def test_lock_mood_spec_carries_tonal_palette(agent):
    """The locked mood_spec preserves the tonal_palette from the chosen proposal."""
    out = agent.run({
        "operation": "lock",
        "scene_id": "scene_0011",
        "chosen_proposal": {
            "emotional_promise": "x",
            "tonal_palette": ["flat grey", "overcast diffusion"],
            "references": [],
        },
    })
    assert out["mood_spec"]["tonal_palette"] == ["flat grey", "overcast diffusion"]


def test_lock_scene_id_in_output(agent):
    """lock output includes the scene_id."""
    out = agent.run({
        "operation": "lock",
        "scene_id": "scene_0012",
        "chosen_proposal": {"emotional_promise": "x", "tonal_palette": [], "references": []},
    })
    assert out["scene_id"] == "scene_0012"


def test_lock_safe_on_missing_chosen_proposal(agent):
    """lock with no chosen_proposal returns locked=True with empty mood_spec fields."""
    out = agent.run({"operation": "lock", "scene_id": "scene_0013"})
    assert out["locked"] is True
    assert isinstance(out["mood_spec"], dict)


# ── scope contract ───────────────────────────────────────────────────────────

def test_writable_fields_declared():
    """WRITABLE_FIELDS must be declared on the class."""
    from agents.moodboard import MoodboardAgent
    assert MoodboardAgent.WRITABLE_FIELDS is not None
    assert "Scene.mood" in MoodboardAgent.WRITABLE_FIELDS
