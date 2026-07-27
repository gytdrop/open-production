"""Tests for audit.recorder.AuditRecorder.

Five tests:
  1. Recorder writes valid JSONL; entries are parseable as JSON.
  2. Multiple record_gate_decision calls produce the right number of entries.
  3. Each entry has the required fields: ts, gate_name, claim_id, decision_status.
  4. Empty file → entries() returns [].
  5. Recorder truncates/creates fresh on instantiation (no leftover entries).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from audit.recorder import AuditRecorder


# ---------------------------------------------------------------------------
# Test 1: Valid JSONL output
# ---------------------------------------------------------------------------

def test_recorder_writes_valid_jsonl(tmp_path):
    """Single record_gate_decision call writes one parseable JSON line."""
    path = str(tmp_path / "trail.jsonl")
    rec = AuditRecorder(path=path)
    rec.record_gate_decision(
        gate_name="evidence_gate",
        claim_id="c1",
        decision_status="accepted",
        reason="has sources",
        evidence={"source_ids": ["s1"]},
    )
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert isinstance(entry, dict)


# ---------------------------------------------------------------------------
# Test 2: Multiple calls → correct entry count
# ---------------------------------------------------------------------------

def test_multiple_calls_produce_correct_count(tmp_path):
    """Three record_gate_decision calls → three entries."""
    path = str(tmp_path / "trail.jsonl")
    rec = AuditRecorder(path=path)
    for i in range(3):
        rec.record_gate_decision(
            gate_name="evidence_gate",
            claim_id=f"c{i}",
            decision_status="accepted",
        )
    assert len(rec.entries()) == 3


# ---------------------------------------------------------------------------
# Test 3: Required fields present
# ---------------------------------------------------------------------------

def test_entries_have_required_fields(tmp_path):
    """Every entry must contain ts, gate_name, claim_id, decision_status."""
    path = str(tmp_path / "trail.jsonl")
    rec = AuditRecorder(path=path)
    rec.record_gate_decision(
        gate_name="publication_gate",
        claim_id="doc-1",
        decision_status="publish_ok",
        reason="ok",
    )
    entries = rec.entries()
    assert len(entries) == 1
    entry = entries[0]
    for field in ("ts", "gate_name", "claim_id", "decision_status"):
        assert field in entry, f"Missing required field: {field!r}"
    assert entry["gate_name"] == "publication_gate"
    assert entry["claim_id"] == "doc-1"
    assert entry["decision_status"] == "publish_ok"


# ---------------------------------------------------------------------------
# Test 4: Empty file → entries() returns []
# ---------------------------------------------------------------------------

def test_entries_on_empty_file_returns_empty_list(tmp_path):
    """Fresh recorder with no writes returns an empty list from entries()."""
    path = str(tmp_path / "trail.jsonl")
    rec = AuditRecorder(path=path)
    assert rec.entries() == []


# ---------------------------------------------------------------------------
# Test 5: Recorder truncates on re-instantiation
# ---------------------------------------------------------------------------

def test_recorder_truncates_on_reinstatiation(tmp_path):
    """A second AuditRecorder on the same path starts fresh (no leftover entries)."""
    path = str(tmp_path / "trail.jsonl")

    # First recorder writes two entries.
    rec1 = AuditRecorder(path=path)
    rec1.record_gate_decision(gate_name="evidence_gate", claim_id="c1", decision_status="accepted")
    rec1.record_gate_decision(gate_name="evidence_gate", claim_id="c2", decision_status="rejected")
    assert len(rec1.entries()) == 2

    # Second recorder on same path starts fresh.
    rec2 = AuditRecorder(path=path)
    assert rec2.entries() == []
