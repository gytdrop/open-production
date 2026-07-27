"""Gate-validation suite for Open Production's three publication gates.

Tests:
  EvidenceGate  — rejects uncited claims, accepts cited ones, logs rejections.
  ConsistencyGate — surfaces contradictions, surfaces both, empty set is safe.
  PublicationGate — blocks missing DOI, blocks missing authors, accepts complete doc.

Constraints (per session 3 spec):
  - pytest fixtures share claim sets across tests.
  - No external APIs are hit (EvidenceGate/ConsistencyGate/PublicationGate are pure).
  - Production code is NOT modified. Any found bugs are flagged with "Bob flagged:".
"""
from __future__ import annotations

import pytest

from validation.gates import ConsistencyContractGate, ConsistencyGate, EvidenceGate, PublicationGate


# ===========================================================================
# Shared fixtures
# ===========================================================================


@pytest.fixture
def uncited_claim() -> dict:
    """A claim with no source_ids — should be rejected by EvidenceGate."""
    return {"id": "c1", "text": "CRISPR cures sickle cell disease.", "source_ids": []}


@pytest.fixture
def cited_claim() -> dict:
    """A claim with at least one source_id — should be accepted."""
    return {"id": "c2", "text": "CRISPR has shown efficacy in clinical trials.", "source_ids": ["pubmed:12345"]}


@pytest.fixture
def contradicting_claims() -> list[dict]:
    """Two claims about the same fact_id that disagree on conclusion."""
    return [
        {"id": "a", "fact_id": "sickle-cell-cure-rate", "conclusion": "high", "text": "CRISPR achieves >90% efficacy."},
        {"id": "b", "fact_id": "sickle-cell-cure-rate", "conclusion": "moderate", "text": "CRISPR achieves ~60% efficacy."},
    ]


@pytest.fixture
def non_contradicting_claims() -> list[dict]:
    """Two claims about different fact_ids — no contradiction expected."""
    return [
        {"id": "a", "fact_id": "fact-x", "conclusion": "positive", "text": "X is good."},
        {"id": "b", "fact_id": "fact-y", "conclusion": "negative", "text": "Y is bad."},
    ]


@pytest.fixture
def complete_metadata() -> dict:
    """A fully populated document metadata dict — all required fields present."""
    return {
        "doi": "10.1000/xyz123",
        "authors": ["Alice Smith", "Bob Jones"],
        "date": "2026-07-27",
        "title": "CRISPR Gene Editing for Sickle Cell Disease",
    }


@pytest.fixture
def metadata_missing_doi(complete_metadata) -> dict:
    m = dict(complete_metadata)
    del m["doi"]
    return m


@pytest.fixture
def metadata_missing_authors(complete_metadata) -> dict:
    m = dict(complete_metadata)
    del m["authors"]
    return m


# ===========================================================================
# EvidenceGate tests
# ===========================================================================


def test_evidence_gate_rejects_uncited_claim(uncited_claim):
    """EvidenceGate.process() marks a claim with no source_ids as rejected."""
    gate = EvidenceGate()
    result = gate.process(uncited_claim)
    assert result["status"] == "rejected"
    assert "reason" in result


def test_evidence_gate_accepts_cited_claim(cited_claim):
    """EvidenceGate.process() marks a claim with ≥1 source_id as accepted."""
    gate = EvidenceGate()
    result = gate.process(cited_claim)
    assert result["status"] == "accepted"


def test_evidence_gate_rejection_includes_reason(uncited_claim):
    """Rejection result has a non-empty reason so the audit trail is meaningful."""
    gate = EvidenceGate()
    result = gate.process(uncited_claim)
    assert result.get("reason"), "Rejection must carry a non-empty reason string"


def test_evidence_gate_does_not_mutate_input():
    """EvidenceGate.process() must not mutate the caller's dict in-place."""
    gate = EvidenceGate()
    original = {"id": "c0", "text": "Some claim.", "source_ids": []}
    original_copy = dict(original)
    gate.process(original)
    assert original == original_copy, "process() must return a new dict, not mutate the input"


# ===========================================================================
# ConsistencyGate tests
# ===========================================================================


def test_consistency_gate_detects_contradiction(contradicting_claims):
    """Two claims with the same fact_id and different conclusions → contradiction found."""
    gate = ConsistencyGate()
    contradictions = gate.find_contradictions(contradicting_claims)
    assert len(contradictions) == 1
    c = contradictions[0]
    assert c["fact_id"] == "sickle-cell-cure-rate"
    # Both claims must be surfaced — gate must NOT pick a winner.
    assert "claim_a" in c and "claim_b" in c


def test_consistency_gate_surfaces_both_claims(contradicting_claims):
    """The contradiction dict contains both the original claim objects (not just ids)."""
    gate = ConsistencyGate()
    contradictions = gate.find_contradictions(contradicting_claims)
    assert len(contradictions) == 1
    c = contradictions[0]
    both_ids = {c["claim_a"]["id"], c["claim_b"]["id"]}
    assert both_ids == {"a", "b"}


def test_consistency_gate_no_false_positives(non_contradicting_claims):
    """Claims about different fact_ids do not raise a contradiction."""
    gate = ConsistencyGate()
    contradictions = gate.find_contradictions(non_contradicting_claims)
    assert contradictions == []


def test_consistency_gate_empty_claims_is_safe():
    """Empty claim list returns an empty list — not an error."""
    gate = ConsistencyGate()
    result = gate.find_contradictions([])
    assert result == []


def test_consistency_gate_same_conclusion_is_not_contradiction():
    """Two claims with the same fact_id AND same conclusion are not a contradiction."""
    claims = [
        {"id": "a", "fact_id": "f1", "conclusion": "positive"},
        {"id": "b", "fact_id": "f1", "conclusion": "positive"},
    ]
    gate = ConsistencyGate()
    assert gate.find_contradictions(claims) == []


# ===========================================================================
# PublicationGate tests
# ===========================================================================


def test_publication_gate_rejects_missing_doi(metadata_missing_doi):
    """PublicationGate.check() returns (False, message) when DOI is absent."""
    gate = PublicationGate()
    ok, msg = gate.check(metadata_missing_doi)
    assert ok is False
    assert isinstance(msg, str) and len(msg) > 0, "Error must be a non-empty string, not an exception"
    assert "doi" in msg.lower()


def test_publication_gate_rejects_missing_authors(metadata_missing_authors):
    """PublicationGate.check() returns (False, message) when authors is absent."""
    gate = PublicationGate()
    ok, msg = gate.check(metadata_missing_authors)
    assert ok is False
    assert isinstance(msg, str) and len(msg) > 0
    # Bob flagged: 'authors' is in REQUIRED but the check uses `not metadata.get("authors")`.
    # An empty list [] is falsy — gate.check({"doi": "x", "authors": [], "date": "y"})
    # would return (False, "missing authors") even though the key is present.
    # This is arguably correct behaviour (empty authors list = no attribution), but it
    # diverges from the key-presence contract implied by the spec. Flagged for Boris's review.


def test_publication_gate_accepts_complete_document(complete_metadata):
    """PublicationGate.check() returns (True, 'ok') for a fully populated document."""
    gate = PublicationGate()
    ok, msg = gate.check(complete_metadata)
    assert ok is True
    assert msg == "ok"


def test_publication_gate_returns_string_not_exception():
    """Gate returns a (bool, str) tuple — never raises — even for completely empty metadata."""
    gate = PublicationGate()
    try:
        ok, msg = gate.check({})
    except Exception as exc:
        pytest.fail(f"PublicationGate.check() raised an exception instead of returning: {exc}")
    assert ok is False
    assert isinstance(msg, str)


# ===========================================================================
# ConsistencyContractGate tests
# ===========================================================================


def test_ccgate_missing_required_attribute():
    """check() returns (False, message naming the attribute) for a missing required attribute."""
    gate = ConsistencyContractGate()
    contract = {"required_attributes": ["red_scarf", "silver_locket"]}
    result = {"attributes": ["silver_locket"]}  # red_scarf is missing
    ok, reason = gate.check(contract, result)
    assert ok is False
    assert "missing required_attribute" in reason
    assert "red_scarf" in reason


def test_ccgate_prohibited_attribute_present():
    """check() returns (False, message) when a prohibited attribute is in the result."""
    gate = ConsistencyContractGate()
    contract = {"prohibited_attributes": ["glasses"]}
    result = {"attributes": ["glasses", "red_scarf"]}
    ok, reason = gate.check(contract, result)
    assert ok is False
    assert "prohibited_attribute present" in reason
    assert "glasses" in reason


def test_ccgate_empty_contract_passes():
    """check() returns (True, 'ok') when the contract has no required or prohibited entries."""
    gate = ConsistencyContractGate()
    contract = {}
    result = {"attributes": ["anything"]}
    ok, reason = gate.check(contract, result)
    assert ok is True
    assert reason == "ok"


def test_ccgate_tight_tolerance_partial_match():
    """check() includes variance_tolerance in the reason when tolerance <= 0.10."""
    gate = ConsistencyContractGate()
    contract = {
        "required_attributes": ["red_scarf"],
        "variance_tolerance": 0.05,
    }
    result = {"attributes": ["scarf_red"]}  # partial match — not exact
    ok, reason = gate.check(contract, result)
    assert ok is False
    assert "variance_tolerance=0.05" in reason
    assert "red_scarf" in reason
