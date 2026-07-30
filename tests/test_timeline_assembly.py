"""Tests for timeline assembly — EditorAgent proposals → ProductionService.commit_editor_proposal().

Covers the gap identified in row 12 of the architecture audit:
  Timeline.scene_order + Shot.duration_sec proposals are committed back into
  Production.timeline via commit_editor_proposal(), completing the
  timeline-assembly automation.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from agents.editor import EditorAgent
from src.schema.production_document import IntentDocument, Timeline
from src.service.production_service import ProductionService


_SHOTS = [
    {"id": "shot-001", "intent": "wide establishing"},
    {"id": "shot-002", "intent": "medium dialogue"},
    {"id": "shot-003", "intent": "close reaction"},
]


@pytest.fixture
def svc(tmp_path: Path) -> ProductionService:
    return ProductionService(storage_dir=tmp_path)


@pytest.fixture
def prod(svc: ProductionService):
    return svc.init("Timeline Test Film")


# ---------------------------------------------------------------------------
# Timeline schema
# ---------------------------------------------------------------------------

def test_timeline_has_shot_durations_and_total():
    t = Timeline(
        scene_order=["sc1"],
        shot_durations=[{"scene_id": "sc1", "shot_id": "s1", "duration_sec": 5.0}],
        total_duration_sec=5.0,
    )
    assert t.total_duration_sec == 5.0
    assert len(t.shot_durations) == 1


# ---------------------------------------------------------------------------
# commit_editor_proposal — basic wiring
# ---------------------------------------------------------------------------

def test_commit_editor_proposal_populates_timeline(svc, prod):
    agent = EditorAgent()
    out = agent.run({
        "scene_id": "sc1",
        "shots": _SHOTS,
        "narrative_intent": "balanced coverage",
        "target_duration_sec": 30.0,
    })
    proposal = out["proposals"][0]

    new_prod = svc.commit_editor_proposal(prod, proposal)

    assert new_prod.timeline is not None
    assert "sc1" in new_prod.timeline.scene_order


def test_commit_editor_proposal_sets_shot_durations(svc, prod):
    agent = EditorAgent()
    out = agent.run({
        "scene_id": "sc1",
        "shots": _SHOTS,
        "narrative_intent": "fast action",
        "target_duration_sec": 15.0,
    })
    proposal = out["proposals"][0]

    new_prod = svc.commit_editor_proposal(prod, proposal)

    tl = new_prod.timeline
    assert len(tl.shot_durations) == len(proposal["shot_sequence"])
    for entry in tl.shot_durations:
        assert "scene_id" in entry
        assert "shot_id" in entry
        assert "duration_sec" in entry
        assert entry["duration_sec"] > 0


def test_commit_editor_proposal_sets_total_duration(svc, prod):
    agent = EditorAgent()
    out = agent.run({
        "scene_id": "sc1",
        "shots": _SHOTS,
        "narrative_intent": "slow contemplative",
        "target_duration_sec": 45.0,
    })
    proposal = out["proposals"][0]

    new_prod = svc.commit_editor_proposal(prod, proposal)

    tl = new_prod.timeline
    expected = round(sum(e["duration_sec"] for e in tl.shot_durations), 2)
    assert tl.total_duration_sec == expected
    assert tl.total_duration_sec > 0


def test_commit_editor_proposal_sets_transitions(svc, prod):
    agent = EditorAgent()
    out = agent.run({
        "scene_id": "sc1",
        "shots": _SHOTS,
        "narrative_intent": "balanced",
        "target_duration_sec": 30.0,
    })
    proposal = out["proposals"][0]

    new_prod = svc.commit_editor_proposal(prod, proposal)

    tl = new_prod.timeline
    n = len(proposal["shot_sequence"])
    # n shots → n-1 transitions
    assert len(tl.transitions) == n - 1
    for t in tl.transitions:
        assert "from_shot" in t
        assert "to_shot" in t
        assert "type" in t


def test_commit_editor_proposal_is_pure(svc, prod):
    """Calling commit_editor_proposal must not mutate the input Production."""
    agent = EditorAgent()
    out = agent.run({"scene_id": "sc1", "shots": _SHOTS,
                     "narrative_intent": "balanced", "target_duration_sec": 30.0})
    proposal = out["proposals"][0]

    _ = svc.commit_editor_proposal(prod, proposal)

    assert prod.timeline is None  # original untouched


def test_commit_editor_proposal_emits_audit_entry(svc, prod):
    agent = EditorAgent()
    out = agent.run({"scene_id": "sc1", "shots": _SHOTS,
                     "narrative_intent": "balanced", "target_duration_sec": 30.0})
    proposal = out["proposals"][0]

    new_prod = svc.commit_editor_proposal(prod, proposal)

    timeline_events = [
        e for e in new_prod.audit_trail
        if e.action_type == "timeline_assembly"
    ]
    assert len(timeline_events) == 1
    evt = timeline_events[0]
    assert evt.payload["scene_id"] == "sc1"
    assert evt.payload["shot_count"] == len(proposal["shot_sequence"])


# ---------------------------------------------------------------------------
# Multi-scene accumulation
# ---------------------------------------------------------------------------

def test_commit_two_scenes_accumulates(svc, prod):
    """Committing proposals for two different scenes accumulates on the timeline."""
    agent = EditorAgent()

    shots_sc2 = [
        {"id": "shot-010", "intent": "wide"},
        {"id": "shot-011", "intent": "close"},
    ]

    out1 = agent.run({"scene_id": "sc1", "shots": _SHOTS,
                      "narrative_intent": "balanced", "target_duration_sec": 30.0})
    out2 = agent.run({"scene_id": "sc2", "shots": shots_sc2,
                      "narrative_intent": "fast action", "target_duration_sec": 10.0})

    prod2 = svc.commit_editor_proposal(prod, out1["proposals"][0])
    prod3 = svc.commit_editor_proposal(prod2, out2["proposals"][0])

    tl = prod3.timeline
    assert "sc1" in tl.scene_order
    assert "sc2" in tl.scene_order
    assert len(tl.shot_durations) == len(_SHOTS) + len(shots_sc2)
    assert tl.total_duration_sec > 0


def test_commit_same_scene_replaces_not_duplicates(svc, prod):
    """Re-committing a proposal for the same scene replaces its entries."""
    agent = EditorAgent()

    out = agent.run({"scene_id": "sc1", "shots": _SHOTS,
                     "narrative_intent": "balanced", "target_duration_sec": 30.0})

    prod2 = svc.commit_editor_proposal(prod, out["proposals"][0])
    prod3 = svc.commit_editor_proposal(prod2, out["proposals"][1])  # different proposal, same scene

    tl = prod3.timeline
    sc1_entries = [e for e in tl.shot_durations if e["scene_id"] == "sc1"]
    # Should equal the shot count of the sequence, not doubled
    assert len(sc1_entries) == len(out["proposals"][1]["shot_sequence"])
    assert tl.scene_order.count("sc1") == 1


# ---------------------------------------------------------------------------
# Round-trip persistence
# ---------------------------------------------------------------------------

def test_commit_proposal_persists_and_reloads(svc, prod):
    """Timeline assembled from a proposal survives save/load round-trip."""
    agent = EditorAgent()
    out = agent.run({"scene_id": "sc1", "shots": _SHOTS,
                     "narrative_intent": "balanced", "target_duration_sec": 30.0})
    proposal = out["proposals"][0]

    new_prod = svc.commit_editor_proposal(prod, proposal)
    svc.save(new_prod)
    reloaded = svc.load(new_prod.id)

    tl = reloaded.timeline
    assert tl is not None
    assert "sc1" in tl.scene_order
    assert len(tl.shot_durations) == len(proposal["shot_sequence"])
    assert tl.total_duration_sec == new_prod.timeline.total_duration_sec
