"""Tests for AssetLibraryAgent — Stage 15 of the production pipeline."""
from __future__ import annotations

import pytest

from agents.asset_library import AssetLibraryAgent


@pytest.fixture
def agent():
    return AssetLibraryAgent()


# ---------------------------------------------------------------------------
# Minimal / empty production
# ---------------------------------------------------------------------------

def test_asset_library_safe_on_empty_input(agent):
    """run({}) must not raise and must return the assemble keys (K.11 rule 4)."""
    out = agent.run({})
    assert "assets" in out
    assert "gaps" in out
    assert "summary" in out
    assert "ready" in out


def test_asset_library_empty_production_has_zero_assets(agent):
    """An empty production document yields zero assets and no gaps."""
    out = agent.run({"operation": "assemble", "production": {}})
    assert out["summary"]["total"] == 0
    assert out["summary"]["gap_count"] == 0
    assert out["ready"] is True


# ---------------------------------------------------------------------------
# Production.references
# ---------------------------------------------------------------------------

def test_asset_library_collects_references(agent):
    """References in Production.references appear in the asset inventory."""
    production = {
        "references": [
            {"id": "ref_abc123", "kind": "image", "label": "Mood board image",
             "uri": "s3://bucket/mood.jpg", "sha256": "abc123"},
        ]
    }
    out = agent.run({"operation": "assemble", "production": production})
    assert out["summary"]["total"] == 1
    asset = out["assets"][0]
    assert asset["id"] == "ref_abc123"
    assert asset["kind"] == "reference"
    assert asset["status"] == "complete"
    assert asset["source"] == "Production.references"


def test_asset_library_reference_without_uri_is_gap(agent):
    """A reference with no uri and no sha256 appears in gaps."""
    production = {
        "references": [
            {"id": "ref_xyz999", "kind": "image", "label": "Placeholder",
             "uri": None, "sha256": None},
        ]
    }
    out = agent.run({"operation": "assemble", "production": production})
    assert out["summary"]["gap_count"] == 1
    assert out["ready"] is False
    gap = out["gaps"][0]
    assert gap["id"] == "ref_xyz999"
    assert "uri" in gap["reason"].lower() or "sha256" in gap["reason"].lower()


# ---------------------------------------------------------------------------
# Brand kit
# ---------------------------------------------------------------------------

def test_asset_library_collects_brand_kit_logos(agent):
    """Logos in brand_kit.logos appear in the inventory as 'logo' kind."""
    production = {
        "brand_kit": {
            "logos": [
                {"id": "ref_logo01", "kind": "image", "label": "Primary logo",
                 "uri": "s3://brand/logo.svg", "sha256": "deadbeef"},
            ],
            "palette": [],
            "typography": [],
        }
    }
    out = agent.run({"operation": "assemble", "production": production})
    logos = [a for a in out["assets"] if a["kind"] == "logo"]
    assert len(logos) == 1
    assert logos[0]["status"] == "complete"


def test_asset_library_style_tokens_do_not_generate_gaps(agent):
    """Palette and typography tokens are inline — they must NOT appear in gaps."""
    production = {
        "brand_kit": {
            "logos": [],
            "palette": [
                {"id": "tok_pal001", "name": "Primary Blue", "kind": "color", "value": "#3b82d4"},
            ],
            "typography": [
                {"id": "tok_typ001", "name": "Body Font", "kind": "composite", "value": "Inter"},
            ],
        }
    }
    out = agent.run({"operation": "assemble", "production": production})
    assert out["summary"]["gap_count"] == 0
    assert out["ready"] is True
    kinds = {a["kind"] for a in out["assets"]}
    assert "style_token:color" in kinds
    assert "style_token:typography" in kinds


# ---------------------------------------------------------------------------
# Character and environment visual anchors
# ---------------------------------------------------------------------------

def test_asset_library_collects_character_visual_anchors(agent):
    """visual_anchors on characters appear in the inventory with correct source."""
    production = {
        "characters": [
            {
                "id": "char_hero01",
                "name": "Elena",
                "visual_anchors": [
                    {"id": "ref_elena01", "kind": "image", "label": "Elena reference",
                     "uri": "s3://chars/elena.jpg", "sha256": "aabbcc"},
                ],
            }
        ]
    }
    out = agent.run({"operation": "assemble", "production": production})
    anchors = [a for a in out["assets"] if a["kind"] == "visual_anchor"]
    assert len(anchors) == 1
    assert "Elena" in anchors[0]["source"]


def test_asset_library_character_anchor_without_uri_is_gap(agent):
    """A character visual_anchor with no uri and no sha256 is a gap."""
    production = {
        "characters": [
            {
                "id": "char_hero02",
                "name": "Marcus",
                "visual_anchors": [
                    {"id": "ref_marcus01", "kind": "image", "label": "Marcus ref",
                     "uri": None, "sha256": None},
                ],
            }
        ]
    }
    out = agent.run({"operation": "assemble", "production": production})
    assert out["summary"]["gap_count"] == 1
    assert out["gaps"][0]["id"] == "ref_marcus01"


def test_asset_library_collects_environment_visual_anchors(agent):
    """visual_anchors on environments appear in the inventory."""
    production = {
        "environments": [
            {
                "id": "env_office01",
                "name": "The Office",
                "visual_anchors": [
                    {"id": "ref_off01", "kind": "image", "label": "Office ref",
                     "uri": "s3://env/office.jpg", "sha256": "112233"},
                ],
            }
        ]
    }
    out = agent.run({"operation": "assemble", "production": production})
    anchors = [a for a in out["assets"] if a["kind"] == "visual_anchor"]
    assert len(anchors) == 1
    assert "The Office" in anchors[0]["source"]


# ---------------------------------------------------------------------------
# check_gaps operation
# ---------------------------------------------------------------------------

def test_asset_library_check_gaps_operation(agent):
    """check_gaps returns gaps, gap_count, and ready without the full asset list."""
    production = {
        "references": [
            {"id": "ref_miss01", "kind": "video", "label": "Missing clip",
             "uri": None, "sha256": None},
        ]
    }
    out = agent.run({"operation": "check_gaps", "production": production})
    assert "gaps" in out
    assert "gap_count" in out
    assert "ready" in out
    # Should NOT include the full asset inventory in a check_gaps response
    assert "assets" not in out
    assert out["gap_count"] == 1
    assert out["ready"] is False


def test_asset_library_check_gaps_ready_when_no_gaps(agent):
    """check_gaps returns ready=True when all references have URIs."""
    production = {
        "references": [
            {"id": "ref_ok001", "kind": "image", "label": "OK ref",
             "uri": "s3://bucket/ok.jpg", "sha256": "001122"},
        ]
    }
    out = agent.run({"operation": "check_gaps", "production": production})
    assert out["ready"] is True
    assert out["gap_count"] == 0


# ---------------------------------------------------------------------------
# Summary accuracy
# ---------------------------------------------------------------------------

def test_asset_library_summary_counts_are_accurate(agent):
    """summary.total == complete + incomplete, gap_count matches len(gaps)."""
    production = {
        "references": [
            {"id": "ref_a0001", "kind": "image", "label": "A",
             "uri": "s3://x/a.jpg", "sha256": None},        # complete (has uri)
            {"id": "ref_b0001", "kind": "image", "label": "B",
             "uri": None, "sha256": None},                   # incomplete → gap
        ]
    }
    out = agent.run({"operation": "assemble", "production": production})
    s = out["summary"]
    assert s["total"] == 2
    assert s["complete"] == 1
    assert s["incomplete"] == 1
    assert s["gap_count"] == len(out["gaps"])


# ---------------------------------------------------------------------------
# Scope contract
# ---------------------------------------------------------------------------

def test_asset_library_writable_fields_contract(agent):
    """WRITABLE_FIELDS must only include Production.metadata."""
    assert AssetLibraryAgent.WRITABLE_FIELDS == frozenset({"Production.metadata"})
