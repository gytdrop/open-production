"""Tests for the ``src.cli.timeline`` command.

Covers the lookup helper, the audit/header readers, the renderer (with and
without the per-event table), and the ``python -m src.cli.timeline`` entry
point itself via subprocess. The goal is to lock in the user-visible behavior
so the audit trail stays a first-class deliverable.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from cli._production_dir import (
    ProductionNotFoundError,
    find_production_dir,
    load_audit_entries,
    load_production_header,
)
from cli.timeline import (
    _classify_decision,
    _gate_counts,
    _state_progression,
    _summarize_entry,
    main,
    render_timeline,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def prod_dir(tmp_path: Path) -> Path:
    """Write a small, deterministic production under tmp_path."""
    d = tmp_path / "prod_abc123def456"
    d.mkdir()
    audit = d / "audit.jsonl"
    entries = [
        {
            "id": "evt_init_0001",
            "ts": "2026-07-29T10:00:00.000000+00:00",
            "actor": "system",
            "action_type": "system",
            "gate_name": None,
            "claim_id": None,
            "decision_status": None,
            "reason": None,
            "evidence": {},
            "payload": {"operation": "init", "title": "CRISPR 101"},
            "state_before": None,
            "state_after": "h0001",
        },
        {
            "id": "evt_gate_0002",
            "ts": "2026-07-29T10:00:00.020000+00:00",
            "actor": "demo_flow.build_demo_report",
            "action_type": "gate_decision",
            "gate_name": "evidence_gate",
            "claim_id": "c1",
            "decision_status": "accepted",
            "reason": "has sources",
            "evidence": {"source_ids": ["pubmed:1"]},
            "payload": {},
            "state_before": None,
            "state_after": None,
        },
        {
            "id": "evt_gate_0003",
            "ts": "2026-07-29T10:00:00.025000+00:00",
            "actor": "demo_flow.build_demo_report",
            "action_type": "gate_decision",
            "gate_name": "evidence_gate",
            "claim_id": "c2",
            "decision_status": "rejected",
            "reason": "no source_ids",
            "evidence": {"source_ids": []},
            "payload": {},
            "state_before": None,
            "state_after": None,
        },
        {
            "id": "evt_trans_0004",
            "ts": "2026-07-29T10:00:00.030000+00:00",
            "actor": "demo_flow",
            "action_type": "state_transition",
            "gate_name": None,
            "claim_id": None,
            "decision_status": None,
            "reason": None,
            "evidence": {},
            "payload": {"next_state": "BRIEFED"},
            "state_before": None,
            "state_after": None,
        },
        # A malformed line that should be skipped silently.
        "this is not json\n",
    ]
    # Re-open the fixture and write a known-bad line interleaved with the
    # valid entries to prove malformed lines don't crash the reader.
    audit.write_text("\n".join(json.dumps(e) for e in entries[:4]) + "\n"
                     + "this is not json\n", encoding="utf-8")
    # Write a minimal production.json so the header is parsed.
    state = {
        "production_id": "prod_abc123def456",
        "state": "PUBLISHED",
        "metadata": {"title": "CRISPR 101"},
        "audit_trail": [
            {
                "action_type": "system",
                "payload": {"operation": "init", "title": "CRISPR 101"},
            }
        ],
    }
    (d / "production.json").write_text(json.dumps(state), encoding="utf-8")
    return d


# ---------------------------------------------------------------------------
# find_production_dir
# ---------------------------------------------------------------------------

class TestFindProductionDir:
    def test_resolves_explicit_path(self, prod_dir: Path) -> None:
        result = find_production_dir(str(prod_dir))
        assert result.resolve() == prod_dir.resolve()

    def test_searches_known_storage_roots(self, prod_dir: Path, tmp_path: Path) -> None:
        # Move the prod dir under output/public-demo and search from tmp_path
        # as the project root.
        public = tmp_path / "output" / "public-demo"
        public.mkdir(parents=True)
        target = public / prod_dir.name
        prod_dir.rename(target)
        result = find_production_dir(prod_dir.name, project_root=tmp_path)
        assert result == target.resolve()

    def test_searches_productions_root(self, prod_dir: Path, tmp_path: Path) -> None:
        prod = tmp_path / "output" / "productions"
        prod.mkdir(parents=True)
        target = prod / prod_dir.name
        prod_dir.rename(target)
        result = find_production_dir(prod_dir.name, project_root=tmp_path)
        assert result == target.resolve()

    def test_searches_project_root(self, prod_dir: Path, tmp_path: Path) -> None:
        # No output/ directory: should fall back to the project root.
        target = tmp_path / prod_dir.name
        prod_dir.rename(target)
        result = find_production_dir(prod_dir.name, project_root=tmp_path)
        assert result == target.resolve()

    def test_missing_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ProductionNotFoundError):
            find_production_dir("prod_nope_nope", project_root=tmp_path)

    def test_explicit_path_without_audit_raises(self, tmp_path: Path) -> None:
        d = tmp_path / "prod_nope"
        d.mkdir()
        with pytest.raises(ProductionNotFoundError):
            find_production_dir(str(d))


# ---------------------------------------------------------------------------
# load_audit_entries
# ---------------------------------------------------------------------------

class TestLoadAuditEntries:
    def test_parses_valid_entries(self, prod_dir: Path) -> None:
        entries = load_audit_entries(prod_dir)
        assert len(entries) == 4
        assert entries[0]["id"] == "evt_init_0001"
        assert entries[-1]["action_type"] == "state_transition"

    def test_skips_malformed_lines(self, prod_dir: Path) -> None:
        entries = load_audit_entries(prod_dir)
        # The 5th line ("this is not json") is dropped silently.
        assert all(isinstance(e, dict) for e in entries)
        assert len(entries) == 4

    def test_empty_file_returns_empty_list(self, tmp_path: Path) -> None:
        d = tmp_path / "prod_empty"
        d.mkdir()
        (d / "audit.jsonl").write_text("", encoding="utf-8")
        assert load_audit_entries(d) == []

    def test_missing_file_returns_empty_list(self, tmp_path: Path) -> None:
        d = tmp_path / "prod_empty"
        d.mkdir()
        assert load_audit_entries(d) == []


# ---------------------------------------------------------------------------
# load_production_header
# ---------------------------------------------------------------------------

class TestLoadProductionHeader:
    def test_reads_title_from_metadata(self, prod_dir: Path) -> None:
        header = load_production_header(prod_dir)
        assert header["title"] == "CRISPR 101"
        assert header["state"] == "PUBLISHED"
        assert header["production_id"] == "prod_abc123def456"

    def test_falls_back_to_payload_title(self, tmp_path: Path) -> None:
        d = tmp_path / "prod_x"
        d.mkdir()
        (d / "production.json").write_text(
            json.dumps(
                {
                    "production_id": "prod_x",
                    "state": "DRAFT",
                    "audit_trail": [
                        {"payload": {"operation": "init", "title": "From Payload"}}
                    ],
                }
            ),
            encoding="utf-8",
        )
        header = load_production_header(d)
        assert header["title"] == "From Payload"

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        d = tmp_path / "prod_x"
        d.mkdir()
        assert load_production_header(d) == {}

    def test_malformed_json_returns_empty(self, tmp_path: Path) -> None:
        d = tmp_path / "prod_x"
        d.mkdir()
        (d / "production.json").write_text("{not json", encoding="utf-8")
        assert load_production_header(d) == {}


# ---------------------------------------------------------------------------
# Classification + aggregation helpers
# ---------------------------------------------------------------------------

class TestClassification:
    def test_pass_decisions(self) -> None:
        for s in ("accepted", "pass", "publish_ok", "ok", "approved"):
            assert _classify_decision(s) == "pass"

    def test_fail_decisions(self) -> None:
        for s in ("rejected", "fail", "blocked",
                  "sources_insufficient", "contradiction_detected"):
            assert _classify_decision(s) == "fail"

    def test_warn_decision(self) -> None:
        assert _classify_decision("something_else") == "warn"
        assert _classify_decision(None) == "-"


class TestAggregation:
    def test_gate_counts(self) -> None:
        entries = [
            {"action_type": "gate_decision", "gate_name": "evidence_gate",
             "decision_status": "accepted"},
            {"action_type": "gate_decision", "gate_name": "evidence_gate",
             "decision_status": "accepted"},
            {"action_type": "gate_decision", "gate_name": "evidence_gate",
             "decision_status": "rejected"},
            {"action_type": "system"},  # ignored
        ]
        counts = _gate_counts(entries)
        assert counts == {"evidence_gate:accepted": 2, "evidence_gate:rejected": 1}

    def test_state_progression_preserves_order(self) -> None:
        entries = [
            {"action_type": "system"},
            {"action_type": "state_transition", "payload": {"next_state": "BRIEFED"}},
            {"action_type": "state_transition", "payload": {"next_state": "IN_PRODUCTION"}},
            {"action_type": "state_transition", "payload": {"next_state": "PUBLISHED"}},
        ]
        assert _state_progression(entries) == ["BRIEFED", "IN_PRODUCTION", "PUBLISHED"]


class TestSummarizeEntry:
    def test_gate_decision_subject_contains_claim(self) -> None:
        entry = {
            "action_type": "gate_decision",
            "actor": "agent_x",
            "gate_name": "evidence_gate",
            "claim_id": "c7",
            "decision_status": "accepted",
            "reason": "has sources",
            "evidence": {},
            "payload": {},
        }
        kind, actor, subject, glyph, summary = _summarize_entry(entry)
        assert kind == "gate_decision"
        assert actor == "agent_x"
        assert subject == "evidence_gate:c7"
        assert glyph == "+"
        assert "has sources" in summary

    def test_state_transition_subject(self) -> None:
        entry = {
            "action_type": "state_transition",
            "actor": "demo_flow",
            "payload": {"next_state": "IN_REVIEW"},
            "evidence": {},
        }
        _, _, subject, _, _ = _summarize_entry(entry)
        assert subject == "->IN_REVIEW"

    def test_timeline_assembly_subject(self) -> None:
        entry = {
            "action_type": "timeline_assembly",
            "actor": "editor_agent",
            "payload": {"proposal_label": "Balanced edit",
                        "shot_count": 3, "total_duration_sec": 12.0},
            "evidence": {},
        }
        _, _, subject, _, summary = _summarize_entry(entry)
        assert subject == "editor"
        assert "Balanced edit" in summary
        assert "3 shots" in summary
        assert "12.0s" in summary

    def test_unknown_action_type_falls_back(self) -> None:
        entry = {
            "action_type": "future_kind",
            "actor": "someone",
            "payload": {"foo": "bar"},
            "evidence": {},
        }
        _, _, subject, _, _ = _summarize_entry(entry)
        assert subject == "future_kind"


# ---------------------------------------------------------------------------
# render_timeline
# ---------------------------------------------------------------------------

class TestRenderTimeline:
    def test_empty_audit_renders_header_with_no_events(self, tmp_path: Path) -> None:
        d = tmp_path / "prod_empty"
        d.mkdir()
        (d / "audit.jsonl").write_text("", encoding="utf-8")
        (d / "production.json").write_text(
            json.dumps(
                {"production_id": "prod_empty", "state": "DRAFT",
                 "metadata": {"title": "Nothing"}, "audit_trail": []}
            ),
            encoding="utf-8",
        )
        text = render_timeline(d)
        assert "Production prod_empty" in text
        assert "Nothing" in text
        assert "Entries: 0" in text
        assert "(no audit entries recorded)" in text

    def test_full_render_contains_every_entry(self, prod_dir: Path) -> None:
        text = render_timeline(prod_dir)
        assert "CRISPR 101" in text
        assert "PUBLISHED" in text
        assert "Entries: 4" in text
        # gate decisions rendered with + and x glyphs
        assert "evidence_gate:c1" in text
        assert "evidence_gate:c2" in text
        assert "+" in text
        assert "x" in text
        # state transition rendered
        assert "->BRIEFED" in text

    def test_summary_only_skips_per_event_table(self, prod_dir: Path) -> None:
        text = render_timeline(prod_dir, summary_only=True)
        assert "CRISPR 101" in text
        assert "Gate decisions:" in text
        # The per-event table header must NOT be present in summary mode.
        assert "actor" not in text.split("Gate decisions:")[1]
        # And no separator dashes from the table either.
        assert "----" not in text


# ---------------------------------------------------------------------------
# main() and the python -m entry point
# ---------------------------------------------------------------------------

class TestMain:
    def test_main_returns_zero_on_hit(self, prod_dir: Path, capsys) -> None:
        rc = main([str(prod_dir)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "CRISPR 101" in out
        assert "evidence_gate:c1" in out

    def test_main_returns_zero_for_summary(self, prod_dir: Path, capsys) -> None:
        rc = main([str(prod_dir), "--summary"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Gate decisions:" in out
        assert "evidence_gate" in out
        # No per-event rows.
        assert "no source_ids" not in out

    def test_main_returns_zero_for_json(self, prod_dir: Path, capsys) -> None:
        rc = main([str(prod_dir), "--json"])
        assert rc == 0
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed["header"]["title"] == "CRISPR 101"
        assert parsed["entry_count"] == 4
        assert "evidence_gate:accepted" in parsed["gate_decisions"]

    def test_main_returns_one_on_missing(self, capsys) -> None:
        rc = main(["prod_does_not_exist_xyz"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "not found" in err

    def test_subprocess_invocation(self, prod_dir: Path) -> None:
        """End-to-end check: ``python -m src.cli.timeline <path>`` works."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.timeline",
             "--project-root", str(prod_dir.parent), prod_dir.name],
            capture_output=True,
            text=True,
            cwd=str(Path.cwd()),
        )
        assert result.returncode == 0, result.stderr
        assert "CRISPR 101" in result.stdout
        assert "evidence_gate:c1" in result.stdout

    def test_subprocess_json_invocation(self, prod_dir: Path) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.timeline", str(prod_dir), "--json"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        parsed = json.loads(result.stdout)
        assert parsed["header"]["title"] == "CRISPR 101"
        assert parsed["entry_count"] == 4

    def test_subprocess_missing_returns_one(self, prod_dir: Path) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.timeline", "prod_no_such_prod_zzz",
             "--project-root", str(prod_dir.parent)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "not found" in result.stderr
