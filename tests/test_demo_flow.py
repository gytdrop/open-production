"""Tests for the shared browser/terminal demo flow."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from demo_flow import build_demo_report, generate_angles, pick_default_angle_id
from public_demo.server import render_index_html


def test_generate_angles_returns_three_angles():
    """The browser demo should surface the same three creative angles."""
    angles = generate_angles("CRISPR for sickle cell disease")
    assert len(angles) == 3
    assert {angle["id"] for angle in angles} == {"skeptic", "advocate", "contrarian"}


def test_build_demo_report_writes_audit_trail():
    """The shared flow should still write a complete audit trail."""
    scratch_dir = Path(tempfile.mkdtemp(dir=str(Path.cwd() / ".tmp")))
    audit_path = scratch_dir / "audit.jsonl"
    report = build_demo_report(
        topic="CRISPR for sickle cell disease",
        chosen_angle_id="advocate",
        audit_path=str(audit_path),
    )

    assert report["chosen_angle"]["id"] == "advocate"
    assert report["accepted_claims"] == 2
    assert report["rejected_claims"] == 1
    assert len(report["contradictions"]) == 1
    assert audit_path.exists()

    lines = audit_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 6
    entries = [json.loads(line) for line in lines]
    assert entries[0]["gate_name"] == "confirm_gate"
    assert entries[-1]["gate_name"] == "publication_gate"


def test_render_index_html_mentions_browser_demo():
    """The landing page should clearly present the browser-first experience."""
    html = render_index_html()
    assert "Guided Flow" in html or "browser demo" in html.lower()
    assert "Show creative angles" in html
    assert "Open Production" in html


def test_pick_default_angle_id_is_stable():
    """The default choice should stay deterministic for a given topic."""
    assert pick_default_angle_id("alpha") == pick_default_angle_id("alpha")


def test_build_demo_report_accepts_custom_claims():
    """build_demo_report() should use the caller-supplied claims list instead of fixture defaults."""
    import tempfile
    scratch_dir = Path(tempfile.mkdtemp(dir=str(Path.cwd() / ".tmp")))
    audit_path = scratch_dir / "audit_custom_claims.jsonl"
    custom_claims = [
        {
            "id": "x1",
            "fact_id": "test-fact",
            "conclusion": "positive",
            "text": "Custom claim with source.",
            "source_ids": ["src:001"],
        }
    ]
    report = build_demo_report(
        topic="Test topic",
        audit_path=str(audit_path),
        claims=custom_claims,
    )
    # Only 1 claim, it has source_ids → 1 accepted, 0 rejected
    assert report["accepted_claims"] == 1
    assert report["rejected_claims"] == 0
    assert len(report["evidence_results"]) == 1
    assert report["evidence_results"][0]["id"] == "x1"


def test_build_demo_report_accepts_custom_metadata():
    """build_demo_report() should use the caller-supplied metadata instead of fixture defaults."""
    import tempfile
    scratch_dir = Path(tempfile.mkdtemp(dir=str(Path.cwd() / ".tmp")))
    audit_path = scratch_dir / "audit_custom_metadata.jsonl"
    custom_metadata = {
        "doi": "10.9999/custom-test",
        "authors": ["Custom Author"],
        "date": "2026-01-01",
        "title": "Custom metadata test",
    }
    report = build_demo_report(
        topic="Test topic",
        audit_path=str(audit_path),
        metadata=custom_metadata,
    )
    # Publication gate should pass with valid custom metadata
    assert report["publication_result"]["decision_status"] == "publish_ok"
    # The evidence in the publication row should reflect our custom metadata
    assert report["publication_result"]["evidence"]["doi"] == "10.9999/custom-test"
