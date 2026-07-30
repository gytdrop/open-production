"""Tests for StoryboardArtistAgent — Appendix K.2."""
from __future__ import annotations

from agents.storyboard_artist import StoryboardArtistAgent


def test_output_has_all_required_keys():
    agent = StoryboardArtistAgent()
    out = agent.run({
        "shot_id": "s1",
        "camera": {"framing": "medium", "angle": "eye_level", "movement": "static"},
        "characters": [{"id": "char-001", "name": "Elena"}],
        "location": "the abandoned warehouse",
        "intent": "Elena discovers the hidden door.",
    })
    assert "composition_description" in out
    assert "blocking_diagram" in out
    assert "frame_elements" in out
    assert "negative_space" in out


def test_blocking_diagram_is_nonempty_string():
    agent = StoryboardArtistAgent()
    out = agent.run({
        "camera": {"framing": "wide"},
        "intent": "Wide establishing shot.",
    })
    assert isinstance(out["blocking_diagram"], str)
    assert len(out["blocking_diagram"]) > 10


def test_missing_camera_spec_flagged():
    """If camera spec is absent, missing_specs must be returned."""
    agent = StoryboardArtistAgent()
    out = agent.run({"intent": "character enters room"})
    assert "missing_specs" in out
    assert len(out["missing_specs"]) > 0


def test_safe_on_empty_input():
    """run({}) must not raise (K.11 rule 4)."""
    agent = StoryboardArtistAgent()
    out = agent.run({})
    assert "blocking_diagram" in out
