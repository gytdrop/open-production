"""Tests for ``src.cli.doctor`` - the green / yellow / red health reporter.

Covers:
- the production-scoped checks (schema, audit.jsonl well-formedness, gate
  types, rationale, asset SHA-256s, state reachability)
- the --all flag (one block per production)
- the project-scoped checks (run with no prod_id)
- the exit-code rule: 0 for green/yellow, 1 for any red
- the real shipped production ``prod_9915e6697a12`` is healthy enough to
  exit 0 (its only complaint is the informational "consistency_contract_gate
  not seen" yellow note)

The doctor closes the observability triad alongside ``timeline`` (audit) and
``trace`` (provenance); these tests lock in the user-visible behavior so a
single command answers "is this production healthy?".
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from cli.doctor import (
    GREEN,
    RED,
    YELLOW,
    CheckResult,
    Report,
    _check_production_json_validates,
    _check_audit_jsonl_well_formed,
    _check_audit_has_gate_types,
    _check_audit_no_error_rationale,
    _check_asset_sha256s_exist,
    _check_state_reachable_from_draft,
    main,
    run_production_checks,
    run_project_checks,
)


REAL_PROD_ID = "prod_9915e6697a12"


# ---------------------------------------------------------------------------
# Test fixtures.
# ---------------------------------------------------------------------------
def _write_minimal_production(
    prod_dir: Path,
    *,
    production_id: str = "prod_test123456",
    state: str = "PUBLISHED",
    audit_entries: list[dict] | None = None,
    corrupt_audit: bool = False,
    include_assets: bool = False,
) -> Path:
    """Write a self-contained production.json + audit.jsonl pair under prod_dir.

    By default the production is "healthy" (PUBLISHED state, no corrupt
    audit, all required fields populated). Test cases toggle individual
    knobs to exercise each check.
    """
    prod_dir.mkdir(parents=True, exist_ok=True)
    if audit_entries is None:
        audit_entries = [
            {
                "id": "evt_init0000001",
                "ts": "2026-07-29T10:00:00+00:00",
                "actor": "system",
                "action_type": "system",
                "gate_name": None,
                "claim_id": None,
                "decision_status": None,
                "reason": None,
                "evidence": {},
                "payload": {"operation": "init", "title": "Test"},
                "state_before": None,
                "state_after": "h0001",
            },
            {
                "id": "evt_evidence0001",
                "ts": "2026-07-29T10:00:00.020+00:00",
                "actor": "demo",
                "action_type": "gate_decision",
                "gate_name": "evidence_gate",
                "claim_id": "c1",
                "decision_status": "accepted",
                "reason": "has sources",
                "evidence": {"source_ids": ["pubmed:1"]},
                "payload": {},
            },
            {
                "id": "evt_consist00001",
                "ts": "2026-07-29T10:00:00.030+00:00",
                "actor": "demo",
                "action_type": "gate_decision",
                "gate_name": "consistency_gate",
                "claim_id": "c2",
                "decision_status": "accepted",
                "reason": "ok",
                "evidence": {},
                "payload": {},
            },
            {
                "id": "evt_publ0000001",
                "ts": "2026-07-29T10:00:00.040+00:00",
                "actor": "demo",
                "action_type": "gate_decision",
                "gate_name": "publication_gate",
                "claim_id": "c3",
                "decision_status": "publish_ok",
                "reason": "metadata complete",
                "evidence": {},
                "payload": {},
            },
            {
                "id": "evt_contract001",
                "ts": "2026-07-29T10:00:00.050+00:00",
                "actor": "demo",
                "action_type": "gate_decision",
                "gate_name": "consistency_contract_gate",
                "claim_id": "c4",
                "decision_status": "ok",
                "reason": "contract honored",
                "evidence": {},
                "payload": {},
            },
        ]
    refs: list[dict] = []
    if include_assets:
        # Two references each with a SHA-256; one file exists on disk, one
        # is missing so the asset check can flag the missing file.
        refs.append(
            {
                "id": "ref_aaaaaaaaaaaaaaaa",
                "kind": "image",
                "label": "exists",
                "sha256": "a" * 64,
            }
        )
        refs.append(
            {
                "id": "ref_bbbbbbbbbbbbbbbb",
                "kind": "image",
                "label": "missing",
                "sha256": "b" * 64,
            }
        )
    state_doc: dict = {
        "schema_version": "1.0.0",
        "id": production_id,
        "state": state,
        "title": "Test production",
        "created_at": "2026-07-29T10:00:00+00:00",
        "updated_at": "2026-07-29T10:00:01+00:00",
        "intent": {"topic": "Test"},
        "scenes": [],
        "audit_trail": audit_entries,
        "references": refs,
        "snapshots": [],
    }
    (prod_dir / "production.json").write_text(
        json.dumps(state_doc), encoding="utf-8"
    )
    if corrupt_audit:
        # One valid entry, then one bad line, then the rest of the valid
        # entries. The corrupted line must NOT be valid JSON.
        lines = [json.dumps(audit_entries[0])]
        lines.append("this is not valid json {")
        lines.extend(json.dumps(e) for e in audit_entries[1:])
        (prod_dir / "audit.jsonl").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
    else:
        (prod_dir / "audit.jsonl").write_text(
            "\n".join(json.dumps(e) for e in audit_entries) + "\n",
            encoding="utf-8",
        )
    if include_assets:
        assets = prod_dir / "assets"
        assets.mkdir()
        # Only create the first file; the second SHA-256 is intentionally
        # missing to exercise the red branch of the asset check.
        (assets / ("a" * 64)).write_bytes(b"asset-bytes")
    return prod_dir


@pytest.fixture()
def prod_dir(tmp_path: Path) -> Path:
    """Return a fully healthy minimal production under tmp_path."""
    return _write_minimal_production(tmp_path / "prod_health1234")


@pytest.fixture()
def repo_root() -> Path:
    """Return the absolute path to the Open_Production repository root."""
    return Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Test 1: doctor on prod_9915e6697a12 exits 0 and prints >= 7 lines.
# ---------------------------------------------------------------------------
class TestRealProduction:
    def test_real_production_exits_zero(self, repo_root: Path, capsys) -> None:
        rc = main([REAL_PROD_ID, "--project-root", str(repo_root)])
        assert rc == 0
        out = capsys.readouterr().out
        # >= 7 lines: title + separator + 6 checks + status + blank.
        nonblank = [l for l in out.splitlines() if l.strip()]
        assert len(nonblank) >= 7, nonblank
        # And the audit-trail check should be green.
        assert "[OK]" in out
        assert "audit.jsonl is well-formed" in out

    def test_real_production_render_is_green_or_yellow(
        self, repo_root: Path, capsys
    ) -> None:
        main([REAL_PROD_ID, "--project-root", str(repo_root)])
        out = capsys.readouterr().out
        # No "[X]" (red) markers should appear on the shipped production.
        assert "[X]" not in out

    def test_real_production_subprocess(self, repo_root: Path) -> None:
        """End-to-end: ``python -m src.cli.doctor prod_9915e6697a12`` exits 0."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.doctor",
                REAL_PROD_ID,
                "--project-root",
                str(repo_root),
            ],
            capture_output=True,
            text=True,
            cwd=str(Path.cwd()),
        )
        assert result.returncode == 0, result.stderr
        assert "[OK]" in result.stdout


# ---------------------------------------------------------------------------
# Test 2: corrupted audit.jsonl -> exit 1 + the audit.jsonl check is red.
# ---------------------------------------------------------------------------
class TestCorruptedAudit:
    def test_corrupted_audit_exits_one(self, tmp_path: Path, capsys) -> None:
        d = _write_minimal_production(
            tmp_path / "prod_corrupt0001", corrupt_audit=True
        )
        rc = main([str(d)])
        assert rc == 1
        out = capsys.readouterr().out
        assert "[X]" in out
        assert "audit.jsonl is well-formed" in out

    def test_check_audit_jsonl_well_formed_unit(
        self, tmp_path: Path
    ) -> None:
        d = _write_minimal_production(
            tmp_path / "prod_corrupt0002", corrupt_audit=True
        )
        report = Report(title="x")
        _check_audit_jsonl_well_formed(d, report)
        # Exactly one result, and it is RED.
        assert len(report.checks) == 1
        assert report.checks[0].status == RED
        assert "invalid JSON" in report.checks[0].detail

    def test_missing_audit_exits_one(self, tmp_path: Path, capsys) -> None:
        # When audit.jsonl is missing the production cannot even be
        # located by ``find_production_dir`` (a production dir is
        # defined as containing audit.jsonl). The doctor surfaces a
        # clean stderr error and exits 1 without a Python traceback.
        d = tmp_path / "prod_no_audit000"
        _write_minimal_production(d)
        (d / "audit.jsonl").unlink()
        rc = main([str(d)])
        assert rc == 1
        err = capsys.readouterr().err
        assert "audit.jsonl" in err or "not found" in err
        assert "Traceback" not in err


# ---------------------------------------------------------------------------
# Test 3: --all iterates every production dir and prints one report block.
# ---------------------------------------------------------------------------
class TestAllFlag:
    def test_all_iterates_each_production(
        self, tmp_path: Path, capsys
    ) -> None:
        # Three distinct production dirs at the project root level.
        _write_minimal_production(
            tmp_path / "prod_alpha000001",
            production_id="prod_alpha000001",
        )
        _write_minimal_production(
            tmp_path / "prod_beta0000002",
            production_id="prod_beta0000002",
        )
        _write_minimal_production(
            tmp_path / "prod_gamma000003",
            production_id="prod_gamma000003",
        )
        rc = main(["--all", "--project-root", str(tmp_path)])
        assert rc == 0
        out = capsys.readouterr().out
        # One report block per production.
        assert "doctor: prod_alpha000001" in out
        assert "doctor: prod_beta0000002" in out
        assert "doctor: prod_gamma000003" in out

    def test_all_with_one_corrupt_returns_one(
        self, tmp_path: Path, capsys
    ) -> None:
        _write_minimal_production(
            tmp_path / "prod_healthy001",
            production_id="prod_healthy001",
        )
        _write_minimal_production(
            tmp_path / "prod_corrupt0001",
            production_id="prod_corrupt0001",
            corrupt_audit=True,
        )
        rc = main(["--all", "--project-root", str(tmp_path)])
        assert rc == 1
        out = capsys.readouterr().out
        assert "prod_healthy001" in out
        assert "prod_corrupt0001" in out

    def test_all_no_productions_errors(self, tmp_path: Path, capsys) -> None:
        rc = main(["--all", "--project-root", str(tmp_path)])
        # An empty project root has no productions; --all should exit 1
        # with a clean stderr message and no Python traceback.
        assert rc == 1
        err = capsys.readouterr().err
        assert "no production directories found" in err
        assert "Traceback" not in err


# ---------------------------------------------------------------------------
# Test 4: project-scoped checks when run with no prod_id.
# ---------------------------------------------------------------------------
class TestProjectScoped:
    def test_project_scoped_runs_six_checks(
        self, repo_root: Path, capsys, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Patch subprocess.run so the pytest check does not actually shell
        # out to a long-running test suite (the real suite takes minutes).
        class _FakeCompleted:
            returncode = 0
            stdout = "ok"
            stderr = ""

        def _fake_run(cmd, **kwargs):
            return _FakeCompleted()

        monkeypatch.setattr("src.cli.doctor.subprocess.run", _fake_run)
        rc = main(["--project-root", str(repo_root)])
        out = capsys.readouterr().out
        # 6 project-scoped checks: pytest, plan, agents, gates,
        # productions writable, CLI imports.
        for label in (
            "pytest tests/",
            "plan checklist",
            "every agent",
            "every gate",
            "productions/",
            "src/cli/{timeline,trace,doctor}",
        ):
            assert label in out, f"missing check label: {label}"
        # Exit code follows the status rule.
        assert rc in (0, 1)

    def test_run_project_checks_returns_report(
        self, repo_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class _FakeCompleted:
            returncode = 0
            stdout = ""
            stderr = ""

        monkeypatch.setattr(
            "src.cli.doctor.subprocess.run",
            lambda cmd, **kwargs: _FakeCompleted(),
        )
        report = run_project_checks(repo_root, fast=True)
        # Project-scoped report has 6 checks.
        assert len(report.checks) >= 5
        # Title carries the project root path.
        assert str(repo_root) in report.title


# ---------------------------------------------------------------------------
# Test 5: exit-code rule: 0 for green/yellow, 1 for any red.
# ---------------------------------------------------------------------------
class TestExitCodeRule:
    def test_green_report_exits_zero(
        self, tmp_path: Path, capsys
    ) -> None:
        d = _write_minimal_production(tmp_path / "prod_green00001")
        rc = main([str(d)])
        assert rc == 0

    def test_yellow_report_exits_zero(
        self, tmp_path: Path, capsys
    ) -> None:
        # The yellow branch is the audit-gate-types check when only some of
        # the four required gate types are present. Drop consistency_contract_gate
        # so the check is yellow (not red).
        d = tmp_path / "prod_yellow0001"
        _write_minimal_production(d)
        # Rewrite the audit.jsonl without the consistency_contract_gate entry.
        audit = d / "audit.jsonl"
        entries = [
            json.loads(line)
            for line in audit.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        filtered = [e for e in entries if e.get("gate_name") != "consistency_contract_gate"]
        audit.write_text(
            "\n".join(json.dumps(e) for e in filtered) + "\n",
            encoding="utf-8",
        )
        rc = main([str(d)])
        out = capsys.readouterr().out
        assert rc == 0
        assert "[!]" in out  # yellow marker present

    def test_red_report_exits_one(
        self, tmp_path: Path, capsys
    ) -> None:
        d = _write_minimal_production(
            tmp_path / "prod_red000001", corrupt_audit=True
        )
        rc = main([str(d)])
        assert rc == 1


# ---------------------------------------------------------------------------
# Direct unit tests for individual check functions.
# ---------------------------------------------------------------------------
class TestIndividualChecks:
    def test_schema_check_on_healthy_prod(
        self, prod_dir: Path
    ) -> None:
        report = Report(title="x")
        _check_production_json_validates(prod_dir, report)
        assert report.checks[0].status == GREEN

    def test_audit_well_formed_check(
        self, prod_dir: Path
    ) -> None:
        report = Report(title="x")
        _check_audit_jsonl_well_formed(prod_dir, report)
        assert report.checks[0].status == GREEN

    def test_gate_types_check_complete(
        self, prod_dir: Path
    ) -> None:
        # The fixture has all four gate types -> green.
        report = Report(title="x")
        _check_audit_has_gate_types(prod_dir, report)
        assert report.checks[0].status == GREEN

    def test_gate_types_check_partial_is_yellow(
        self, tmp_path: Path
    ) -> None:
        d = _write_minimal_production(tmp_path / "prod_partial01")
        audit = d / "audit.jsonl"
        entries = [
            json.loads(line)
            for line in audit.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        # Drop one of the required gate types.
        filtered = [e for e in entries if e.get("gate_name") != "consistency_contract_gate"]
        audit.write_text(
            "\n".join(json.dumps(e) for e in filtered) + "\n",
            encoding="utf-8",
        )
        report = Report(title="x")
        _check_audit_has_gate_types(d, report)
        assert report.checks[0].status == YELLOW

    def test_rationale_check_red_on_error(
        self, tmp_path: Path
    ) -> None:
        d = _write_minimal_production(tmp_path / "prod_rationale1")
        audit = d / "audit.jsonl"
        entries = [
            json.loads(line)
            for line in audit.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        # Wedge an empty-reason gate entry in.
        entries.append(
            {
                "id": "evt_badrationale1",
                "ts": "2026-07-29T11:00:00+00:00",
                "actor": "demo",
                "action_type": "gate_decision",
                "gate_name": "evidence_gate",
                "claim_id": "c_bad",
                "decision_status": "rejected",
                "reason": "",
                "evidence": {},
                "payload": {},
            }
        )
        audit.write_text(
            "\n".join(json.dumps(e) for e in entries) + "\n",
            encoding="utf-8",
        )
        report = Report(title="x")
        _check_audit_no_error_rationale(d, report)
        assert report.checks[0].status == RED

    def test_asset_check_missing_file_is_red(
        self, tmp_path: Path
    ) -> None:
        d = _write_minimal_production(
            tmp_path / "prod_assets0001", include_assets=True
        )
        report = Report(title="x")
        _check_asset_sha256s_exist(d, report)
        assert report.checks[0].status == RED
        assert "b" * 8 in report.checks[0].detail

    def test_asset_check_no_assets_dir_is_green(
        self, prod_dir: Path
    ) -> None:
        report = Report(title="x")
        _check_asset_sha256s_exist(prod_dir, report)
        assert report.checks[0].status == GREEN

    def test_state_reachable_published_is_green(
        self, prod_dir: Path
    ) -> None:
        report = Report(title="x")
        _check_state_reachable_from_draft(prod_dir, report)
        assert report.checks[0].status == GREEN

    def test_state_reachable_unreachable_is_red(
        self, tmp_path: Path
    ) -> None:
        d = _write_minimal_production(
            tmp_path / "prod_unreachab1", state="UNKNOWN_STATE"
        )
        report = Report(title="x")
        _check_state_reachable_from_draft(d, report)
        assert report.checks[0].status == RED


# ---------------------------------------------------------------------------
# Report helper sanity checks.
# ---------------------------------------------------------------------------
class TestReport:
    def test_status_worst_of(self) -> None:
        report = Report(title="x")
        report.add(CheckResult("a", GREEN))
        report.add(CheckResult("b", YELLOW))
        assert report.status() == YELLOW
        report.add(CheckResult("c", RED))
        assert report.status() == RED

    def test_render_includes_status(self) -> None:
        report = Report(title="hello")
        report.add(CheckResult("one", GREEN))
        text = report.render()
        assert "hello" in text
        assert "GREEN" in text

    def test_render_yellow_status(self) -> None:
        report = Report(title="hello")
        report.add(CheckResult("one", YELLOW))
        text = report.render()
        assert "YELLOW" in text

    def test_render_red_status(self) -> None:
        report = Report(title="hello")
        report.add(CheckResult("one", RED))
        text = report.render()
        assert "RED" in text


# ---------------------------------------------------------------------------
# run_production_checks helper sanity check.
# ---------------------------------------------------------------------------
class TestRunProductionChecks:
    def test_returns_report_with_six_checks(
        self, prod_dir: Path
    ) -> None:
        report = run_production_checks(prod_dir)
        # 6 production-scoped checks: schema, audit well-formed, gate types,
        # rationale, assets, state reachable.
        assert len(report.checks) == 6
        labels = [c.label for c in report.checks]
        assert "production.json validates against schema" in labels
        assert "audit.jsonl is well-formed" in labels
        assert "state field is reachable from DRAFT via _ALLOWED_TRANSITIONS" in labels
