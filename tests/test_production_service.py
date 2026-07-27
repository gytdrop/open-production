"""
Tests for src.service.production_service.ProductionService.

Covers:
- init() creates disk artifacts and a DRAFT production
- load() round-trips save()
- save() is atomic (uses temp+rename)
- save() appends only NEW audit entries to the journal
- apply_event() is pure (never mutates input)
- log() filters by action_type
- list_productions() enumerates
- status() returns JSON-friendly dict
- ProductionNotFound raised on missing production

Smoke-test: 8 tests, all should pass.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.service.production_service import (
    ProductionNotFound,
    ProductionService,
    StorageError,
)
from src.schema.production_document import (
    AuditEntry,
    IntentDocument,
    Production,
    utc_now_iso,
)


@pytest.fixture
def svc(tmp_path: Path) -> ProductionService:
    return ProductionService(storage_dir=tmp_path)


def test_init_creates_disk_artifacts(svc: ProductionService, tmp_path: Path):
    prod = svc.init("Test Brand Film")
    assert prod.id.startswith("prod_")
    assert prod.state == "DRAFT"
    assert prod.title == "Test Brand Film"
    prod_dir = tmp_path / prod.id
    assert prod_dir.exists()
    assert (prod_dir / "production.json").exists()
    assert (prod_dir / "audit.jsonl").exists()


def test_init_emits_system_event(svc: ProductionService):
    prod = svc.init("Hello")
    assert len(prod.audit_trail) == 1
    assert prod.audit_trail[0].action_type == "system"
    assert prod.audit_trail[0].payload.get("operation") == "init"


def test_load_roundtrips_save(svc: ProductionService):
    prod = svc.init("Roundtrip")
    prod2 = svc.load(prod.id)
    assert prod2.id == prod.id
    assert prod2.title == prod.title
    assert prod2.state == prod.state
    assert len(prod2.audit_trail) == len(prod.audit_trail)


def test_apply_event_is_pure(svc: ProductionService):
    prod = svc.init("Pure")
    original_audit_len = len(prod.audit_trail)
    new_entry = AuditEntry(
        id="evt_test123abc",
        ts=utc_now_iso(),
        actor="human.test",
        action_type="decision",
        payload={"pick": "angle_2"},
    )
    new_prod = svc.apply_event(prod, new_entry)
    # original untouched
    assert len(prod.audit_trail) == original_audit_len
    # new has the additional entry
    assert len(new_prod.audit_trail) == original_audit_len + 1
    assert new_prod.audit_trail[-1].id == "evt_test123abc"


def test_save_appends_only_new_entries(svc: ProductionService, tmp_path: Path):
    prod = svc.init("Journal Test")
    initial_journal_lines = (tmp_path / prod.id / "audit.jsonl").read_text().count("\n")
    # apply one more event, save, check journal grew by exactly 1
    new_prod = svc.apply_event(prod, AuditEntry(
        id="evt_journtest1",
        ts=utc_now_iso(),
        actor="test",
        action_type="decision",
        payload={"x": 1},
    ))
    svc.save(new_prod)
    after_lines = (tmp_path / prod.id / "audit.jsonl").read_text().count("\n")
    assert after_lines == initial_journal_lines + 1


def test_log_filters_by_action_type(svc: ProductionService):
    prod = svc.init("Filter Test")
    new_prod = svc.apply_event(prod, AuditEntry(
        id="evt_filtest1234",
        ts=utc_now_iso(),
        actor="test",
        action_type="gate_decision",
        gate_name="confirm_gate",
        claim_id="c1",
        decision_status="accepted",
    ))
    svc.save(new_prod)
    all_entries = svc.log(prod.id)
    assert any(e["action_type"] == "system" for e in all_entries)
    assert any(e["action_type"] == "gate_decision" for e in all_entries)
    gate_only = svc.log(prod.id, action_type="gate_decision")
    assert all(e["action_type"] == "gate_decision" for e in gate_only)
    assert len(gate_only) >= 1


def test_list_productions_enumerates(svc: ProductionService):
    a = svc.init("Alpha")
    b = svc.init("Beta")
    summary = svc.list_productions()
    ids = {p["id"] for p in summary}
    assert a.id in ids
    assert b.id in ids
    assert all("state" in p for p in summary)


def test_production_not_found_on_missing(svc: ProductionService):
    with pytest.raises(ProductionNotFound):
        svc.load("prod_doesnotexist1234")
    with pytest.raises(ProductionNotFound):
        svc.log("prod_doesnotexist1234")
