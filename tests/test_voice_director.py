"""Tests for VoiceDirectorAgent — Appendix K.5 of open-production-plan.md."""
from __future__ import annotations

import pytest

from agents.voice_director import VoiceDirectorAgent


@pytest.fixture
def director():
    return VoiceDirectorAgent()


def test_voice_director_returns_direction_per_line(director):
    """One voice_direction entry is produced for each script line."""
    out = director.run({
        "character_id": "char_elena001",
        "script_lines": ["I don't know how much longer I can do this.", "Then stop."],
        "scene_mood": {"emotional_promise": "restrained grief", "locked": True},
        "character_brief": "Elena is exhausted and close to breaking.",
    })
    assert "voice_direction" in out
    assert len(out["voice_direction"]) == 2


def test_voice_director_entry_has_required_fields(director):
    """Every direction entry must have line, emotion, pace, emphasis, subtext."""
    out = director.run({
        "character_id": "char_001",
        "script_lines": ["We need to go. Now."],
        "scene_mood": {"emotional_promise": "fear"},
        "character_brief": "Under immediate threat.",
    })
    entry = out["voice_direction"][0]
    assert "line" in entry
    assert "emotion" in entry
    assert "pace" in entry
    assert "emphasis" in entry
    assert isinstance(entry["emphasis"], list)
    assert "subtext" in entry


def test_voice_director_line_preserved_verbatim(director):
    """The original script line text is preserved in the output entry."""
    line = "She's been gone for three years now."
    out = director.run({
        "character_id": "char_002",
        "script_lines": [line],
        "scene_mood": {"emotional_promise": "grief"},
        "character_brief": "Grieving.",
    })
    assert out["voice_direction"][0]["line"] == line


def test_voice_director_grief_mood_routes_correctly(director):
    """A grief emotional_promise should produce grief-specific emotion label."""
    out = director.run({
        "character_id": "char_003",
        "script_lines": ["This is all I have left."],
        "scene_mood": {"emotional_promise": "grief"},
        "character_brief": "",
    })
    emotion = out["voice_direction"][0]["emotion"]
    assert "grief" in emotion.lower()


def test_voice_director_no_lines_returns_voice_profile(director):
    """When no script lines are supplied, a voice_profile is proposed instead."""
    out = director.run({
        "character_id": "char_004",
        "script_lines": [],
        "character_brief": "Authority figure under pressure.",
        "scene_mood": {"emotional_promise": "cold authority"},
    })
    assert out["voice_direction"] == []
    assert out["voice_profile"] is not None
    assert "rationale" in out["voice_profile"]


def test_voice_director_safe_on_empty_input(director):
    """run({}) must return a valid dict and never raise (K.11 rule 4)."""
    out = director.run({})
    assert "voice_direction" in out
    assert isinstance(out["voice_direction"], list)


def test_voice_director_character_id_propagated(director):
    """character_id from input is present in the output."""
    out = director.run({
        "character_id": "char_test_id1",
        "script_lines": ["One line."],
        "scene_mood": {},
        "character_brief": "",
    })
    assert out["character_id"] == "char_test_id1"
