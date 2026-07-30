"""Tests for ``src.cli.list`` -- the production-discovery CLI.

Covers:
  1. Module-level helpers (discover_production_dirs, _summarise, render_table,
     render_json) work on a self-contained tmp production pair.
  2. The CLI text output prints the table header, includes every production
     id, and sorts newest-first by created_at.
  3. ``--json`` emits a parseable array with the documented keys.
  4. ``--filter <state>`` narrows to that state only.
  5. ``--out`` overrides the search root.
  6. Empty search root returns the ``no productions found`` line and exits 0.
  7. Bad ``--filter`` value exits non-zero with a clean argparse error.
  8. End-to-end: the dispatcher (``python -m src.cli list``) routes the
     subcommand and produces the same output as ``python -m src.cli.list``.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.cli.list import (
    discover_production_dirs,
    main,
    render_json,
    render_table,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
REAL_PROD_ID = "prod_9915e6697a12"


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "src.cli", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )


def _run_cli_module(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "src.cli.list", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )


# ---------------------------------------------------------------------------
# Fixture helper: write a self-contained production pair under tmp_path.
# ---------------------------------------------------------------------------
def _write_production(
    prod_root: Path,
    *,
    production_id: str,
    state: str = "PUBLISHED",
    topic: str = "A test production",
    created_at: str = "2026-07-29T12:00:00+00:00",
    audit_entries: list[dict] | None = None,
) -> Path:
    """Create ``prod_root/<production_id>/`` with production.json + audit.jsonl."""
    prod_dir = prod_root / production_id
    prod_dir.mkdir(parents=True, exist_ok=True)

    production_doc = {
        "id": production_id,
        "state": state,
        "created_at": created_at,
        "updated_at": created_at,
        "intent": {"topic": topic, "audience": "educated_lay", "tone": "neutral", "platform": "youtube"},
        "metadata": {},
        "audit_trail": [],
    }
    (prod_dir / "production.json").write_text(
        json.dumps(production_doc, ensure_ascii=False),
        encoding="utf-8",
    )

    entries = audit_entries if audit_entries is not None else [{"ts": created_at, "actor": "system", "action_type": "system"}]
    with (prod_dir / "audit.jsonl").open("w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return prod_dir


# ---------------------------------------------------------------------------
# 1. Module-level helpers
# ---------------------------------------------------------------------------
class TestDiscoverAndSummarise:
    def test_discover_finds_direct_child(self, tmp_path: Path) -> None:
        _write_production(tmp_path, production_id="prod_aaaa11110000")
        _write_production(tmp_path, production_id="prod_bbbb22220000")

        found = discover_production_dirs(tmp_path)

        names = {p.name for p in found}
        assert names == {"prod_aaaa11110000", "prod_bbbb22220000"}

    def test_discover_finds_output_subdirs(self, tmp_path: Path) -> None:
        out = tmp_path / "output" / "productions"
        _write_production(out, production_id="prod_cccc33330000")

        found = discover_production_dirs(tmp_path)

        assert any(p.name == "prod_cccc33330000" for p in found)

    def test_discover_dedupes_when_search_root_matches_subdir(self, tmp_path: Path) -> None:
        # If both ``tmp_path/prod_x`` and ``tmp_path/output/productions/prod_x``
        # exist, dedupe to one entry.
        _write_production(tmp_path, production_id="prod_dddd44440000")
        _write_production(tmp_path / "output" / "productions", production_id="prod_dddd44440000")

        found = discover_production_dirs(tmp_path)

        matching = [p for p in found if p.name == "prod_dddd44440000"]
        assert len(matching) == 1

    def test_discover_skips_non_prod_subdirs(self, tmp_path: Path) -> None:
        _write_production(tmp_path, production_id="prod_eeee55550000")
        # A sibling that does NOT start with ``prod_`` must be ignored.
        not_a_prod = tmp_path / "not_a_production"
        not_a_prod.mkdir()
        (not_a_prod / "audit.jsonl").write_text("{}\n", encoding="utf-8")

        found = discover_production_dirs(tmp_path)

        names = {p.name for p in found}
        assert "prod_eeee55550000" in names
        assert "not_a_production" not in names

    def test_discover_skips_dirs_without_audit_jsonl(self, tmp_path: Path) -> None:
        # A prod_-prefixed dir without an audit.jsonl must NOT be listed.
        empty = tmp_path / "prod_noaudit12345"
        empty.mkdir()
        (empty / "production.json").write_text("{}", encoding="utf-8")

        found = discover_production_dirs(tmp_path)

        assert all(p.name != "prod_noaudit12345" for p in found)

    def test_summarise_extracts_topic_state_and_entry_count(self, tmp_path: Path) -> None:
        prod_dir = _write_production(
            tmp_path,
            production_id="prod_ffff66660000",
            state="DRAFT",
            topic="Smoke test topic",
            audit_entries=[{"ts": "2026-07-29T10:00:00+00:00"}, {"ts": "2026-07-29T11:00:00+00:00"}, {"ts": "2026-07-29T12:00:00+00:00"}],
        )

        from src.cli.list import _summarise

        summary = _summarise(prod_dir)

        assert summary is not None
        assert summary["production_id"] == "prod_ffff66660000"
        assert summary["state"] == "DRAFT"
        assert summary["topic"] == "Smoke test topic"
        assert summary["created_at"] == "2026-07-29T12:00"
        assert summary["entries"] == 3


# ---------------------------------------------------------------------------
# 2. Renderer shape
# ---------------------------------------------------------------------------
class TestRenderers:
    def test_render_table_includes_all_production_ids(self) -> None:
        summaries = [
            {"production_id": "prod_aaa", "state": "PUBLISHED", "topic": "topic a", "created_at": "2026-07-29T12:00", "entries": 5, "_prod_dir": "/x"},
            {"production_id": "prod_bbb", "state": "DRAFT", "topic": "topic b", "created_at": "2026-07-29T13:00", "entries": 7, "_prod_dir": "/y"},
        ]

        out = render_table(summaries)

        assert "PRODUCTION ID" in out
        assert "STATE" in out
        assert "INTENT TOPIC" in out
        assert "CREATED" in out
        assert "ENTRIES" in out
        assert "prod_aaa" in out
        assert "prod_bbb" in out
        assert "topic a" in out
        assert "topic b" in out

    def test_render_table_sorts_newest_first(self) -> None:
        summaries = [
            {"production_id": "prod_aaa", "state": "PUBLISHED", "topic": "old", "created_at": "2026-07-29T10:00", "entries": 1, "_prod_dir": "/x"},
            {"production_id": "prod_bbb", "state": "PUBLISHED", "topic": "new", "created_at": "2026-07-29T15:00", "entries": 1, "_prod_dir": "/y"},
        ]

        out = render_table(summaries)

        # Newer topic appears above older topic.
        assert out.index("new") < out.index("old")

    def test_render_table_empty_returns_clean_message(self) -> None:
        out = render_table([])
        assert "no productions found" in out

    def test_render_json_emits_parseable_array(self) -> None:
        summaries = [
            {"production_id": "prod_aaa", "state": "PUBLISHED", "topic": "topic a", "created_at": "2026-07-29T12:00", "entries": 5, "_prod_dir": "/x"},
        ]

        out = render_json(summaries)
        parsed = json.loads(out)

        assert isinstance(parsed, list)
        assert len(parsed) == 1
        row = parsed[0]
        assert set(row.keys()) == {"production_id", "state", "topic", "created_at", "entries"}
        assert "_prod_dir" not in row


# ---------------------------------------------------------------------------
# 3. CLI behaviour
# ---------------------------------------------------------------------------
class TestListCLI:
    def test_module_invocation_lists_known_production(self) -> None:
        """``python -m src.cli.list`` against the real project root includes the
        shipped ``prod_9915e6697a12/`` (its ``audit.jsonl`` + ``production.json``
        are the canonical fixture for the audit trail)."""
        result = _run_cli_module()

        assert result.returncode == 0, result.stderr
        assert REAL_PROD_ID in result.stdout
        # The header line is always present.
        assert "PRODUCTION ID" in result.stdout
        assert "INTENT TOPIC" in result.stdout

    def test_module_invocation_json_is_parseable(self) -> None:
        result = _run_cli_module("--json")

        assert result.returncode == 0, result.stderr
        parsed = json.loads(result.stdout)
        assert isinstance(parsed, list)
        assert any(row["production_id"] == REAL_PROD_ID for row in parsed)
        row = next(r for r in parsed if r["production_id"] == REAL_PROD_ID)
        assert row["state"] == "PUBLISHED"
        assert row["topic"] == "Test failure"

    def test_module_invocation_filter_published(self) -> None:
        result = _run_cli_module("--filter", "PUBLISHED", "--no-color")

        assert result.returncode == 0, result.stderr
        # Header line is present; rows for PUBLISHED productions appear.
        assert "PRODUCTION ID" in result.stdout
        assert "PUBLISHED" in result.stdout
        # No DRAFT rows leak into a --filter PUBLISHED run.
        # Walk lines and assert state column is PUBLISHED for every row.
        for line in result.stdout.splitlines():
            if not line or line.startswith("PRODUCTION") or line.startswith("---"):
                continue
            parts = line.split()
            assert parts[1] == "PUBLISHED", f"non-PUBLISHED row leaked through --filter: {line!r}"

    def test_module_invocation_out_override_finds_nested(self, tmp_path: Path) -> None:
        nested_root = tmp_path / "nested"
        nested_out = nested_root / "output" / "productions"
        _write_production(nested_out, production_id="prod_zzzz99990000", state="DRAFT", topic="nested")

        result = _run_cli_module("--out", str(nested_root))

        assert result.returncode == 0, result.stderr
        assert "prod_zzzz99990000" in result.stdout

    def test_module_invocation_empty_dir_reports_no_productions(self, tmp_path: Path) -> None:
        result = _run_cli_module("--out", str(tmp_path))

        assert result.returncode == 0, result.stderr
        assert "no productions found" in result.stdout

    def test_module_invocation_bad_filter_value_errors(self) -> None:
        result = _run_cli_module("--filter", "BOGUS")

        assert result.returncode != 0
        assert "invalid choice" in result.stderr.lower()

    def test_module_invocation_no_color_strips_ansi(self) -> None:
        result = _run_cli_module("--no-color")

        assert result.returncode == 0, result.stderr
        # When --no-color is set, the output must not contain ESC sequences.
        assert "\x1b[" not in result.stdout


# ---------------------------------------------------------------------------
# 4. Dispatcher routing
# ---------------------------------------------------------------------------
class TestDispatcherRouting:
    def test_dispatcher_routes_list_subcommand(self) -> None:
        """``python -m src.cli list`` must produce the same shape of output
        as ``python -m src.cli.list`` -- the dispatcher cannot reject ``list``."""
        result = _run_cli("list", "--no-color")

        assert result.returncode == 0, result.stderr
        assert "PRODUCTION ID" in result.stdout
        assert REAL_PROD_ID in result.stdout

    def test_dispatcher_list_json_is_parseable(self) -> None:
        result = _run_cli("list", "--json")

        assert result.returncode == 0, result.stderr
        parsed = json.loads(result.stdout)
        assert isinstance(parsed, list)
        assert any(row["production_id"] == REAL_PROD_ID for row in parsed)

    def test_dispatcher_list_filter_routes_through(self) -> None:
        result = _run_cli("list", "--filter", "DRAFT", "--no-color")

        assert result.returncode == 0, result.stderr
        # Every row must be in DRAFT.
        for line in result.stdout.splitlines():
            if not line or line.startswith("PRODUCTION") or line.startswith("---"):
                continue
            parts = line.split()
            assert parts[1] == "DRAFT", f"non-DRAFT row leaked through --filter: {line!r}"

    def test_dispatcher_list_help_exits_zero(self) -> None:
        result = _run_cli("list", "--help")

        assert result.returncode == 0, result.stderr
        assert "usage: production list" in result.stdout
        assert "--filter" in result.stdout
        assert "--json" in result.stdout
