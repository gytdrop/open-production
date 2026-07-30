"""Additional tests for ScriptAgent — Pipeline Stage 7 (import from canonical module).

These tests supplement test_script_agent.py with coverage of the draft/lock/validate
interface using the production-plan scene-structure contract.
"""
from __future__ import annotations

import pytest

from agents.script_agent import ScriptAgent


@pytest.fixture
def agent():
    return ScriptAgent()


# ── helpers ──────────────────────────────────────────────────────────────────

def _scene(scene_type: str = "Opening", description: str = "An opening scene.") -> dict:
    return {"scene_type": scene_type, "description": description}


def _script(*scene_types: str) -> dict:
    return {
        "scenes": [_scene(st) for st in scene_types],
        "script_locked": True,
    }


# ── draft operation ──────────────────────────────────────────────────────────

def test_draft_proposals_have_duration_hint(agent):
    """Each proposal should carry a duration_hint_sec indicating target scene length."""
    out = agent.run({"topic": "heist drama", "structure_locked": True})
    for p in out["proposals"]:
        assert "duration_hint_sec" in p
        assert p["duration_hint_sec"] > 0


def test_draft_proposals_have_sample_lines(agent):
    """Each proposal must have a non-empty sample_lines list."""
    out = agent.run({"topic": "a thriller", "structure_locked": True})
    for p in out["proposals"]:
        assert "sample_lines" in p
        assert len(p["sample_lines"]) >= 1


def test_draft_sample_lines_have_character_key(agent):
    """Every sample line must have at least a 'character' key."""
    out = agent.run({"topic": "drama", "structure_locked": True})
    for p in out["proposals"]:
        for line in p["sample_lines"]:
            assert "character" in line


def test_draft_structure_warning_absent_when_locked(agent):
    """No structure_warning in output when structure_locked=True."""
    out = agent.run({"topic": "comedy", "structure_locked": True})
    assert "structure_warning" not in out


def test_draft_structure_warning_present_when_not_locked(agent):
    """structure_warning present when structure_locked=False."""
    out = agent.run({"topic": "comedy", "structure_locked": False})
    assert "structure_warning" in out


def test_draft_genre_in_output(agent):
    """genre is echoed (or derived) in the output dict."""
    out = agent.run({"topic": "crime drama"})
    assert "genre" in out


def test_draft_act_label_in_output(agent):
    """act_label is echoed in the output dict."""
    out = agent.run({"topic": "drama", "act_label": "Setup"})
    assert out["act_label"] == "Setup"


# ── lock operation ───────────────────────────────────────────────────────────

def test_lock_scene_count_accurate(agent):
    """scene_count in the lock output matches the number of scenes supplied."""
    out = agent.run({"operation": "lock", "script": _script("Scene A", "Scene B", "Scene C")})
    assert out["script_locked"] is True
    assert out["scene_count"] == 3


def test_lock_mentions_downstream_in_rationale(agent):
    """Lock rationale references downstream agents or confirms lock event."""
    out = agent.run({"operation": "lock", "script": _script("Opening", "Climax")})
    assert any(k in out["rationale"] for k in ("locked", "approved", "proceed", "Script"))


def test_lock_fails_with_no_script_key(agent):
    """lock with no 'script' key must return script_locked=False."""
    out = agent.run({"operation": "lock"})
    assert out["script_locked"] is False


# ── validate operation ───────────────────────────────────────────────────────

def test_validate_reports_unlocked_issue(agent):
    """validate detects script_locked=False and adds an issue."""
    script = _script("Opening", "Middle")
    script["script_locked"] = False
    out = agent.run({"operation": "validate", "script": script})
    assert out["valid"] is False
    assert any("script_locked" in i for i in out["issues"])


def test_validate_reports_no_script_issue(agent):
    """validate with None/empty script reports at least one issue."""
    out = agent.run({"operation": "validate", "script": None})
    assert out["valid"] is False
    assert len(out["issues"]) >= 1


def test_validate_reports_empty_scenes_issue(agent):
    """validate detects a script with no scenes."""
    out = agent.run({
        "operation": "validate",
        "script": {"scenes": [], "script_locked": True},
    })
    assert out["valid"] is False


# ── package import ───────────────────────────────────────────────────────────

def test_script_agent_accessible_from_agents_package():
    """ScriptAgent must be importable from the agents package."""
    from agents import ScriptAgent as SA  # noqa: PLC0415
    assert SA is ScriptAgent
