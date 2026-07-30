"""Tests for ``python -m src.cli.run`` (the keystone production-run command).

Locks in the user-visible behavior of the runner so that the
``production run "<intent>"`` entry point keeps working as the project
grows. Covers:

  1. Happy path with --no-confirm: production.json + audit.jsonl present,
     >= 18 audit lines, one gate_decision per required gate type.
  2. Re-running with the same intent creates a SECOND production
     (idempotent on out_dir).
  3. --pick forces that angle through ConfirmGate even with --no-confirm.
  4. A stage that returns empty proposals does NOT crash the pipeline;
     emits a "no proposals" audit event and the next stage still runs.
  5. End-to-end: the resulting production.json validates against
     docs/schema/production-document.schema.json.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "docs" / "schema" / "production-document.schema.json"
)


def _run_subprocess(cmd, cwd):
    return subprocess.run(
        [sys.executable, *cmd],
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )


def _load_audit_entries(prod_dir):
    text = (prod_dir / "audit.jsonl").read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# 1. Happy path with --no-confirm
# ---------------------------------------------------------------------------

class TestHappyPath:
    def test_production_json_and_audit_jsonl_exist(self, tmp_path):
        out_dir = tmp_path / "productions"
        result = _run_subprocess(
            [
                "-m", "src.cli.run",
                "CRISPR for sickle cell",
                "--no-confirm",
                "--out", str(out_dir),
            ],
            Path.cwd(),
        )
        assert result.returncode == 0, result.stderr
        prod_dirs = [p for p in out_dir.iterdir() if p.is_dir()]
        assert len(prod_dirs) == 1, f"expected one production, got {prod_dirs}"
        prod_dir = prod_dirs[0]
        assert (prod_dir / "production.json").is_file()
        assert (prod_dir / "audit.jsonl").is_file()

    def test_audit_has_at_least_eighteen_stage_entries(self, tmp_path):
        out_dir = tmp_path / "productions"
        result = _run_subprocess(
            [
                "-m", "src.cli.run",
                "CRISPR for sickle cell",
                "--no-confirm",
                "--out", str(out_dir),
            ],
            Path.cwd(),
        )
        assert result.returncode == 0, result.stderr
        prod_dir = next(p for p in out_dir.iterdir() if p.is_dir())
        entries = _load_audit_entries(prod_dir)
        assert len(entries) >= 18, (
            f"expected >=18 audit entries (one per wired stage), got {len(entries)}"
        )

    def test_at_least_one_gate_decision_per_required_gate_type(self, tmp_path):
        out_dir = tmp_path / "productions"
        result = _run_subprocess(
            [
                "-m", "src.cli.run",
                "CRISPR for sickle cell",
                "--no-confirm",
                "--out", str(out_dir),
            ],
            Path.cwd(),
        )
        assert result.returncode == 0, result.stderr
        prod_dir = next(p for p in out_dir.iterdir() if p.is_dir())
        entries = _load_audit_entries(prod_dir)
        gate_decisions = [
            e for e in entries
            if e.get("action_type") == "gate_decision" and e.get("gate_name")
        ]
        seen_gates = {g["gate_name"] for g in gate_decisions}
        for required in ("evidence", "consistency", "consistency_contract", "publication"):
            assert any(required in g for g in seen_gates), (
                f"missing gate_decision for {required!r}; saw {sorted(seen_gates)}"
            )


# ---------------------------------------------------------------------------
# 2. Idempotent re-run with the same intent
# ---------------------------------------------------------------------------

class TestIdempotentRerun:
    def test_re_run_creates_second_production(self, tmp_path):
        out_dir = tmp_path / "productions"
        out_dir.mkdir()

        first = _run_subprocess(
            [
                "-m", "src.cli.run",
                "CRISPR for sickle cell",
                "--no-confirm",
                "--out", str(out_dir),
            ],
            Path.cwd(),
        )
        assert first.returncode == 0, first.stderr

        second = _run_subprocess(
            [
                "-m", "src.cli.run",
                "CRISPR for sickle cell",
                "--no-confirm",
                "--out", str(out_dir),
            ],
            Path.cwd(),
        )
        assert second.returncode == 0, second.stderr

        prod_dirs = sorted(p for p in out_dir.iterdir() if p.is_dir())
        assert len(prod_dirs) >= 2, (
            f"second run should create a fresh production, got {prod_dirs}"
        )
        for prod_dir in prod_dirs:
            assert (prod_dir / "audit.jsonl").is_file()
            assert (prod_dir / "production.json").is_file()


# ---------------------------------------------------------------------------
# 3. --pick forces that angle through ConfirmGate
# ---------------------------------------------------------------------------

class TestPickAngle:
    def test_pick_skeptic_with_no_confirm(self, tmp_path):
        out_dir = tmp_path / "productions"
        result = _run_subprocess(
            [
                "-m", "src.cli.run",
                "CRISPR for sickle cell",
                "--no-confirm",
                "--pick", "skeptic",
                "--out", str(out_dir),
            ],
            Path.cwd(),
        )
        assert result.returncode == 0, result.stderr
        prod_dir = next(p for p in out_dir.iterdir() if p.is_dir())
        entries = _load_audit_entries(prod_dir)
        confirm = [
            e for e in entries
            if e.get("action_type") == "gate_decision"
            and e.get("gate_name") == "confirm_gate"
        ]
        assert confirm, "expected at least one confirm_gate gate_decision"
        assert confirm[0].get("claim_id") == "skeptic", (
            f"--pick skeptic should record claim_id=skeptic, got {confirm[0]}"
        )
        assert confirm[0].get("decision_status") == "accepted"


# ---------------------------------------------------------------------------
# 4. Empty proposals from a stage don't crash the pipeline
# ---------------------------------------------------------------------------

class TestEmptyProposalsAreTolerated:
    def test_empty_proposal_stage_emits_no_proposals_event(self, tmp_path, monkeypatch):
        """If a stage returns empty proposals, the runner must NOT crash; it
        must emit a 'no proposals' audit event and continue."""

        # Monkeypatch MoodboardAgent to return an empty proposal list.
        from src.agents import moodboard as moodboard_module

        original_run = moodboard_module.MoodboardAgent.run

        def empty_run(self, input):
            result = original_run(self, input)
            result["proposals"] = []
            return result

        monkeypatch.setattr(moodboard_module.MoodboardAgent, "run", empty_run)

        from src.agents.confirm_gate import AutoConfirmSink
        from src.schema.production_document import IntentDocument
        from src.service.pipeline_runner import PipelineRunner

        out_dir = tmp_path / "productions"
        out_dir.mkdir(parents=True, exist_ok=True)
        intent = IntentDocument(
            topic="CRISPR for sickle cell",
            audience="educated_lay",
            tone="neutral",
            platform="youtube",
        )
        runner = PipelineRunner(sink=AutoConfirmSink(choice="advocate"))
        production = runner.run(intent, out_dir)

        prod_dir = out_dir / production.id
        assert (prod_dir / "production.json").is_file()
        assert (prod_dir / "audit.jsonl").is_file()

        entries = _load_audit_entries(prod_dir)
        no_proposal_events = [
            e for e in entries
            if (e.get("payload") or {}).get("no_proposals") is True
        ]
        assert no_proposal_events, (
            "expected at least one 'no proposals' audit event when a stage "
            "returns empty proposals"
        )
        actors = [e.get("actor") for e in no_proposal_events]
        assert "moodboard" in actors, (
            f"moodboard should be the empty actor, saw {actors}"
        )

        later_actors = [
            e.get("actor") for e in entries
            if e.get("actor") in ("story", "script", "shot_designer", "shot_planner")
        ]
        assert later_actors, (
            "expected at least one later stage to still emit an event after "
            "the empty moodboard stage"
        )


# ---------------------------------------------------------------------------
# 5. End-to-end schema validation
# ---------------------------------------------------------------------------

class TestSchemaValidation:
    def test_production_json_validates_against_schema(self, tmp_path):
        """The resulting production.json must structurally validate against the JSON schema.

        Uses the same structural rules as ``production doctor`` (which is the
        canonical "is this production healthy?" check in this project): we
        strip optional nulls before validating and ignore enum/pattern/format
        noise. Required fields, root types, and top-level shape must all match.
        """
        from tests._schema_check import validate_production_structurally

        out_dir = tmp_path / "productions"
        result = _run_subprocess(
            [
                "-m", "src.cli.run",
                "CRISPR for sickle cell",
                "--no-confirm",
                "--out", str(out_dir),
            ],
            Path.cwd(),
        )
        assert result.returncode == 0, result.stderr
        prod_dir = next(p for p in out_dir.iterdir() if p.is_dir())
        doc = json.loads((prod_dir / "production.json").read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        validate_production_structurally(doc, schema)

