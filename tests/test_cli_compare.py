"""Tests for ``src.cli.compare`` -- the production side-by-side diff.

Covers:
- compare on two known productions from output/public-demo/ exits 0 and
  prints a row per axis (>= 6 rows)
- compare --mermaid output starts with "graph TD" or "flowchart TD"
- compare --only scenes shows only the scenes row and the divergence count
- compare on two productions with NO common ancestor prints a clean
  "no common ancestor" line and still exits 0
- compare prod_a prod_a prints all axes with delta=0 and divergence events=0
- compare --json output is valid JSON with keys matching the table columns
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.cli.compare import (
    CompareUsageError,
    build_compare,
    main,
    render_compare,
    render_json,
    render_mermaid,
)


REAL_PROD_ID = "prod_9915e6697a12"


# ---------------------------------------------------------------------------
# Test fixtures.
# ---------------------------------------------------------------------------
def _write_production(
    prod_dir: Path,
    *,
    production_id: str,
    state: str = "PUBLISHED",
    audit_entries: list[dict] | None = None,
    scenes: list[dict] | None = None,
    characters: list[dict] | None = None,
    sidecar_sha: str | None = None,
    no_common_ancestor: bool = False,
) -> Path:
    """Write a self-contained production.json + audit.jsonl pair.

    By default the production is healthy. Test cases toggle individual knobs.
    """
    prod_dir.mkdir(parents=True, exist_ok=True)
    if audit_entries is None:
        audit_entries = [
            {
                "id": "evt_init_00001",
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
                "id": "evt_evidence_001",
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
        ]
    if no_common_ancestor:
        # Make every entry unique per production: bump id and state_after so no
        # sibling production can share any matching audit entry.
        for i, entry in enumerate(audit_entries):
            entry["id"] = "evt_init_" + production_id[-12:] + "_" + str(i).zfill(4)
            entry["state_after"] = "unique_" + production_id[-12:] + "_" + str(i).zfill(4)
    state_doc: dict = {
        "schema_version": "1.0.0",
        "id": production_id,
        "state": state,
        "title": "Test production",
        "created_at": "2026-07-29T10:00:00+00:00",
        "updated_at": "2026-07-29T10:00:01+00:00",
        "intent": {"topic": "Test"},
        "scenes": scenes or [],
        "characters": characters or [],
        "audit_trail": audit_entries,
        "references": [],
        "snapshots": [],
    }
    (prod_dir / "production.json").write_text(
        json.dumps(state_doc), encoding="utf-8"
    )
    (prod_dir / "audit.jsonl").write_text(
        "\n".join(json.dumps(e) for e in audit_entries) + "\n",
        encoding="utf-8",
    )
    if sidecar_sha is not None:
        (prod_dir / "production.json.sha256").write_text(
            sidecar_sha + "\n", encoding="utf-8"
        )
    return prod_dir


@pytest.fixture()
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture()
def public_demo_dir(repo_root: Path) -> Path:
    """Return the absolute path to output/public-demo."""
    return repo_root / "output" / "public-demo"


def _two_distinct_public_demo_productions(public_demo_dir: Path) -> tuple[str, str]:
    """Return two distinct production ids from output/public-demo/."""
    candidates = sorted(
        p.name for p in public_demo_dir.iterdir()
        if p.is_dir() and (p / "audit.jsonl").is_file()
    )
    if len(candidates) < 2:
        pytest.skip(
            f"need at least 2 production dirs under {public_demo_dir}; "
            f"found {len(candidates)}"
        )
    return candidates[0], candidates[1]


# ---------------------------------------------------------------------------
# Test 1: compare on two known productions from output/public-demo/ exits 0
# and prints a row per axis (>= 6 rows).
# ---------------------------------------------------------------------------
class TestRealProduction:
    def test_compare_two_real_productions_exits_zero(
        self, repo_root: Path, public_demo_dir: Path, capsys
    ) -> None:
        prod_a, prod_b = _two_distinct_public_demo_productions(public_demo_dir)
        rc = main([prod_a, prod_b, "--project-root", str(repo_root)])
        assert rc == 0
        out = capsys.readouterr().out
        # >= 6 rows: header line + 6 axis rows minimum + divergence lines
        axis_rows = [
            line for line in out.splitlines()
            if line and line.split()[0] in {
                "state", "scenes", "shots", "characters",
                "reviewer", "content", "audit",
            }
        ]
        assert len(axis_rows) >= 6, axis_rows
        # Axis labels in expected order
        assert any("state" in row for row in axis_rows)
        assert any("scenes" in row for row in axis_rows)
        assert any("shots" in row for row in axis_rows)
        assert any("characters" in row for row in axis_rows)
        assert any("content root hash" in row for row in axis_rows)
        assert any("audit events" in row for row in axis_rows)

    def test_compare_two_real_productions_subprocess(
        self, repo_root: Path, public_demo_dir: Path
    ) -> None:
        prod_a, prod_b = _two_distinct_public_demo_productions(public_demo_dir)
        result = subprocess.run(
            [
                sys.executable, "-m", "src.cli.compare",
                prod_a, prod_b,
                "--project-root", str(repo_root),
            ],
            capture_output=True,
            text=True,
            cwd=str(Path.cwd()),
        )
        assert result.returncode == 0, result.stderr
        assert "compare:" in result.stdout


# ---------------------------------------------------------------------------
# Test 2: compare --mermaid output starts with "graph TD" or "flowchart TD".
# ---------------------------------------------------------------------------
class TestMermaid:
    def test_mermaid_starts_with_flowchart_td(
        self, repo_root: Path, public_demo_dir: Path, capsys
    ) -> None:
        prod_a, prod_b = _two_distinct_public_demo_productions(public_demo_dir)
        rc = main([prod_a, prod_b, "--mermaid", "--project-root", str(repo_root)])
        assert rc == 0
        out = capsys.readouterr().out.strip()
        first_line = out.splitlines()[0].strip()
        assert first_line in {"flowchart TD", "graph TD"}, first_line

    def test_mermaid_is_parseable_header(
        self, repo_root: Path, public_demo_dir: Path
    ) -> None:
        prod_a, prod_b = _two_distinct_public_demo_productions(public_demo_dir)
        result = subprocess.run(
            [
                sys.executable, "-m", "src.cli.compare",
                prod_a, prod_b, "--mermaid",
                "--project-root", str(repo_root),
            ],
            capture_output=True,
            text=True,
            cwd=str(Path.cwd()),
        )
        assert result.returncode == 0, result.stderr
        first = result.stdout.splitlines()[0].strip()
        assert first.startswith("flowchart") or first.startswith("graph")
        # Mermaid syntax requires "TD" or "LR" etc. directly after the type.
        assert " TD" in first or first.endswith("TD") or " LR" in first

    def test_mermaid_with_no_common_ancestor(
        self, tmp_path: Path, capsys
    ) -> None:
        _write_production(
            tmp_path / "prod_a_xx000001",
            production_id="prod_a_xx000001",
            no_common_ancestor=True,
        )
        _write_production(
            tmp_path / "prod_b_xx000002",
            production_id="prod_b_xx000002",
            no_common_ancestor=True,
        )
        rc = main([
            "prod_a_xx000001", "prod_b_xx000002",
            "--mermaid", "--project-root", str(tmp_path),
        ])
        assert rc == 0
        out = capsys.readouterr().out
        first = out.splitlines()[0].strip()
        assert first.startswith("flowchart") or first.startswith("graph")
        # No common ancestor produces an edge labelled with that message.
        assert "no common ancestor" in out


# ---------------------------------------------------------------------------
# Test 3: compare --only scenes shows only the scenes row and the divergence
# count, not the full table.
# ---------------------------------------------------------------------------
class TestOnly:
    def test_only_scenes_shows_only_that_row(
        self, repo_root: Path, public_demo_dir: Path, capsys
    ) -> None:
        prod_a, prod_b = _two_distinct_public_demo_productions(public_demo_dir)
        rc = main([
            prod_a, prod_b, "--only", "scenes",
            "--project-root", str(repo_root),
        ])
        assert rc == 0
        out = capsys.readouterr().out
        # Only the scenes row should be present in the table body.
        axis_rows = [
            line for line in out.splitlines()
            if line and line.split()[0] in {
                "state", "scenes", "shots", "characters",
                "reviewer", "content", "audit",
            }
        ]
        assert len(axis_rows) == 1
        assert "scenes" in axis_rows[0]
        # The divergence count line must still appear.
        assert "divergence events" in out
        # But the per-event list must NOT appear (the spec says "not the
        # full table" -- the scrollable divergence list is excluded too).
        assert "at event " not in out

    def test_only_invalid_value_errors(
        self, repo_root: Path, public_demo_dir: Path, capsys
    ) -> None:
        prod_a, prod_b = _two_distinct_public_demo_productions(public_demo_dir)
        rc = main([
            prod_a, prod_b, "--only", "bogus",
            "--project-root", str(repo_root),
        ])
        assert rc == 1
        err = capsys.readouterr().err
        assert "unknown --only value" in err

    def test_only_each_alias(
        self, repo_root: Path, public_demo_dir: Path, capsys
    ) -> None:
        prod_a, prod_b = _two_distinct_public_demo_productions(public_demo_dir)
        for alias in ("scenes", "shots", "characters", "reviewer", "hashes", "events"):
            rc = main([
                prod_a, prod_b, "--only", alias,
                "--project-root", str(repo_root),
            ])
            assert rc == 0
            out = capsys.readouterr().out
            axis_rows = [
                line for line in out.splitlines()
                if line and line.split()[0] in {
                    "state", "scenes", "shots", "characters",
                    "reviewer", "content", "audit",
                }
            ]
            assert len(axis_rows) == 1, (alias, axis_rows)


# ---------------------------------------------------------------------------
# Test 4: compare on two productions with NO common ancestor prints a clean
# "no common ancestor" line and still exits 0.
# ---------------------------------------------------------------------------
class TestNoCommonAncestor:
    def test_no_common_ancestor_message_and_exit_zero(
        self, tmp_path: Path, capsys
    ) -> None:
        _write_production(
            tmp_path / "prod_a_yy000001",
            production_id="prod_a_yy000001",
            no_common_ancestor=True,
        )
        _write_production(
            tmp_path / "prod_b_yy000002",
            production_id="prod_b_yy000002",
            no_common_ancestor=True,
        )
        rc = main([
            "prod_a_yy000001", "prod_b_yy000002",
            "--project-root", str(tmp_path),
        ])
        assert rc == 0
        out = capsys.readouterr().out
        assert "no common ancestor" in out
        # The top-level diff is still shown.
        assert "compare:" in out
        assert "scenes" in out
        assert "shots" in out


# ---------------------------------------------------------------------------
# Test 5: compare prod_a prod_a (same production) prints all axes with
# delta=0 and divergence events=0.
# ---------------------------------------------------------------------------
class TestSelfCompare:
    def test_self_compare_all_deltas_zero(self, repo_root: Path, capsys) -> None:
        rc = main([REAL_PROD_ID, REAL_PROD_ID, "--project-root", str(repo_root)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "(same production)" in out
        # Each numeric axis row should have delta 0
        for axis in ("scenes", "shots", "characters", "audit"):
            row = next(
                line for line in out.splitlines()
                if line.startswith(axis)
            )
            assert row.rstrip().endswith("0"), row
        assert "divergence events (since common ancestor): 0" in out

    def test_self_compare_subprocess(self, repo_root: Path) -> None:
        result = subprocess.run(
            [
                sys.executable, "-m", "src.cli.compare",
                REAL_PROD_ID, REAL_PROD_ID,
                "--project-root", str(repo_root),
            ],
            capture_output=True,
            text=True,
            cwd=str(Path.cwd()),
        )
        assert result.returncode == 0, result.stderr
        assert "divergence events (since common ancestor): 0" in result.stdout


# ---------------------------------------------------------------------------
# Test 6: compare --json output is valid JSON with keys matching the table
# columns above.
# ---------------------------------------------------------------------------
class TestJson:
    def test_json_is_valid(
        self, repo_root: Path, public_demo_dir: Path, capsys
    ) -> None:
        prod_a, prod_b = _two_distinct_public_demo_productions(public_demo_dir)
        rc = main([prod_a, prod_b, "--json", "--project-root", str(repo_root)])
        assert rc == 0
        out = capsys.readouterr().out
        # Must parse as JSON.
        data = json.loads(out)
        assert "axes" in data
        assert "prod_a" in data
        assert "prod_b" in data
        assert "common_ancestor_idx" in data
        assert "divergence_count" in data
        assert "divergence_events" in data
        # Each axis row carries the four column keys.
        for row in data["axes"]:
            assert {"axis", "value_a", "value_b", "delta", "match"} <= set(row.keys())
            assert row["axis"] in {
                "state", "scenes", "shots", "characters",
                "reviewer score", "content root hash", "audit events",
            }

    def test_self_compare_json_has_all_deltas_zero(
        self, repo_root: Path, capsys
    ) -> None:
        rc = main([
            REAL_PROD_ID, REAL_PROD_ID, "--json",
            "--project-root", str(repo_root),
        ])
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["same_production"] is True
        assert data["divergence_count"] == 0
        for row in data["axes"]:
            if row["axis"] in {"scenes", "shots", "characters", "audit events"}:
                assert row["delta"] == 0, row
            assert row["match"] is True, row


# ---------------------------------------------------------------------------
# render_compare / render_mermaid / render_json unit tests.
# ---------------------------------------------------------------------------
class TestRenderers:
    def test_render_compare_with_only(
        self, tmp_path: Path
    ) -> None:
        d_a = _write_production(tmp_path / "prod_x_zz00001", production_id="prod_x_zz00001")
        d_b = _write_production(tmp_path / "prod_y_zz00002", production_id="prod_y_zz00002")
        result = build_compare(d_a, d_b)
        text = render_compare(result, only="scenes", use_color=False)
        assert "compare:" in text
        assert "scenes" in text
        # The "shots" axis must NOT appear when --only scenes.
        assert "\nshots " not in ("\n" + text)

    def test_render_mermaid_emits_three_node_or_pair(
        self, tmp_path: Path
    ) -> None:
        d_a = _write_production(tmp_path / "prod_x_zz00003", production_id="prod_x_zz00003")
        d_b = _write_production(tmp_path / "prod_y_zz00004", production_id="prod_y_zz00004")
        result = build_compare(d_a, d_b)
        text = render_mermaid(result)
        assert text.splitlines()[0] in {"flowchart TD", "graph TD"}
        assert "prod_x_zz00003" in text
        assert "prod_y_zz00004" in text

    def test_render_json_smoke(
        self, tmp_path: Path
    ) -> None:
        d_a = _write_production(tmp_path / "prod_x_zz00005", production_id="prod_x_zz00005")
        d_b = _write_production(tmp_path / "prod_y_zz00006", production_id="prod_y_zz00006")
        result = build_compare(d_a, d_b)
        text = render_json(result)
        data = json.loads(text)
        assert data["prod_a"]["id"] == "prod_x_zz00005"
        assert data["prod_b"]["id"] == "prod_y_zz00006"
        assert isinstance(data["axes"], list)
        assert len(data["axes"]) == 7

    def test_missing_production_errors(
        self, tmp_path: Path, capsys
    ) -> None:
        rc = main([
            "prod_does_not_exist", REAL_PROD_ID,
            "--project-root", str(tmp_path),
        ])
        assert rc == 1
        err = capsys.readouterr().err
        assert "not found" in err
        assert "Traceback" not in err