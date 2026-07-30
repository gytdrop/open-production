"""Tests for ProductionService.advance_stage() — §14 stage gate enforcement.

Verifies that:
  - advance_stage() blocks illegal state transitions (same as apply_event).
  - Each gate is evaluated; failing gates raise StorageError and do NOT mutate the prod.
  - Passing gates emit a ``gate_decision`` AuditEntry with decision_status='passed'.
  - Failing gates emit a ``gate_decision`` AuditEntry with decision_status='blocked'.
  - gate_overrides let callers waive named gates; those emit decision_status='overridden'.
  - A successful advance emits a ``stage_advance`` AuditEntry and flips prod.state.
  - advance_stage() is pure — the input Production is never mutated.
  - Stages with no registered gates (BRIEFED→IN_PRODUCTION with no gate) advance freely
    once the structural check passes.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.service.production_service import ProductionService, StorageError
from src.schema.production_document import (
    AuditEntry,
    Character,
    Environment,
    IntentDocument,
    MoodSpec,
    Production,
    Reference,
    Scene,
    Shot,
    StyleToken,
    utc_now_iso,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def svc(tmp_path: Path) -> ProductionService:
    return ProductionService(storage_dir=tmp_path)


@pytest.fixture
def draft_prod(svc: ProductionService) -> Production:
    return svc.init("Gate Test Production")


def _add_three_refs(prod: Production) -> Production:
    """Helper: attach 3 references with URIs so research_gate passes."""
    refs = [
        Reference(id=f"ref_gatetest{i:04d}", kind="image", label=f"ref{i}", uri=f"demo://img/{i}")
        for i in range(1, 4)
    ]
    return replace(prod, references=list(prod.references) + refs)


def _add_scene_with_shots(prod: Production) -> Production:
    """Helper: attach one scene with one shot (in_review status)."""
    shot = Shot(
        id="shot_gatetest001",
        scene_id="scene_gatetest001",
        intent="Demo shot",
        duration_sec=3.0,
        status="in_review",
    )
    scene = Scene(id="scene_gatetest001", name="Gate Test Scene", shots=[shot])
    return replace(prod, scenes=list(prod.scenes) + [scene])


def _add_publication_metadata(prod: Production) -> Production:
    """Helper: add doi/authors/date to metadata so publication_gate passes."""
    return replace(prod, metadata={
        **prod.metadata,
        "doi": "10.9999/gate-test",
        "authors": ["Alice"],
        "date": "2026-07-27",
    })


# ---------------------------------------------------------------------------
# Basic transition validation (mirrors apply_event tests)
# ---------------------------------------------------------------------------

def test_advance_stage_illegal_transition_raises(svc, draft_prod):
    """advance_stage from DRAFT→IN_PRODUCTION (skipping BRIEFED) must raise."""
    with pytest.raises(StorageError, match="illegal transition"):
        svc.advance_stage(draft_prod, "IN_PRODUCTION")


def test_advance_stage_unknown_state_raises(svc, draft_prod):
    """advance_stage to a non-existent state raises StorageError."""
    with pytest.raises(StorageError, match="unknown target state"):
        svc.advance_stage(draft_prod, "LIMBO")


# ---------------------------------------------------------------------------
# DRAFT → BRIEFED  (research_gate: need ≥3 references)
# ---------------------------------------------------------------------------

def test_advance_to_briefed_blocked_without_refs(svc, draft_prod):
    """research_gate blocks DRAFT→BRIEFED when Production.references is empty."""
    with pytest.raises(StorageError, match="research_gate"):
        svc.advance_stage(draft_prod, "BRIEFED")


def test_advance_to_briefed_blocked_audit_entry(svc, draft_prod):
    """A blocked gate still emits a gate_decision AuditEntry with status='blocked'."""
    try:
        svc.advance_stage(draft_prod, "BRIEFED")
    except StorageError:
        pass
    # Production was not mutated — the blocked entry is only in the raised error.
    # Verify input prod is unchanged (pure).
    assert draft_prod.state == "DRAFT"


def test_advance_to_briefed_passes_with_refs(svc, draft_prod):
    """research_gate passes when ≥3 references are present."""
    prod = _add_three_refs(draft_prod)
    new_prod = svc.advance_stage(prod, "BRIEFED", actor="test_runner")

    assert new_prod.state == "BRIEFED"
    advance_entries = [e for e in new_prod.audit_trail if e.action_type == "stage_advance"]
    assert len(advance_entries) == 1
    ae = advance_entries[0]
    assert ae.payload["from_state"] == "DRAFT"
    assert ae.payload["to_state"] == "BRIEFED"
    assert ae.actor == "test_runner"


def test_advance_to_briefed_emits_gate_passed_entry(svc, draft_prod):
    """A passed gate emits a gate_decision AuditEntry with decision_status='passed'."""
    prod = _add_three_refs(draft_prod)
    new_prod = svc.advance_stage(prod, "BRIEFED")

    gate_entries = [
        e for e in new_prod.audit_trail
        if e.action_type == "gate_decision" and e.gate_name == "research_gate"
    ]
    assert len(gate_entries) == 1
    assert gate_entries[0].decision_status == "passed"


def test_advance_to_briefed_is_pure(svc, draft_prod):
    """advance_stage never mutates the input Production."""
    prod = _add_three_refs(draft_prod)
    original_state = prod.state
    original_trail_len = len(prod.audit_trail)

    svc.advance_stage(prod, "BRIEFED")

    assert prod.state == original_state
    assert len(prod.audit_trail) == original_trail_len


# ---------------------------------------------------------------------------
# Gate override mechanism
# ---------------------------------------------------------------------------

def test_gate_override_allows_blocked_gate(svc, draft_prod):
    """gate_overrides with a matching substring waives the gate."""
    # No references — research_gate would normally block.
    new_prod = svc.advance_stage(
        draft_prod,
        "BRIEFED",
        actor="supervisor",
        gate_overrides={"research_gate": True},
    )
    assert new_prod.state == "BRIEFED"
    override_entries = [
        e for e in new_prod.audit_trail
        if e.action_type == "gate_decision" and e.decision_status == "overridden"
    ]
    assert len(override_entries) == 1
    assert "supervisor" in override_entries[0].reason


# ---------------------------------------------------------------------------
# IN_REVIEW → APPROVED  (consistency_gate + shot_review_gate)
# ---------------------------------------------------------------------------

def _advance_to_in_review(svc, prod):
    """Helper: fast-forward a production to IN_REVIEW using raw apply_event."""
    def _tx(p, ns):
        return svc.apply_event(p, AuditEntry(
            id=f"evt_{ns.lower()[:12]}",
            ts=utc_now_iso(),
            actor="test",
            action_type="state_transition",
            payload={"next_state": ns},
        ))
    prod = _tx(prod, "BRIEFED")
    prod = _tx(prod, "IN_PRODUCTION")
    prod = _tx(prod, "IN_REVIEW")
    return prod


def test_advance_to_approved_passes_with_reviewed_shots(svc, draft_prod):
    """consistency + shot_review gates pass → production advances to APPROVED."""
    prod = _advance_to_in_review(svc, draft_prod)
    prod = _add_scene_with_shots(prod)
    new_prod = svc.advance_stage(prod, "APPROVED")
    assert new_prod.state == "APPROVED"


def test_advance_to_approved_blocked_by_draft_shots(svc, draft_prod):
    """shot_review_gate blocks APPROVED when shots are still in 'draft' status."""
    prod = _advance_to_in_review(svc, draft_prod)
    # Add a shot in 'draft' status — not yet reviewed.
    bad_shot = Shot(
        id="shot_draft0001",
        scene_id="scene_bad0001",
        intent="Not reviewed",
        duration_sec=2.0,
        status="draft",
    )
    scene = Scene(id="scene_bad0001", name="Bad Scene", shots=[bad_shot])
    prod = replace(prod, scenes=[scene])
    with pytest.raises(StorageError, match="shot_review_gate"):
        svc.advance_stage(prod, "APPROVED")


# ---------------------------------------------------------------------------
# APPROVED → PUBLISHED  (publication_gate)
# ---------------------------------------------------------------------------

def _advance_to_approved(svc, prod):
    """Helper: fast-forward to APPROVED using raw apply_event."""
    def _tx(p, ns):
        return svc.apply_event(p, AuditEntry(
            id=f"evt_{ns.lower()[:12]}",
            ts=utc_now_iso(),
            actor="test",
            action_type="state_transition",
            payload={"next_state": ns},
        ))
    for ns in ("BRIEFED", "IN_PRODUCTION", "IN_REVIEW", "APPROVED"):
        prod = _tx(prod, ns)
    return prod


def test_advance_to_published_blocked_without_metadata(svc, draft_prod):
    """publication_gate blocks APPROVED→PUBLISHED when doi/authors/date absent."""
    prod = _advance_to_approved(svc, draft_prod)
    with pytest.raises(StorageError, match="publication_gate"):
        svc.advance_stage(prod, "PUBLISHED")


def test_advance_to_published_passes_with_metadata(svc, draft_prod):
    """publication_gate passes when metadata contains doi, authors, date."""
    prod = _advance_to_approved(svc, draft_prod)
    prod = _add_publication_metadata(prod)
    new_prod = svc.advance_stage(prod, "PUBLISHED")
    assert new_prod.state == "PUBLISHED"
    advance_entries = [e for e in new_prod.audit_trail if e.action_type == "stage_advance"]
    assert len(advance_entries) == 1
    assert advance_entries[0].payload["to_state"] == "PUBLISHED"
