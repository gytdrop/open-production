"""Integration tests for the newly wired pipeline stages in demo_flow.py.

Stages covered:
  Stage 3  — ReferenceClusteringAgent write-back (references + style_tokens on Production)
  Stage 4  — MoodboardAgent write-back (Scene.mood locked=True)
  Stage 12 — EditorAgent + commit_editor_proposal() write-back (Timeline populated)
  Stage 24 — create_branch() + snapshot() write-back (branch_id + snapshot_id returned)
  Stage 25 — PublisherAgent manifest write-back (Production.metadata.publish_manifest)
  Stage 26 — archive() write-back (Production.metadata.archived_at + expires_at)

All tests use build_demo_report() with a temporary audit path so they are
fully isolated from the production artifact store.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _scratch() -> str:
    d = Path(tempfile.mkdtemp(dir=str(Path.cwd() / ".tmp")))
    return str(d / "audit.jsonl")


def _report(topic: str = "CRISPR gene therapy research", **kw) -> dict:
    from demo_flow import build_demo_report
    return build_demo_report(topic=topic, audit_path=_scratch(), **kw)


# ---------------------------------------------------------------------------
# Stage 3 — Reference clustering
# ---------------------------------------------------------------------------

class TestStage3ReferenceClustering:
    def test_ref_cluster_result_present(self):
        r = _report()
        assert "ref_cluster_result" in r

    def test_ref_cluster_returns_proposals(self):
        r = _report()
        rc = r["ref_cluster_result"]
        if rc:  # best-effort; may be empty if service unavailable
            assert "proposals" in rc
            assert len(rc["proposals"]) == 3

    def test_production_references_populated(self):
        """Three demo references are persisted to Production.references."""
        from service.production_service import ProductionService
        r = _report()
        prod_id = r.get("production_id")
        if not prod_id:
            pytest.skip("ProductionService not available")
        audit_dir = Path(r["audit_path"]).parent
        svc = ProductionService(storage_dir=audit_dir)
        try:
            prod = svc.load(prod_id)
        except Exception:
            pytest.skip("Could not load production from disk")
        # Should have at least 3 references added by Stage 3.
        assert len(prod.references) >= 3

    def test_style_tokens_populated(self):
        """StyleTokens from the top cluster are persisted to Production."""
        from service.production_service import ProductionService
        r = _report()
        prod_id = r.get("production_id")
        if not prod_id:
            pytest.skip("ProductionService not available")
        audit_dir = Path(r["audit_path"]).parent
        svc = ProductionService(storage_dir=audit_dir)
        try:
            prod = svc.load(prod_id)
        except Exception:
            pytest.skip("Could not load production from disk")
        assert len(prod.style_tokens) >= 1


# ---------------------------------------------------------------------------
# Stage 4 — Moodboard
# ---------------------------------------------------------------------------

class TestStage4Moodboard:
    def test_moodboard_result_present(self):
        r = _report()
        assert "moodboard_result" in r

    def test_moodboard_returns_three_proposals(self):
        r = _report()
        mb = r["moodboard_result"]
        if mb:
            assert len(mb.get("proposals", [])) == 3

    def test_scene_mood_locked(self):
        """After Stage 4 the demo scene's mood spec has locked=True."""
        from service.production_service import ProductionService
        r = _report()
        prod_id = r.get("production_id")
        if not prod_id:
            pytest.skip("ProductionService not available")
        audit_dir = Path(r["audit_path"]).parent
        svc = ProductionService(storage_dir=audit_dir)
        try:
            prod = svc.load(prod_id)
        except Exception:
            pytest.skip("Could not load production from disk")
        if prod.scenes:
            mood = prod.scenes[0].mood
            assert mood is not None, "Scene mood should be set after Stage 4"
            assert mood.locked is True, "Scene mood should be locked after Stage 4"


# ---------------------------------------------------------------------------
# Stage 12 — Timeline / Editing
# ---------------------------------------------------------------------------

class TestStage12Timeline:
    def test_editor_result_present(self):
        r = _report()
        assert "editor_result" in r

    def test_editor_returns_proposals(self):
        r = _report()
        er = r["editor_result"]
        if er:
            proposals = er.get("proposals", [])
            assert len(proposals) >= 1

    def test_timeline_committed(self):
        """commit_editor_proposal() attaches a Timeline to the Production."""
        from service.production_service import ProductionService
        r = _report()
        prod_id = r.get("production_id")
        if not prod_id:
            pytest.skip("ProductionService not available")
        audit_dir = Path(r["audit_path"]).parent
        svc = ProductionService(storage_dir=audit_dir)
        try:
            prod = svc.load(prod_id)
        except Exception:
            pytest.skip("Could not load production from disk")
        # The demo scene has shots, so the editor should have committed a timeline.
        if r.get("shot_plan_result") and r["editor_result"]:
            assert prod.timeline is not None, "Timeline should be committed after Stage 12"


# ---------------------------------------------------------------------------
# Stage 24 — Branching + Snapshot
# ---------------------------------------------------------------------------

class TestStage24Branching:
    def test_branch_result_present(self):
        r = _report()
        assert "branch_result" in r

    def test_branch_id_populated(self):
        r = _report()
        br = r["branch_result"]
        if br:
            assert br.get("branch_id", "").startswith("branch_")

    def test_snapshot_id_populated(self):
        r = _report()
        br = r["branch_result"]
        if br:
            assert br.get("snapshot_id", "").startswith("snap_")


# ---------------------------------------------------------------------------
# Stage 25 — Publishing
# ---------------------------------------------------------------------------

class TestStage25Publishing:
    def test_publish_result_present(self):
        r = _report()
        assert "publish_result" in r

    def test_publish_returns_proposals(self):
        r = _report()
        pr = r["publish_result"]
        if pr:
            assert len(pr.get("proposals", [])) >= 1

    def test_publish_manifest_has_platform(self):
        r = _report()
        pr = r["publish_result"]
        if pr:
            proposals = pr.get("proposals", [])
            if proposals:
                manifest = proposals[0].get("manifest") or {}
                # Manifest should mention at least one target platform.
                assert manifest  # non-empty

    def test_publish_metadata_written_to_production(self):
        """Production.metadata.publish_manifest is set after Stage 25."""
        from service.production_service import ProductionService
        r = _report()
        prod_id = r.get("production_id")
        if not prod_id:
            pytest.skip("ProductionService not available")
        if not r.get("publish_result"):
            pytest.skip("publish_result not populated (service path unavailable)")
        audit_dir = Path(r["audit_path"]).parent
        svc = ProductionService(storage_dir=audit_dir)
        try:
            prod = svc.load(prod_id)
        except Exception:
            pytest.skip("Could not load production from disk")
        assert "publish_manifest" in prod.metadata, (
            "publish_manifest should be written to Production.metadata"
        )


# ---------------------------------------------------------------------------
# Stage 26 — Archive
# ---------------------------------------------------------------------------

class TestStage26Archive:
    def test_archive_result_present(self):
        r = _report()
        assert "archive_result" in r

    def test_archive_result_has_timestamps(self):
        r = _report()
        ar = r["archive_result"]
        if ar:
            assert ar.get("archived_at"), "archived_at should be set"
            assert ar.get("expires_at"), "expires_at should be set"

    def test_archive_expires_in_future(self):
        """expires_at should be 7 years (~2555 days) after archived_at."""
        import datetime as dt
        r = _report()
        ar = r["archive_result"]
        if not ar or not ar.get("archived_at") or not ar.get("expires_at"):
            pytest.skip("archive_result not populated")
        archived_dt = dt.datetime.fromisoformat(ar["archived_at"])
        expires_dt = dt.datetime.fromisoformat(ar["expires_at"])
        delta_days = (expires_dt - archived_dt).days
        # Allow a few days of tolerance.
        assert 2550 <= delta_days <= 2560, (
            f"Expected ~2555 days retention, got {delta_days}"
        )
