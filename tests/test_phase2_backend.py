"""Tests for Phase 2 backend additions:
  - ProductionService.snapshot()
  - State-transition direction enforcement
  - Deserialization round-trip (visual_anchors, Shot.characters, version_history)
  - ScopeViolation enforcement in BaseAgent
"""
from __future__ import annotations

import pytest

from src.service.production_service import ProductionService, StorageError
from src.schema.production_document import (
    AuditEntry, IntentDocument, Character, ConsistencyContract,
    Reference, Shot, Scene, CharacterReference, utc_now_iso,
)


@pytest.fixture
def svc(tmp_path):
    return ProductionService(storage_dir=tmp_path)


# ---------------------------------------------------------------------------
# Snapshot tests
# ---------------------------------------------------------------------------

def test_snapshot_creates_version_snapshot(svc):
    """snapshot() adds a VersionSnapshot to the production."""
    prod = svc.init("Snapshot Test")
    snapped = svc.snapshot(prod, label="before-edit", taken_by="test.user")
    assert len(snapped.snapshots) == 1
    snap = snapped.snapshots[0]
    assert snap.id.startswith("snap_")
    assert snap.label == "before-edit"
    assert snap.taken_by == "test.user"
    assert len(snap.content_hash) == 64  # SHA-256 hex


def test_snapshot_is_pure(svc):
    """snapshot() never mutates the original production."""
    prod = svc.init("Pure Snapshot")
    original_snap_count = len(prod.snapshots)
    svc.snapshot(prod, label="test")
    assert len(prod.snapshots) == original_snap_count


def test_snapshot_emits_audit_entry(svc):
    """snapshot() adds a 'snapshot' action_type entry to the audit trail."""
    prod = svc.init("Audit Snapshot")
    snapped = svc.snapshot(prod, label="v1")
    snap_entries = [e for e in snapped.audit_trail if e.action_type == "snapshot"]
    assert len(snap_entries) == 1
    assert snap_entries[0].payload.get("label") == "v1"


def test_snapshot_roundtrips_save_load(svc, tmp_path):
    """snapshot is preserved after save() + load()."""
    prod = svc.init("Roundtrip Snap")
    snapped = svc.snapshot(prod, label="checkpoint-1")
    svc.save(snapped)
    loaded = svc.load(snapped.id)
    assert len(loaded.snapshots) == 1
    assert loaded.snapshots[0].label == "checkpoint-1"


# ---------------------------------------------------------------------------
# State transition direction enforcement
# ---------------------------------------------------------------------------

def test_forward_transition_allowed(svc):
    """DRAFT → BRIEFED is a valid forward transition."""
    prod = svc.init("Forward Trans")
    entry = AuditEntry(
        id="evt_fwdtest1234",
        ts=utc_now_iso(),
        actor="test",
        action_type="state_transition",
        payload={"next_state": "BRIEFED"},
    )
    new_prod = svc.apply_event(prod, entry)
    assert new_prod.state == "BRIEFED"


def test_illegal_backward_transition_raises(svc):
    """DRAFT → APPROVED is illegal and must raise StorageError."""
    prod = svc.init("Bad Trans")
    entry = AuditEntry(
        id="evt_badtrans123",
        ts=utc_now_iso(),
        actor="test",
        action_type="state_transition",
        payload={"next_state": "APPROVED"},
    )
    with pytest.raises(StorageError, match="illegal state transition"):
        svc.apply_event(prod, entry)


def test_revision_loop_allowed(svc):
    """IN_REVIEW → IN_PRODUCTION (revision loop) is explicitly allowed."""
    prod = svc.init("Revision Loop")
    # Advance to IN_REVIEW in steps
    for next_state in ("BRIEFED", "IN_PRODUCTION", "IN_REVIEW"):
        prod = svc.apply_event(prod, AuditEntry(
            id=f"evt_{next_state[:4].lower()}test1",
            ts=utc_now_iso(), actor="test",
            action_type="state_transition",
            payload={"next_state": next_state},
        ))
    # Revision loop: back to IN_PRODUCTION
    prod = svc.apply_event(prod, AuditEntry(
        id="evt_revloop1234",
        ts=utc_now_iso(), actor="test",
        action_type="state_transition",
        payload={"next_state": "IN_PRODUCTION"},
    ))
    assert prod.state == "IN_PRODUCTION"


def test_published_is_terminal(svc):
    """PUBLISHED → anything raises StorageError (terminal state)."""
    prod = svc.init("Terminal")
    for next_state in ("BRIEFED", "IN_PRODUCTION", "IN_REVIEW", "APPROVED", "PUBLISHED"):
        prod = svc.apply_event(prod, AuditEntry(
            id=f"evt_{next_state[:3].lower()}x12345",
            ts=utc_now_iso(), actor="test",
            action_type="state_transition",
            payload={"next_state": next_state},
        ))
    assert prod.state == "PUBLISHED"
    with pytest.raises(StorageError, match="illegal state transition"):
        svc.apply_event(prod, AuditEntry(
            id="evt_postpub1234",
            ts=utc_now_iso(), actor="test",
            action_type="state_transition",
            payload={"next_state": "DRAFT"},
        ))


# ---------------------------------------------------------------------------
# Deserialization round-trip — data fidelity
# ---------------------------------------------------------------------------

def test_character_visual_anchors_survive_roundtrip(svc, tmp_path):
    """visual_anchors on Character are preserved through save() + load()."""
    prod = svc.init("Anchor Roundtrip")
    ref = Reference(id="ref_anchor001", kind="image", label="Nadia front-on")
    contract = ConsistencyContract(
        subject_id="char_nadia001",
        visual_anchors=[ref],
        required_attributes=["red_scarf"],
    )
    char = Character(
        id="char_nadia001",
        name="Nadia",
        consistency_contract=contract,
        visual_anchors=[ref],
    )
    from dataclasses import replace
    prod = replace(prod, characters=[char])
    svc.save(prod)
    loaded = svc.load(prod.id)
    assert len(loaded.characters) == 1
    loaded_char = loaded.characters[0]
    assert loaded_char.name == "Nadia"
    assert len(loaded_char.visual_anchors) == 1
    assert loaded_char.visual_anchors[0].id == "ref_anchor001"
    assert loaded_char.consistency_contract is not None
    assert loaded_char.consistency_contract.required_attributes == ["red_scarf"]
    assert len(loaded_char.consistency_contract.visual_anchors) == 1


def test_shot_characters_survive_roundtrip(svc, tmp_path):
    """CharacterReferences on Shot are preserved through save() + load()."""
    prod = svc.init("Shot Char Roundtrip")
    char_ref = CharacterReference(character_id="char_nadia001", expression="determined")
    shot = Shot(
        id="shot_test0001",
        scene_id="scene_test001",
        intent="Nadia enters the frame",
        duration_sec=3.5,
        characters=[char_ref],
    )
    scene = Scene(id="scene_test001", name="Opening", shots=[shot])
    from dataclasses import replace
    prod = replace(prod, scenes=[scene])
    svc.save(prod)
    loaded = svc.load(prod.id)
    loaded_shot = loaded.scenes[0].shots[0]
    assert len(loaded_shot.characters) == 1
    assert loaded_shot.characters[0].character_id == "char_nadia001"
    assert loaded_shot.characters[0].expression == "determined"


# ---------------------------------------------------------------------------
# ScopeViolation enforcement
# ---------------------------------------------------------------------------

def test_scope_violation_raised_on_out_of_scope_field():
    """_enforce_scope raises ScopeViolation when the output contains a forbidden field."""
    from agents.base import BaseAgent, ScopeViolation

    class StrictAgent(BaseAgent):
        WRITABLE_FIELDS = frozenset({"Shot.camera"})

        def run(self, input: dict) -> dict:
            return self._enforce_scope({"Shot.camera": {"framing": "medium"}, "Shot.lighting": {}})

    agent = StrictAgent(name="strict")
    with pytest.raises(ScopeViolation, match="Shot.lighting"):
        agent.run({})


def test_scope_enforcement_passes_on_allowed_field():
    """_enforce_scope does not raise when all output keys are in WRITABLE_FIELDS."""
    from agents.base import BaseAgent, ScopeViolation

    class LooseAgent(BaseAgent):
        WRITABLE_FIELDS = frozenset({"Shot.camera", "Shot.lighting"})

        def run(self, input: dict) -> dict:
            return self._enforce_scope({
                # K.11 Rule 5: rationale is mandatory in every proposal dict
                "proposals": [{"camera": {}, "lighting": {}, "rationale": "test rationale"}],
            })

    agent = LooseAgent(name="loose")
    result = agent.run({})
    assert "proposals" in result


def test_scope_none_skips_enforcement():
    """WRITABLE_FIELDS=None skips scope checking entirely (legacy agent compatibility)."""
    from agents.base import BaseAgent

    class LegacyAgent(BaseAgent):
        WRITABLE_FIELDS = None

        def run(self, input: dict) -> dict:
            return self._enforce_scope({"anything_at_all": True, "random_key": 42})

    agent = LegacyAgent(name="legacy")
    result = agent.run({})
    assert result["anything_at_all"] is True


def test_scope_violation_raised_on_missing_rationale():
    """_enforce_scope raises ScopeViolation when a proposal dict lacks 'rationale' (K.11 Rule 5)."""
    from agents.base import BaseAgent, ScopeViolation

    class BadProposalAgent(BaseAgent):
        WRITABLE_FIELDS = frozenset({"Shot.camera"})

        def run(self, input: dict) -> dict:
            # Proposal missing the mandatory 'rationale' key
            return self._enforce_scope({"proposals": [{"camera": {}}]})

    agent = BadProposalAgent(name="bad_proposal")
    with pytest.raises(ScopeViolation, match="rationale"):
        agent.run({})
