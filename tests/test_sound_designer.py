"""Tests for SoundDesignerAgent — Appendix K.6 of open-production-plan.md."""
from __future__ import annotations

import pytest

from agents.sound_designer import SoundDesignerAgent


@pytest.fixture
def designer():
    return SoundDesignerAgent()


def test_sound_designer_returns_sound_palette(designer):
    """SoundDesignerAgent returns a sound_palette dict."""
    out = designer.run({
        "scene_id": "scene_001",
        "scene_mood": {"emotional_promise": "cold institutional", "locked": True},
        "location": "office interior",
        "shot_sequence": [{"id": "shot-001"}, {"id": "shot-002"}],
    })
    assert "sound_palette" in out
    palette = out["sound_palette"]
    assert "ambient" in palette
    assert "sfx" in palette
    assert "silence_intent" in palette
    assert "avoid" in palette


def test_sound_designer_sfx_count_matches_shots(designer):
    """SFX list length is capped by the number of shots."""
    shots = [{"id": f"shot-{i}"} for i in range(3)]
    out = designer.run({
        "scene_id": "scene_002",
        "scene_mood": {"emotional_promise": "warm", "locked": True},
        "location": "home interior",
        "shot_sequence": shots,
    })
    assert len(out["sound_palette"]["sfx"]) <= len(shots)


def test_sound_designer_unlocked_mood_sets_needs_flag(designer):
    """needs_mood_lock is True when scene_mood.locked is False or missing."""
    out = designer.run({
        "scene_id": "scene_003",
        "scene_mood": {"emotional_promise": "dramatic", "locked": False},
        "location": "exterior street",
        "shot_sequence": [],
    })
    assert out["needs_mood_lock"] is True


def test_sound_designer_locked_mood_clears_needs_flag(designer):
    """needs_mood_lock is False when scene_mood.locked is True."""
    out = designer.run({
        "scene_id": "scene_004",
        "scene_mood": {"emotional_promise": "dramatic", "locked": True},
        "location": "exterior alley",
        "shot_sequence": [{"id": "shot-x"}],
    })
    assert out["needs_mood_lock"] is False


def test_sound_designer_exterior_location_routing(designer):
    """Exterior location produces outdoor-appropriate ambient description."""
    out = designer.run({
        "scene_id": "scene_005",
        "scene_mood": {"emotional_promise": "urban tension", "locked": True},
        "location": "exterior street",
        "shot_sequence": [],
    })
    ambient = out["sound_palette"]["ambient"].lower()
    # Exterior ambient should reference outdoor/traffic sounds
    assert any(w in ambient for w in ("traffic", "wind", "outdoor", "crowd", "air"))


def test_sound_designer_palette_has_rationale(designer):
    """sound_palette must contain a rationale string."""
    out = designer.run({
        "scene_id": "scene_006",
        "scene_mood": {"emotional_promise": "warm", "locked": True},
        "location": "home interior",
        "shot_sequence": [],
    })
    assert "rationale" in out["sound_palette"]
    assert isinstance(out["sound_palette"]["rationale"], str)


def test_sound_designer_safe_on_empty_input(designer):
    """run({}) must return a valid dict and never raise (K.11 rule 4)."""
    out = designer.run({})
    assert "sound_palette" in out
    assert "needs_mood_lock" in out
