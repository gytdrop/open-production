"""Tests for ResearchAgent — Stage 2 "at least 3 sources" gate."""
from __future__ import annotations

import pytest

from agents.research_agent import MIN_SOURCES, ResearchAgent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sources(*ids: str) -> list[dict]:
    return [{"id": sid, "title": f"Source {sid}"} for sid in ids]


# ---------------------------------------------------------------------------
# Gate pass / fail
# ---------------------------------------------------------------------------

def test_gate_passes_with_exactly_min_sources():
    agent = ResearchAgent()
    out = agent.run({"operation": "validate", "topic": "CRISPR", "sources": _sources("s1", "s2", "s3")})
    assert out["gate_passed"] is True
    assert out["verdict"] == "sources_sufficient"
    assert out["source_count"] == 3
    assert out["missing"] == 0


def test_gate_passes_with_more_than_min_sources():
    agent = ResearchAgent()
    out = agent.run({"operation": "validate", "topic": "AI safety", "sources": _sources("a", "b", "c", "d", "e")})
    assert out["gate_passed"] is True
    assert out["source_count"] == 5
    assert out["missing"] == 0


def test_gate_fails_with_fewer_than_min_sources():
    agent = ResearchAgent()
    out = agent.run({"operation": "validate", "topic": "fusion energy", "sources": _sources("s1", "s2")})
    assert out["gate_passed"] is False
    assert out["verdict"] == "sources_insufficient"
    assert out["source_count"] == 2
    assert out["missing"] == 1


def test_gate_fails_with_zero_sources():
    agent = ResearchAgent()
    out = agent.run({"operation": "validate", "topic": "quantum", "sources": []})
    assert out["gate_passed"] is False
    assert out["source_count"] == 0
    assert out["missing"] == MIN_SOURCES


def test_gate_fails_when_sources_key_absent():
    agent = ResearchAgent()
    out = agent.run({"operation": "validate", "topic": "robotics"})
    assert out["gate_passed"] is False
    assert out["source_count"] == 0


# ---------------------------------------------------------------------------
# Source validation — empty / invalid ids stripped
# ---------------------------------------------------------------------------

def test_empty_id_sources_are_stripped():
    agent = ResearchAgent()
    raw = [
        {"id": "valid1"},
        {"id": ""},          # empty string — invalid
        {"id": "   "},       # whitespace-only — invalid
        {"id": None},        # None — invalid
        {"id": "valid2"},
    ]
    out = agent.run({"operation": "validate", "topic": "test", "sources": raw})
    assert out["source_count"] == 2


def test_non_dict_source_entries_are_stripped():
    agent = ResearchAgent()
    raw = [{"id": "ok"}, "not-a-dict", 42, None, {"id": "ok2"}, {"id": "ok3"}]
    out = agent.run({"operation": "validate", "topic": "test", "sources": raw})
    assert out["source_count"] == 3
    assert out["gate_passed"] is True


# ---------------------------------------------------------------------------
# Output structure
# ---------------------------------------------------------------------------

def test_output_has_all_required_keys():
    agent = ResearchAgent()
    out = agent.run({"operation": "validate", "topic": "climate", "sources": _sources("s1", "s2", "s3")})
    for key in ("verdict", "gate_passed", "source_count", "required_count",
                "sources", "missing", "rationale", "proposals"):
        assert key in out, f"missing key: {key!r}"


def test_required_count_matches_constant_by_default():
    agent = ResearchAgent()
    out = agent.run({"operation": "validate", "topic": "t", "sources": []})
    assert out["required_count"] == MIN_SOURCES


def test_proposals_list_has_one_entry_with_rationale():
    """K.11 Rule 5: every proposal must have a 'rationale' key."""
    agent = ResearchAgent()
    out = agent.run({"operation": "validate", "topic": "bio", "sources": _sources("s1", "s2", "s3")})
    assert len(out["proposals"]) == 1
    assert "rationale" in out["proposals"][0]


def test_sources_in_output_matches_valid_inputs():
    agent = ResearchAgent()
    src = _sources("a", "b", "c")
    out = agent.run({"operation": "validate", "topic": "t", "sources": src})
    returned_ids = {s["id"] for s in out["sources"]}
    assert returned_ids == {"a", "b", "c"}


# ---------------------------------------------------------------------------
# Custom minimum override
# ---------------------------------------------------------------------------

def test_custom_require_min_sources_override():
    agent = ResearchAgent()
    out = agent.run({"operation": "validate", "topic": "t", "sources": _sources("s1"), "require_min_sources": 1})
    assert out["gate_passed"] is True
    assert out["required_count"] == 1


def test_custom_require_min_sources_blocks_at_higher_threshold():
    agent = ResearchAgent()
    out = agent.run({"operation": "validate", "topic": "t", "sources": _sources("s1", "s2", "s3"),
                     "require_min_sources": 5})
    assert out["gate_passed"] is False
    assert out["missing"] == 2


# ---------------------------------------------------------------------------
# Safety — run({}) must not raise (K.11 Rule 4)
# ---------------------------------------------------------------------------

def test_safe_on_empty_input():
    """run({}) must not raise (K.11 Rule 4). Default operation is synthesise."""
    agent = ResearchAgent()
    out = agent.run({})
    assert "proposals" in out  # synthesise path returns proposals

def test_safe_on_empty_validate_input():
    """run({"operation": "validate"}) must not raise on missing keys."""
    agent = ResearchAgent()
    out = agent.run({"operation": "validate"})
    assert "gate_passed" in out
    assert out["gate_passed"] is False


# ---------------------------------------------------------------------------
# Agent identity and name
# ---------------------------------------------------------------------------

def test_agent_name():
    agent = ResearchAgent()
    assert agent.name == "research_agent"


def test_agent_imported_from_package():
    from agents import ResearchAgent as RA  # noqa: PLC0415
    assert RA is ResearchAgent


# ---------------------------------------------------------------------------
# Rationale strings are descriptive
# ---------------------------------------------------------------------------

def test_pass_rationale_mentions_count_and_topic():
    agent = ResearchAgent()
    out = agent.run({"operation": "validate", "topic": "CRISPR therapy", "sources": _sources("a", "b", "c")})
    assert "3" in out["rationale"]
    assert "CRISPR therapy" in out["rationale"]


def test_fail_rationale_mentions_missing_count():
    agent = ResearchAgent()
    out = agent.run({"operation": "validate", "topic": "fusion", "sources": _sources("s1")})
    assert "2" in out["rationale"]   # 2 more needed
    assert "BLOCKED" in out["rationale"]
