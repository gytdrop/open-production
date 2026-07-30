"""Tests for EditorAgent — Appendix K.8."""
from __future__ import annotations

from agents.editor import EditorAgent


_SHOTS = [
    {"id": "shot-001", "intent": "wide establishing"},
    {"id": "shot-002", "intent": "medium dialogue"},
    {"id": "shot-003", "intent": "close reaction"},
]


def test_editor_returns_three_proposals():
    agent = EditorAgent()
    out = agent.run({"scene_id": "sc1", "shots": _SHOTS,
                     "narrative_intent": "balanced coverage",
                     "target_duration_sec": 30.0})
    assert len(out["proposals"]) == 3


def test_editor_proposals_have_required_fields():
    agent = EditorAgent()
    out = agent.run({"shots": _SHOTS, "narrative_intent": "fast action",
                     "target_duration_sec": 15.0})
    for p in out["proposals"]:
        assert "label" in p
        assert "shot_sequence" in p
        assert "durations" in p
        assert "transitions" in p
        assert "rationale" in p
        assert "total_duration_sec" in p


def test_editor_transitions_count_is_shots_minus_one():
    agent = EditorAgent()
    out = agent.run({"shots": _SHOTS, "narrative_intent": "contemplative",
                     "target_duration_sec": 45.0})
    for p in out["proposals"]:
        n_shots = len(p["shot_sequence"])
        assert len(p["transitions"]) == n_shots - 1


def test_editor_coverage_warning_on_single_shot():
    agent = EditorAgent()
    out = agent.run({"scene_id": "sc2", "shots": [{"id": "shot-001"}],
                     "narrative_intent": "fast"})
    assert out["coverage_warning"] is not None
    assert "thin" in out["coverage_warning"].lower()


def test_editor_safe_on_empty_input():
    """run({}) must not raise (K.11 rule 4)."""
    agent = EditorAgent()
    out = agent.run({})
    assert "proposals" in out
