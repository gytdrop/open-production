"""Tests for ShotPlanningAgent — Appendix K.1-ext of open-production-plan.md."""
from __future__ import annotations

import pytest

from agents.shot_planner import ShotPlanningAgent


@pytest.fixture
def planner():
    return ShotPlanningAgent()


# ---------------------------------------------------------------------------
# Basic structure
# ---------------------------------------------------------------------------

def test_shot_planner_returns_shots_key(planner):
    """run() always returns a 'shots' list."""
    out = planner.run({"scene_id": "scene_0001", "scene_type": "dialogue"})
    assert "shots" in out
    assert isinstance(out["shots"], list)
    assert len(out["shots"]) > 0


def test_shot_planner_shots_have_required_fields(planner):
    """Every shot dict must have shot_id, scene_id, label, intent, duration_sec."""
    out = planner.run({"scene_id": "scene_0002", "scene_type": "action"})
    for shot in out["shots"]:
        assert "shot_id" in shot
        assert "scene_id" in shot
        assert "label" in shot
        assert "intent" in shot
        assert "duration_sec" in shot


def test_shot_planner_shot_id_format(planner):
    """Every shot_id must start with 'shot_'."""
    out = planner.run({"scene_id": "scene_0003", "scene_type": "default"})
    for shot in out["shots"]:
        assert shot["shot_id"].startswith("shot_"), (
            f"shot_id {shot['shot_id']!r} does not start with 'shot_'"
        )


def test_shot_planner_scene_id_echoed(planner):
    """Output scene_id must match the input scene_id."""
    out = planner.run({"scene_id": "scene_0004", "scene_type": "montage"})
    assert out["scene_id"] == "scene_0004"
    for shot in out["shots"]:
        assert shot["scene_id"] == "scene_0004"


# ---------------------------------------------------------------------------
# Scene-type routing
# ---------------------------------------------------------------------------

def test_shot_planner_action_scene_type(planner):
    """'action' scene_type resolves to the action template (5 shots)."""
    out = planner.run({"scene_id": "scene_act1", "scene_type": "action"})
    assert out["scene_type"] == "action"
    assert len(out["shots"]) == 5


def test_shot_planner_dialogue_scene_type(planner):
    """'dialogue' scene_type resolves to the dialogue template (5 shots)."""
    out = planner.run({"scene_id": "scene_dlg1", "scene_type": "dialogue"})
    assert out["scene_type"] == "dialogue"
    assert len(out["shots"]) == 5


def test_shot_planner_montage_scene_type(planner):
    """'montage' scene_type resolves to the montage template (5 shots)."""
    out = planner.run({"scene_id": "scene_mon1", "scene_type": "montage"})
    assert out["scene_type"] == "montage"
    assert len(out["shots"]) == 5


def test_shot_planner_default_scene_type(planner):
    """Unknown scene_type falls back to 'default' template (3 shots)."""
    out = planner.run({"scene_id": "scene_def1", "scene_type": "mystery"})
    assert out["scene_type"] == "default"
    assert len(out["shots"]) == 3


def test_shot_planner_scene_type_keyword_matching(planner):
    """scene_type keyword matching is case-insensitive."""
    out = planner.run({"scene_id": "scene_kw1", "scene_type": "Dialogue scene"})
    assert out["scene_type"] == "dialogue"


# ---------------------------------------------------------------------------
# num_shots override
# ---------------------------------------------------------------------------

def test_shot_planner_num_shots_truncates(planner):
    """num_shots=2 returns only 2 shots from the action template."""
    out = planner.run({
        "scene_id": "scene_tr1",
        "scene_type": "action",
        "num_shots": 2,
    })
    assert len(out["shots"]) == 2
    assert out["coverage_warning"] is None


def test_shot_planner_num_shots_clamped_to_ten(planner):
    """num_shots > 10 is clamped to 10 with a coverage_warning.

    The dialogue template has 5 shots, so the result is min(10, 5) = 5.
    The important invariant is that the coverage_warning is emitted and
    the returned count never exceeds 10.
    """
    out = planner.run({
        "scene_id": "scene_cl1",
        "scene_type": "dialogue",
        "num_shots": 99,
    })
    assert len(out["shots"]) <= 10
    assert out["coverage_warning"] is not None
    assert "10" in out["coverage_warning"]


def test_shot_planner_num_shots_invalid_defaults(planner):
    """num_shots < 1 triggers warning and falls back to template length."""
    out = planner.run({
        "scene_id": "scene_iv1",
        "scene_type": "default",
        "num_shots": 0,
    })
    assert len(out["shots"]) == 3   # default template has 3
    assert out["coverage_warning"] is not None


# ---------------------------------------------------------------------------
# Safe on empty / minimal input
# ---------------------------------------------------------------------------

def test_shot_planner_safe_on_empty_input(planner):
    """run({}) must return shots and never raise (K.11 rule 4)."""
    out = planner.run({})
    assert "shots" in out
    assert len(out["shots"]) >= 1


def test_shot_planner_duration_is_positive(planner):
    """All duration_sec values must be positive floats."""
    out = planner.run({"scene_id": "scene_dur1", "scene_type": "action"})
    for shot in out["shots"]:
        assert isinstance(shot["duration_sec"], (int, float))
        assert shot["duration_sec"] > 0
