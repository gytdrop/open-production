"""Tests for AnimationDirectorAgent — Stage 18 (Animation) of open-production-plan.md."""
from __future__ import annotations

import pytest

from agents.animation_director import AnimationDirectorAgent


@pytest.fixture
def agent():
    return AnimationDirectorAgent()


# ---------------------------------------------------------------------------
# Basic contract
# ---------------------------------------------------------------------------

def test_returns_three_proposals(agent):
    """propose op always returns exactly 3 proposals."""
    out = agent.run({
        "scene_id": "scene_001",
        "scene_type": "action",
        "shot_sequence": [{"id": "shot-001"}, {"id": "shot-002"}],
        "edit_locked": True,
    })
    assert "proposals" in out
    assert len(out["proposals"]) == 3


def test_each_proposal_has_required_fields(agent):
    """Every proposal must have label, motion_primitives, transition_specs, motion_intensity, rationale."""
    out = agent.run({
        "scene_id": "scene_002",
        "scene_type": "dialogue",
        "shot_sequence": [{"id": "shot-001"}],
        "edit_locked": True,
    })
    for p in out["proposals"]:
        assert "label" in p, "missing 'label'"
        assert "motion_primitives" in p, "missing 'motion_primitives'"
        assert "transition_specs" in p, "missing 'transition_specs'"
        assert "motion_intensity" in p, "missing 'motion_intensity'"
        assert "rationale" in p, "missing 'rationale' (K.11 Rule 5)"


def test_safe_on_empty_input(agent):
    """run({}) must never raise and must return a valid dict (K.11 Rule 4)."""
    out = agent.run({})
    assert "proposals" in out
    assert len(out["proposals"]) == 3


# ---------------------------------------------------------------------------
# Scene-type routing
# ---------------------------------------------------------------------------

def test_action_scene_type_routes_to_high_intensity(agent):
    """Action scene types produce at least one high-intensity proposal."""
    out = agent.run({
        "scene_id": "scene_003",
        "scene_type": "chase action",
        "shot_sequence": [{"id": "s1"}, {"id": "s2"}],
    })
    intensities = [p["motion_intensity"] for p in out["proposals"]]
    assert "high" in intensities


def test_dialogue_scene_type_produces_low_or_none_intensity(agent):
    """Dialogue scene types produce only low or none intensity proposals."""
    out = agent.run({
        "scene_id": "scene_004",
        "scene_type": "intimate conversation",
        "shot_sequence": [{"id": "s1"}],
    })
    intensities = {p["motion_intensity"] for p in out["proposals"]}
    assert intensities.issubset({"low", "none"}), f"unexpected intensities: {intensities}"


def test_montage_scene_type_routes_to_montage_proposals(agent):
    """Montage scene type produces montage-style motion labels."""
    out = agent.run({
        "scene_id": "scene_005",
        "scene_type": "memory montage",
        "shot_sequence": [{"id": "s1"}, {"id": "s2"}, {"id": "s3"}],
    })
    labels = [p["label"].lower() for p in out["proposals"]]
    montage_keywords = {"montage", "match-cut", "drift", "jump"}
    assert any(any(k in lbl for k in montage_keywords) for lbl in labels)


def test_unknown_scene_type_falls_back_to_default(agent):
    """An unrecognised scene_type uses the default motion templates (3 proposals returned)."""
    out = agent.run({
        "scene_id": "scene_006",
        "scene_type": "some_unusual_value_xyz",
        "shot_sequence": [{"id": "s1"}],
    })
    assert len(out["proposals"]) == 3


# ---------------------------------------------------------------------------
# Proposals annotated with scene context
# ---------------------------------------------------------------------------

def test_proposals_annotated_with_scene_id(agent):
    """Each proposal carries the scene_id passed in the input."""
    out = agent.run({
        "scene_id": "scene_007",
        "scene_type": "default",
        "shot_sequence": [],
    })
    for p in out["proposals"]:
        assert p["scene_id"] == "scene_007"


def test_proposals_annotated_with_shot_count(agent):
    """Each proposal carries a shot_count equal to len(shot_sequence)."""
    shots = [{"id": f"shot-{i}"} for i in range(5)]
    out = agent.run({
        "scene_id": "scene_008",
        "scene_type": "action",
        "shot_sequence": shots,
    })
    for p in out["proposals"]:
        assert p["shot_count"] == 5


# ---------------------------------------------------------------------------
# needs_edit_lock flag
# ---------------------------------------------------------------------------

def test_needs_edit_lock_when_no_shots_and_no_edit_locked(agent):
    """needs_edit_lock is True when shot_sequence is empty and edit_locked is falsy."""
    out = agent.run({
        "scene_id": "scene_009",
        "scene_type": "action",
        "shot_sequence": [],
        "edit_locked": False,
    })
    assert out["needs_edit_lock"] is True


def test_no_needs_edit_lock_when_shots_provided(agent):
    """needs_edit_lock is False when at least one shot is in shot_sequence."""
    out = agent.run({
        "scene_id": "scene_010",
        "scene_type": "action",
        "shot_sequence": [{"id": "s1"}],
    })
    assert out["needs_edit_lock"] is False


def test_no_needs_edit_lock_when_edit_locked_true(agent):
    """needs_edit_lock is False when edit_locked=True even with no shots."""
    out = agent.run({
        "scene_id": "scene_011",
        "scene_type": "action",
        "shot_sequence": [],
        "edit_locked": True,
    })
    assert out["needs_edit_lock"] is False


# ---------------------------------------------------------------------------
# motion_locked gate
# ---------------------------------------------------------------------------

def test_propose_op_returns_motion_locked_false(agent):
    """The propose op (default) always returns motion_locked=False."""
    out = agent.run({
        "scene_id": "scene_012",
        "scene_type": "dialogue",
        "shot_sequence": [{"id": "s1"}],
    })
    assert out["motion_locked"] is False
    assert out["motion_spec"] is None


def test_lock_op_sets_motion_locked_true(agent):
    """The lock op returns motion_locked=True with the approved proposal embedded."""
    proposal = {
        "label": "Static Anchor with Slow Push",
        "motion_primitives": [{"movement": "slow_push_in"}],
        "transition_specs": [{"type": "cut", "duration_frames": 0, "rationale": "clean cut"}],
        "motion_intensity": "low",
        "rationale": "A barely perceptible push-in creates intimacy.",
    }
    out = agent.run({
        "op": "lock",
        "scene_id": "scene_013",
        "approved_proposal": proposal,
    })
    assert out["motion_locked"] is True
    assert out["motion_spec"] is not None
    assert out["motion_spec"]["locked"] is True
    assert out["motion_spec"]["label"] == "Static Anchor with Slow Push"
    assert out["proposals"] == []


def test_lock_op_embeds_scene_id_in_motion_spec(agent):
    """motion_spec from lock op always contains the scene_id."""
    out = agent.run({
        "op": "lock",
        "scene_id": "scene_014",
        "approved_proposal": {"rationale": "test", "label": "test proposal",
                               "motion_primitives": [], "transition_specs": [],
                               "motion_intensity": "none"},
    })
    assert out["motion_spec"]["scene_id"] == "scene_014"


# ---------------------------------------------------------------------------
# Transition specs shape
# ---------------------------------------------------------------------------

def test_transition_specs_have_rationale(agent):
    """Every transition_spec in every proposal must have a 'rationale' key."""
    out = agent.run({
        "scene_id": "scene_015",
        "scene_type": "action",
        "shot_sequence": [{"id": "s1"}],
    })
    for p in out["proposals"]:
        for ts in p["transition_specs"]:
            assert "rationale" in ts, f"transition_spec missing rationale: {ts}"


def test_transition_specs_have_type_and_duration(agent):
    """Every transition_spec must have 'type' and 'duration_frames' keys."""
    out = agent.run({
        "scene_id": "scene_016",
        "scene_type": "montage",
        "shot_sequence": [{"id": "s1"}, {"id": "s2"}],
    })
    for p in out["proposals"]:
        for ts in p["transition_specs"]:
            assert "type" in ts
            assert "duration_frames" in ts


# ---------------------------------------------------------------------------
# Template isolation — repeated calls do not mutate shared templates
# ---------------------------------------------------------------------------

def test_proposals_do_not_mutate_shared_templates(agent):
    """Two separate calls must not bleed scene_id or shot_count across runs."""
    out_a = agent.run({"scene_id": "scene_a", "scene_type": "action", "shot_sequence": [{"id": "s1"}]})
    out_b = agent.run({"scene_id": "scene_b", "scene_type": "action", "shot_sequence": []})
    for p in out_a["proposals"]:
        assert p["scene_id"] == "scene_a"
    for p in out_b["proposals"]:
        assert p["scene_id"] == "scene_b"
