"""Tests for PublisherAgent — Appendix K.10 of open-production-plan.md."""
from __future__ import annotations

import pytest

from agents.publisher import PublisherAgent


@pytest.fixture
def publisher():
    return PublisherAgent()


@pytest.fixture
def full_input():
    return {
        "production_id": "prod_test1234",
        "title": "Open Production Demo Film",
        "platforms": ["youtube", "tiktok"],
        "doi": "10.9999/demo-2026",
        "authors": ["Alice Director", "Bob Producer"],
        "date": "2026-08-01",
        "rights_statement": "CC BY 4.0",
        "total_duration_sec": 90.0,
        "scene_count": 5,
        "shot_count": 12,
    }


def test_publisher_returns_proposals(publisher, full_input):
    """PublisherAgent returns at least 2 proposals for a multi-platform input."""
    out = publisher.run(full_input)
    assert "proposals" in out
    assert len(out["proposals"]) >= 2


def test_publisher_readiness_passes_with_complete_metadata(publisher, full_input):
    """Readiness check passes when all required metadata fields are present."""
    out = publisher.run(full_input)
    assert out["readiness_check"]["passed"] is True
    assert out["blocking"] is False
    assert out["missing_fields"] == []


def test_publisher_blocking_when_doi_missing(publisher, full_input):
    """PublisherAgent blocks when DOI is absent."""
    full_input["doi"] = ""
    out = publisher.run(full_input)
    assert out["blocking"] is True
    assert "doi" in out["missing_fields"]


def test_publisher_blocking_when_no_shots(publisher, full_input):
    """PublisherAgent adds shot_count to missing_fields when zero shots approved."""
    full_input["shot_count"] = 0
    out = publisher.run(full_input)
    assert any("shot_count" in f for f in out["missing_fields"])


def test_publisher_proposals_have_manifest(publisher, full_input):
    """Every proposal must contain a manifest dict with production_id and title."""
    out = publisher.run(full_input)
    for p in out["proposals"]:
        assert "manifest" in p
        assert p["manifest"]["production_id"] == "prod_test1234"
        assert p["manifest"]["title"] == "Open Production Demo Film"


def test_publisher_archive_proposal_has_provenance(publisher, full_input):
    """The archive proposal manifest must include provenance metadata."""
    out = publisher.run(full_input)
    archive = next((p for p in out["proposals"] if "archive" in p["label"].lower()), None)
    assert archive is not None
    assert "provenance" in archive["manifest"]
    assert archive["manifest"]["provenance"]["audit_trail_required"] is True


def test_publisher_safe_on_empty_input(publisher):
    """run({}) must return a valid dict and never raise (K.11 rule 4)."""
    out = publisher.run({})
    assert "proposals" in out
    assert "blocking" in out
    assert isinstance(out["missing_fields"], list)
