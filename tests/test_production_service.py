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
- create_branch() / snapshot() / merge() iteration workflow
- archive() retention policy and PUBLISHED-state guard
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


# ===========================================================================
# merge() tests
# ===========================================================================

def _make_published_prod(svc: ProductionService) -> "Production":
    """Helper: advance a production from DRAFT through to PUBLISHED state."""
    from src.schema.production_document import AuditEntry, utc_now_iso

    def _transition(p, next_state):
        return svc.apply_event(p, AuditEntry(
            id=f"evt_{next_state.lower()[:12]}",
            ts=utc_now_iso(),
            actor="test",
            action_type="state_transition",
            payload={"next_state": next_state},
        ))

    prod = svc.init("State Machine")
    prod = _transition(prod, "BRIEFED")
    prod = _transition(prod, "IN_PRODUCTION")
    prod = _transition(prod, "IN_REVIEW")
    prod = _transition(prod, "APPROVED")
    prod = _transition(prod, "PUBLISHED")
    return prod


def test_merge_appends_audit_entry_and_locks_branch(svc: ProductionService):
    """merge() records a 'merge' AuditEntry and locks the source branch."""
    prod = svc.init("Merge Test")
    prod = svc.create_branch(prod, "colour-grade")
    branch_id = prod.branches[-1].id

    # A snapshot belonging to the new branch is required before merging.
    prod = svc.snapshot(prod, label="colour-grade-v1")

    original_len = len(prod.audit_trail)
    merged = svc.merge(prod, branch_id, actor="colorist", label="colour-grade done")

    # Pure: input untouched.
    assert len(prod.audit_trail) == original_len

    # Merge audit entry present.
    merge_entries = [e for e in merged.audit_trail if e.action_type == "merge"]
    assert len(merge_entries) == 1
    entry = merge_entries[0]
    assert entry.actor == "colorist"
    assert entry.payload["source_branch_id"] == branch_id
    assert entry.payload["label"] == "colour-grade done"

    # Source branch is locked.
    merged_branch = next(b for b in merged.branches if b.id == branch_id)
    assert merged_branch.locked is True

    # Original branch object in the input prod is still unlocked (pure).
    original_branch = next(b for b in prod.branches if b.id == branch_id)
    assert original_branch.locked is False


def test_merge_raises_on_unknown_branch(svc: ProductionService):
    """merge() raises StorageError when the branch_id does not exist."""
    prod = svc.init("No Branch")
    with pytest.raises(StorageError, match="not found"):
        svc.merge(prod, "branch_doesnotexist1")


def test_merge_raises_when_no_snapshot(svc: ProductionService):
    """merge() raises StorageError when the branch has no snapshot."""
    prod = svc.init("No Snap")
    prod = svc.create_branch(prod, "empty-branch")
    branch_id = prod.branches[-1].id
    # Do NOT take a snapshot — merge must reject this.
    with pytest.raises(StorageError, match="no snapshots"):
        svc.merge(prod, branch_id)


def test_merge_default_label_uses_branch_name(svc: ProductionService):
    """merge() auto-generates label from branch name when none is supplied."""
    prod = svc.init("Auto Label")
    prod = svc.create_branch(prod, "vfx-pass")
    branch_id = prod.branches[-1].id
    prod = svc.snapshot(prod)
    merged = svc.merge(prod, branch_id)
    entry = next(e for e in merged.audit_trail if e.action_type == "merge")
    assert "vfx-pass" in entry.payload["label"]


# ===========================================================================
# archive() tests
# ===========================================================================

def test_archive_records_expiry_in_metadata(svc: ProductionService, tmp_path: Path):
    """archive() stamps archived_at + expires_at on metadata and audit trail."""
    prod = _make_published_prod(svc)
    archived = svc.archive(prod, actor="studio_admin")

    assert "archived_at" in archived.metadata
    assert "expires_at" in archived.metadata

    archive_entries = [
        e for e in archived.audit_trail
        if e.action_type == "system" and e.payload.get("operation") == "archive"
    ]
    assert len(archive_entries) == 1
    entry = archive_entries[0]
    assert entry.payload["retention_days"] == 2555
    assert entry.payload["artifacts"] == ["production.json", "audit.jsonl"]
    assert entry.actor == "studio_admin"


def test_archive_custom_retention(svc: ProductionService):
    """archive() respects a caller-supplied retention_days."""
    prod = _make_published_prod(svc)
    archived = svc.archive(prod, retention_days=365)
    entry = next(
        e for e in archived.audit_trail
        if e.action_type == "system" and e.payload.get("operation") == "archive"
    )
    assert entry.payload["retention_days"] == 365


def test_archive_requires_published_state(svc: ProductionService):
    """archive() raises StorageError when production is not PUBLISHED."""
    prod = svc.init("Not Published Yet")
    with pytest.raises(StorageError, match="PUBLISHED"):
        svc.archive(prod)


def test_archive_is_pure(svc: ProductionService):
    """archive() never mutates the input production."""
    prod = _make_published_prod(svc)
    original_meta = dict(prod.metadata)
    original_len = len(prod.audit_trail)

    svc.archive(prod)

    assert prod.metadata == original_meta
    assert len(prod.audit_trail) == original_len


# ===========================================================================
# branch_compare() tests  (§16 — Version Trees)
# ===========================================================================

def test_branch_compare_returns_both_branch_summaries(svc: ProductionService):
    """branch_compare() returns structured info for both branches."""
    prod = svc.init("Compare Test")
    prod = svc.create_branch(prod, "dark-angle")
    bid_a = prod.branches[-1].id
    prod = svc.snapshot(prod, label="dark-angle-v1")

    prod = svc.create_branch(prod, "warm-angle")
    bid_b = prod.branches[-1].id
    prod = svc.snapshot(prod, label="warm-angle-v1")

    result = svc.branch_compare(prod, bid_a, bid_b)

    assert result["branch_a"]["id"] == bid_a
    assert result["branch_a"]["name"] == "dark-angle"
    assert result["branch_b"]["id"] == bid_b
    assert result["branch_b"]["name"] == "warm-angle"
    assert result["branch_a"]["snapshot_count"] == 1
    assert result["branch_b"]["snapshot_count"] == 1


def test_branch_compare_tip_snapshot_present(svc: ProductionService):
    """branch_compare() exposes tip snapshot id and content_hash."""
    prod = svc.init("Tip Snap Test")
    prod = svc.create_branch(prod, "branch-x")
    bid = prod.branches[-1].id
    prod = svc.snapshot(prod, label="x-v1")

    prod = svc.create_branch(prod, "branch-y")
    bid2 = prod.branches[-1].id
    prod = svc.snapshot(prod, label="y-v1")

    r = svc.branch_compare(prod, bid, bid2)
    assert r["branch_a"]["tip_snapshot"]["label"] == "x-v1"
    assert r["branch_b"]["tip_snapshot"]["label"] == "y-v1"
    assert isinstance(r["branch_a"]["tip_snapshot"]["content_hash"], str)
    assert len(r["branch_a"]["tip_snapshot"]["content_hash"]) == 64  # SHA-256 hex


def test_branch_compare_summary_keys(svc: ProductionService):
    """branch_compare() summary contains expected keys."""
    prod = svc.init("Summary Keys")
    prod = svc.create_branch(prod, "a")
    bid_a = prod.branches[-1].id
    prod = svc.snapshot(prod)
    prod = svc.create_branch(prod, "b")
    bid_b = prod.branches[-1].id
    prod = svc.snapshot(prod)

    r = svc.branch_compare(prod, bid_a, bid_b)
    for key in ("approved_shots", "scene_count", "reviewer_score_avg",
                "content_hash_a", "content_hash_b", "hashes_equal",
                "audit_events_a", "audit_events_b"):
        assert key in r["summary"], f"missing key: {key}"


def test_branch_compare_divergence_keys(svc: ProductionService):
    """branch_compare() divergence section lists unique event ids."""
    prod = svc.init("Divergence Keys")
    prod = svc.create_branch(prod, "left")
    bid_a = prod.branches[-1].id
    prod = svc.snapshot(prod)
    prod = svc.create_branch(prod, "right")
    bid_b = prod.branches[-1].id
    prod = svc.snapshot(prod)

    r = svc.branch_compare(prod, bid_a, bid_b)
    assert "branch_a_only_events" in r["divergence"]
    assert "branch_b_only_events" in r["divergence"]
    assert "snapshot_count_delta" in r["divergence"]


def test_branch_compare_raises_on_unknown_branch(svc: ProductionService):
    """branch_compare() raises StorageError when a branch_id is unknown."""
    prod = svc.init("Unknown Branch Compare")
    prod = svc.create_branch(prod, "real-branch")
    bid = prod.branches[-1].id
    prod = svc.snapshot(prod)
    with pytest.raises(StorageError, match="not found"):
        svc.branch_compare(prod, bid, "branch_doesnotexist1")


def test_branch_compare_raises_when_no_snapshot(svc: ProductionService):
    """branch_compare() raises StorageError when a branch has no snapshot."""
    prod = svc.init("No Snap Compare")
    prod = svc.create_branch(prod, "snapped")
    bid_a = prod.branches[-1].id
    prod = svc.snapshot(prod)
    prod = svc.create_branch(prod, "no-snap")
    bid_b = prod.branches[-1].id
    # branch-b has no snapshot
    with pytest.raises(StorageError, match="no snapshots"):
        svc.branch_compare(prod, bid_a, bid_b)


def test_branch_compare_is_pure(svc: ProductionService):
    """branch_compare() does not modify the input production."""
    prod = svc.init("Pure Compare")
    prod = svc.create_branch(prod, "c1")
    bid_a = prod.branches[-1].id
    prod = svc.snapshot(prod)
    prod = svc.create_branch(prod, "c2")
    bid_b = prod.branches[-1].id
    prod = svc.snapshot(prod)

    original_len = len(prod.audit_trail)
    svc.branch_compare(prod, bid_a, bid_b)
    assert len(prod.audit_trail) == original_len


# ===========================================================================
# StudioService tests  (§9 — Information Architecture, Layer 1)
# ===========================================================================

from src.service.production_service import StudioService


@pytest.fixture
def studio_svc(tmp_path: Path) -> StudioService:
    return StudioService(storage_dir=tmp_path)


def test_studio_create_returns_studio(studio_svc: StudioService):
    """StudioService.create() returns a Studio with correct id prefix."""
    studio = studio_svc.create("Acme Films", owner="alice")
    assert studio.id.startswith("studio_")
    assert studio.name == "Acme Films"
    assert studio.owner == "alice"
    assert studio.production_ids == []
    assert studio.member_roles == {}


def test_studio_create_writes_disk_artifact(studio_svc: StudioService, tmp_path: Path):
    """StudioService.create() writes studio.json to disk."""
    studio = studio_svc.create("On Disk")
    studio_json = tmp_path / "studios" / studio.id / "studio.json"
    assert studio_json.exists()


def test_studio_load_roundtrip(studio_svc: StudioService):
    """StudioService.load() reconstructs the same Studio after create()."""
    studio = studio_svc.create("Roundtrip Studio")
    loaded = studio_svc.load(studio.id)
    assert loaded.id == studio.id
    assert loaded.name == studio.name
    assert loaded.owner == studio.owner


def test_studio_load_raises_on_missing(studio_svc: StudioService):
    """StudioService.load() raises ProductionNotFound for unknown ids."""
    from src.service.production_service import ProductionNotFound
    with pytest.raises(ProductionNotFound):
        studio_svc.load("studio_doesnotexist1")


def test_studio_add_production_is_pure(studio_svc: StudioService):
    """add_production() returns a new Studio; original is unchanged."""
    studio = studio_svc.create("Add Prod")
    updated = studio_svc.add_production(studio, "prod_abc123456789")
    assert "prod_abc123456789" in updated.production_ids
    assert studio.production_ids == []  # original untouched


def test_studio_add_production_idempotent(studio_svc: StudioService):
    """add_production() is idempotent — adding the same id twice is safe."""
    studio = studio_svc.create("Idempotent")
    s1 = studio_svc.add_production(studio, "prod_abc123456789")
    s2 = studio_svc.add_production(s1, "prod_abc123456789")
    assert s2.production_ids.count("prod_abc123456789") == 1


def test_studio_remove_production(studio_svc: StudioService):
    """remove_production() removes the id from the list."""
    studio = studio_svc.create("Remove Prod")
    studio = studio_svc.add_production(studio, "prod_abc123456789")
    studio = studio_svc.add_production(studio, "prod_def456789012")
    removed = studio_svc.remove_production(studio, "prod_abc123456789")
    assert "prod_abc123456789" not in removed.production_ids
    assert "prod_def456789012" in removed.production_ids


def test_studio_set_member_role(studio_svc: StudioService):
    """set_member_role() adds and updates a member → role mapping."""
    studio = studio_svc.create("Member Roles")
    studio = studio_svc.set_member_role(studio, "user_alice", "director")
    assert studio.member_roles["user_alice"] == "director"
    # update role
    studio = studio_svc.set_member_role(studio, "user_alice", "producer")
    assert studio.member_roles["user_alice"] == "producer"


def test_studio_remove_member(studio_svc: StudioService):
    """remove_member() drops the member from roles."""
    studio = studio_svc.create("Remove Member")
    studio = studio_svc.set_member_role(studio, "user_bob", "editor")
    studio = studio_svc.remove_member(studio, "user_bob")
    assert "user_bob" not in studio.member_roles


def test_studio_list_studios(studio_svc: StudioService):
    """list_studios() enumerates all studios on disk."""
    a = studio_svc.create("Alpha Studio")
    b = studio_svc.create("Beta Studio")
    studio_svc.save(a)
    studio_svc.save(b)
    summaries = studio_svc.list_studios()
    ids = {s["id"] for s in summaries}
    assert a.id in ids
    assert b.id in ids
    assert all("production_count" in s for s in summaries)


def test_studio_save_roundtrip(studio_svc: StudioService):
    """save() + load() preserves member_roles and production_ids."""
    studio = studio_svc.create("Save Roundtrip")
    studio = studio_svc.add_production(studio, "prod_abc123456789")
    studio = studio_svc.set_member_role(studio, "user_carol", "colorist")
    studio_svc.save(studio)
    loaded = studio_svc.load(studio.id)
    assert "prod_abc123456789" in loaded.production_ids
    assert loaded.member_roles["user_carol"] == "colorist"


def test_studio_summary(studio_svc: StudioService):
    """summary() returns a JSON-serialisable dict for the studio."""
    studio = studio_svc.create("Summary Test")
    studio_svc.save(studio)
    d = studio_svc.summary(studio.id)
    assert d["id"] == studio.id
    assert d["name"] == "Summary Test"
    assert isinstance(d["production_ids"], list)


# ===========================================================================
# Content-hash sidecar tests  (P2-C — integrity verification on load())
# ===========================================================================

def test_sidecar_written_on_init(svc: ProductionService, tmp_path: Path):
    """init() writes a production.json.sha256 sidecar next to production.json."""
    prod = svc.init("Sidecar Written")
    sidecar = tmp_path / prod.id / "production.json.sha256"
    assert sidecar.exists(), "sidecar not created by init()"
    digest = sidecar.read_text(encoding="utf-8").strip()
    assert len(digest) == 64, "sidecar should contain a hex SHA-256 (64 chars)"


def test_load_verifies_sidecar_round_trip(svc: ProductionService):
    """load() succeeds when sidecar matches file — basic round-trip."""
    prod = svc.init("Hash Round-trip")
    # A second load must not raise even though a sidecar is present.
    loaded = svc.load(prod.id)
    assert loaded.id == prod.id


def test_load_raises_on_tampered_file(svc: ProductionService, tmp_path: Path):
    """load() raises StorageError when production.json is tampered after write."""
    import hashlib

    prod = svc.init("Tamper Test")
    state_path = tmp_path / prod.id / "production.json"

    # Tamper: append a space so bytes diverge from the recorded hash.
    original = state_path.read_bytes()
    state_path.write_bytes(original + b" ")

    with pytest.raises(StorageError, match="content-hash mismatch"):
        svc.load(prod.id)


def test_load_silent_on_missing_sidecar(svc: ProductionService, tmp_path: Path):
    """load() succeeds silently when no sidecar exists (legacy backward-compat)."""
    prod = svc.init("Legacy No Sidecar")
    sidecar = tmp_path / prod.id / "production.json.sha256"
    sidecar.unlink()  # simulate a pre-sidecar production on disk

    # Must not raise — backward-compatible silent pass.
    loaded = svc.load(prod.id)
    assert loaded.id == prod.id
