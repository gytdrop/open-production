"""Additional tests for StoryAgent — Pipeline Stage 6 (import from canonical module).

These tests supplement test_story_agent.py with outline/lock operation coverage
using the production-plan beat-sheet interface.
"""
from __future__ import annotations

import pytest

from agents.story_agent import StoryAgent


@pytest.fixture
def agent():
    return StoryAgent()


# ── propose operation ────────────────────────────────────────────────────────

def test_propose_each_act_has_beats(agent):
    """Every act in every proposal must contain a non-empty 'beats' list."""
    out = agent.run({"topic": "a documentary investigation"})
    for p in out["proposals"]:
        for act in p["acts"]:
            assert "beats" in act
            assert len(act["beats"]) >= 1


def test_propose_acts_have_act_number_and_label(agent):
    """Each act must have an 'act' integer and a 'label' string."""
    out = agent.run({"topic": "a thriller"})
    for p in out["proposals"]:
        for act in p["acts"]:
            assert "act" in act
            assert isinstance(act["act"], int)
            assert "label" in act
            assert str(act["label"]).strip()


def test_propose_rationale_is_nonempty_string(agent):
    """Each proposal rationale must be a non-empty string (K.11 Rule 5)."""
    out = agent.run({"topic": "climate change"})
    for p in out["proposals"]:
        assert isinstance(p["rationale"], str)
        assert len(p["rationale"]) > 0


def test_propose_dramatic_register_includes_resolution_act(agent):
    """Dramatic structures should include an act labelled 'Resolution' or 'Convergence'."""
    out = agent.run({"topic": "thriller drama action"})
    all_labels = [
        act["label"]
        for p in out["proposals"]
        for act in p["acts"]
    ]
    resolution_keywords = ("Resolution", "Convergence", "Synthesis", "After", "Analysis")
    assert any(k in " ".join(all_labels) for k in resolution_keywords)


def test_propose_informational_register_has_solution_or_outcome(agent):
    """Informational structures should include an act about solutions or outcomes."""
    out = agent.run({"topic": "how renewable energy research works"})
    all_labels = [
        act["label"]
        for p in out["proposals"]
        for act in p["acts"]
    ]
    assert any(k in " ".join(all_labels) for k in ("Solution", "After", "Analysis", "Journey"))


# ── lock operation ───────────────────────────────────────────────────────────

def test_lock_structure_name_echoed_in_output(agent):
    """The locked structure_name must match what was sent in chosen_structure."""
    out = agent.run({
        "operation": "lock",
        "chosen_structure": {
            "structure_name": "Non-Linear Parallel",
            "acts": [{"act": 1, "label": "Present Thread", "description": "x"}],
        },
    })
    assert out["structure_name"] == "Non-Linear Parallel"


def test_lock_rationale_mentions_lock_confirmation(agent):
    """Rationale must mention the locking event (downstream agents may now proceed)."""
    out = agent.run({
        "operation": "lock",
        "chosen_structure": {
            "structure_name": "Problem–Solution Arc",
            "acts": [
                {"act": 1, "label": "Problem", "description": "p"},
                {"act": 2, "label": "Context", "description": "c"},
                {"act": 3, "label": "Solution", "description": "s"},
            ],
        },
    })
    assert out["structure_locked"] is True
    assert any(k in out["rationale"] for k in ("locked", "approved", "proceed"))


# ── validate operation ───────────────────────────────────────────────────────

def test_validate_reports_single_issue_for_no_structure(agent):
    """validate with no story_structure should report at least one issue."""
    out = agent.run({"operation": "validate", "story_structure": None})
    assert out["valid"] is False
    assert len(out["issues"]) >= 1


def test_validate_structure_locked_false_when_unlocked(agent):
    """structure_locked in validate output is False when the structure isn't locked."""
    out = agent.run({
        "operation": "validate",
        "story_structure": {
            "structure_name": "Classical Three-Act",
            "acts": [{"act": 1, "label": "Setup"}],
            "structure_locked": False,
        },
    })
    assert out["structure_locked"] is False


# ── package import ───────────────────────────────────────────────────────────

def test_story_agent_accessible_from_agents_package():
    """StoryAgent must be importable from the agents package."""
    from agents import StoryAgent as SA  # noqa: PLC0415
    assert SA is StoryAgent
