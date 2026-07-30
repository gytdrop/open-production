"""Tests for MusicComposerAgent — Appendix K.7 of open-production-plan.md."""
from __future__ import annotations

import pytest

from agents.music_composer import MusicComposerAgent


@pytest.fixture
def composer():
    return MusicComposerAgent()


def test_music_composer_returns_music_brief(composer):
    """MusicComposerAgent returns a music_brief dict."""
    out = composer.run({
        "scene_id": "scene_001",
        "narrative_function": "escalation",
        "scene_duration_sec": 45.0,
    })
    assert "music_brief" in out
    brief = out["music_brief"]
    assert "tempo_range" in brief
    assert "instrumentation" in brief
    assert "dynamic_arc" in brief
    assert "avoid" in brief
    assert "reference_tracks" in brief
    assert "cue_in" in brief
    assert "cue_out" in brief


def test_music_composer_escalation_brief_has_avoid_list(composer):
    """Escalation brief must specify sounds to avoid."""
    out = composer.run({
        "scene_id": "scene_002",
        "narrative_function": "escalation",
        "scene_duration_sec": 60.0,
    })
    assert isinstance(out["music_brief"]["avoid"], list)
    assert len(out["music_brief"]["avoid"]) > 0


def test_music_composer_resolution_uses_piano(composer):
    """Resolution briefs should reference piano or soft instrumentation."""
    out = composer.run({
        "scene_id": "scene_003",
        "narrative_function": "resolution",
        "scene_duration_sec": 30.0,
    })
    instrumentation = out["music_brief"]["instrumentation"].lower()
    assert "piano" in instrumentation or "cello" in instrumentation


def test_music_composer_flexible_duration_when_no_duration(composer):
    """flexible_duration is True when scene_duration_sec is not set."""
    out = composer.run({
        "scene_id": "scene_004",
        "narrative_function": "transition",
        "scene_duration_sec": 0,
    })
    assert out["music_brief"]["flexible_duration"] is True


def test_music_composer_fixed_duration_clears_flexible_flag(composer):
    """flexible_duration is False when a valid scene_duration_sec is provided."""
    out = composer.run({
        "scene_id": "scene_005",
        "narrative_function": "tension",
        "scene_duration_sec": 90.0,
    })
    assert out["music_brief"]["flexible_duration"] is False


def test_music_composer_scene_id_propagated(composer):
    """scene_id is present in the output."""
    out = composer.run({
        "scene_id": "scene_abc_001",
        "narrative_function": "default",
        "scene_duration_sec": 25.0,
    })
    assert out["scene_id"] == "scene_abc_001"


def test_music_composer_brief_has_rationale(composer):
    """music_brief must contain a rationale string."""
    out = composer.run({
        "scene_id": "scene_006",
        "narrative_function": "escalation",
        "scene_duration_sec": 40.0,
    })
    assert "rationale" in out["music_brief"]
    assert isinstance(out["music_brief"]["rationale"], str)


def test_music_composer_safe_on_empty_input(composer):
    """run({}) must return a valid dict and never raise (K.11 rule 4)."""
    out = composer.run({})
    assert "music_brief" in out
    assert "scene_id" in out
