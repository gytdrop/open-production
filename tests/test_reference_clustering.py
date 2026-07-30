"""Tests for ReferenceClusteringAgent — Pipeline Stage 3 of open-production-plan.md."""
from __future__ import annotations

import pytest

from agents.reference_clustering import ReferenceClusteringAgent


@pytest.fixture
def agent():
    return ReferenceClusteringAgent()


# ── cluster operation ────────────────────────────────────────────────────────

def test_cluster_returns_three_proposals(agent):
    """cluster operation always returns exactly 3 proposals."""
    out = agent.run({
        "operation": "cluster",
        "references": [
            {"id": "ref_0001", "kind": "image", "label": "warm afternoon interior"},
            {"id": "ref_0002", "kind": "image", "label": "golden hour exterior"},
        ],
    })
    assert "proposals" in out
    assert len(out["proposals"]) == 3


def test_cluster_proposals_have_required_fields(agent):
    """Each proposal must have cluster_name, dominant_tone, style_tokens, mood_keywords, rationale."""
    out = agent.run({
        "references": [{"id": "ref_0001", "kind": "image", "label": "natural daylight"}],
    })
    for p in out["proposals"]:
        assert "cluster_name" in p
        assert "dominant_tone" in p
        assert "style_tokens" in p
        assert isinstance(p["style_tokens"], list)
        assert "mood_keywords" in p
        assert "rationale" in p


def test_cluster_reference_count_in_proposals(agent):
    """Each proposal carries a reference_count equal to the number of references supplied."""
    refs = [
        {"id": "ref_0001", "kind": "image", "label": "a"},
        {"id": "ref_0002", "kind": "image", "label": "b"},
        {"id": "ref_0003", "kind": "image", "label": "c"},
    ]
    out = agent.run({"references": refs})
    for p in out["proposals"]:
        assert p["reference_count"] == 3


def test_cluster_stylised_label_routes_to_stylised_family(agent):
    """References with 'neon' or 'graphic' in labels should route to the stylised template family."""
    out = agent.run({
        "references": [
            {"id": "ref_0001", "kind": "image", "label": "neon urban night"},
            {"id": "ref_0002", "kind": "image", "label": "bold geometric signage"},
        ],
    })
    cluster_names = [p["cluster_name"].lower() for p in out["proposals"]]
    assert any(k in " ".join(cluster_names) for k in ("graphic", "neon", "modern", "painterly", "soft"))


def test_cluster_naturalistic_label_routes_to_naturalistic_family(agent):
    """References with natural/organic labels route to the naturalistic family."""
    out = agent.run({
        "references": [
            {"id": "ref_0001", "kind": "image", "label": "overcast morning landscape"},
        ],
    })
    cluster_names = [p["cluster_name"].lower() for p in out["proposals"]]
    assert any(k in " ".join(cluster_names) for k in ("golden", "verite", "dusk", "natural", "overcast"))


def test_cluster_safe_on_empty_input(agent):
    """run({}) must return valid proposals and never raise (K.11 rule 4)."""
    out = agent.run({})
    assert "proposals" in out
    assert len(out["proposals"]) == 3


def test_cluster_reference_count_in_root_output(agent):
    """Top-level reference_count in the output dict matches len(references)."""
    refs = [{"id": "ref_0001", "kind": "image", "label": "x"}]
    out = agent.run({"references": refs})
    assert out["reference_count"] == 1


# ── validate operation ───────────────────────────────────────────────────────

def test_validate_passes_with_labelled_references(agent):
    """validate operation returns valid=True when references are supplied and labelled."""
    out = agent.run({
        "operation": "validate",
        "references": [
            {"id": "ref_0001", "kind": "image", "label": "warm afternoon"},
        ],
    })
    assert out["valid"] is True
    assert out["issues"] == []


def test_validate_fails_with_no_references(agent):
    """validate returns valid=False and an explanatory issue when the list is empty."""
    out = agent.run({"operation": "validate", "references": []})
    assert out["valid"] is False
    assert len(out["issues"]) >= 1
    assert any("reference" in i.lower() for i in out["issues"])


def test_validate_fails_when_reference_has_no_label(agent):
    """validate returns valid=False when a reference has an empty label."""
    out = agent.run({
        "operation": "validate",
        "references": [
            {"id": "ref_0001", "kind": "image", "label": ""},
        ],
    })
    assert out["valid"] is False
    assert any("label" in i.lower() for i in out["issues"])


def test_validate_reference_count_in_output(agent):
    """validate output always includes reference_count."""
    refs = [
        {"id": "ref_0001", "kind": "image", "label": "a"},
        {"id": "ref_0002", "kind": "image", "label": "b"},
    ]
    out = agent.run({"operation": "validate", "references": refs})
    assert out["reference_count"] == 2


def test_validate_safe_on_missing_references_key(agent):
    """validate with no 'references' key treats it as empty and returns valid=False."""
    out = agent.run({"operation": "validate"})
    assert out["valid"] is False


# ── scope contract ───────────────────────────────────────────────────────────

def test_writable_fields_declared():
    """WRITABLE_FIELDS must be declared on the class."""
    from agents.reference_clustering import ReferenceClusteringAgent
    assert ReferenceClusteringAgent.WRITABLE_FIELDS is not None
    assert "Production.references" in ReferenceClusteringAgent.WRITABLE_FIELDS
