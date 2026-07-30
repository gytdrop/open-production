"""End-to-end tests for the unified ``python -m src.cli`` dispatcher."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
REAL_PROD_ID = "prod_9915e6697a12"
REAL_SHA = "4470eb15f4b5c9dc18f15817af21260530b364567faaa0b9fac98a45b1aa23d6"


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


def test_no_args_lists_all_subcommands() -> None:
    result = _run_cli()

    assert result.returncode == 0, result.stderr
    assert "Usage: python -m src.cli <subcmd>" in result.stdout
    assert "timeline   audit replay" in result.stdout
    assert "trace      asset lineage" in result.stdout
    assert "doctor     health report" in result.stdout
    assert "compare    side-by-side diff" in result.stdout
    assert "run        drive the full 22-stage pipeline" in result.stdout
    assert "list       enumerate every production" in result.stdout
    assert result.stderr == ""


def test_top_level_help_lists_all_subcommands_and_shortcut() -> None:
    result = _run_cli("--help")

    assert result.returncode == 0, result.stderr
    for subcommand in ("timeline", "trace", "doctor", "compare", "run", "list"):
        assert subcommand in result.stdout
    assert "production <subcmd>" in result.stdout


def test_timeline_help_delegates_to_timeline_parser() -> None:
    result = _run_cli("timeline", "--help")

    assert result.returncode == 0, result.stderr
    assert "usage: production timeline" in result.stdout
    assert "--summary" in result.stdout


def test_trace_real_sha_delegates_and_exits_zero() -> None:
    result = _run_cli("trace", REAL_SHA)

    assert result.returncode == 0, result.stderr
    assert REAL_PROD_ID in result.stdout
    assert REAL_SHA[:8] in result.stdout


def test_doctor_real_production_delegates_and_exits_zero() -> None:
    result = _run_cli("doctor", REAL_PROD_ID)

    assert result.returncode == 0, result.stderr
    assert f"doctor: {REAL_PROD_ID}" in result.stdout
    assert "status:" in result.stdout


def test_compare_missing_productions_errors_cleanly_and_exits_zero() -> None:
    """The dispatcher must not reject "compare" itself; compare handles a/b."""
    result = _run_cli("compare", "a", "b")

    assert result.returncode == 0
    assert result.stdout == ""
    assert "not found" in result.stderr.lower()


def test_unknown_subcommand_exits_two_with_clean_error() -> None:
    result = _run_cli("bogus")

    assert result.returncode == 2
    assert result.stdout == ""
    assert "unknown subcommand" in result.stderr.lower()

def test_run_help_exits_zero_and_mentions_topic_and_no_confirm() -> None:
    """``python -m src.cli run --help`` must surface the same flag set as
    src/cli/run.py so users discover ``topic`` (positional), ``--no-confirm``
    and the rest from the dispatcher."""
    result = _run_cli("run", "--help")

    assert result.returncode == 0, result.stderr
    # The dispatcher's run subparser mirrors run.py exactly: ``topic`` is the
    # only positional, every optional below matches run.py verbatim.
    assert "topic" in result.stdout
    assert "--no-confirm" in result.stdout
    assert "--audience" in result.stdout
    assert "--tone" in result.stdout
    assert "--platform" in result.stdout
    assert "--out" in result.stdout
    assert "--pick" in result.stdout


def test_run_delegates_and_creates_production_json(tmp_path) -> None:
    """``python -m src.cli run SMOKE --no-confirm --out DIR`` must
    delegate to src/cli/run.py and produce a ``prod_*/production.json``
    directory pair under DIR."""
    out_dir = tmp_path / "productions"
    result = _run_cli("run", "smoke", "--no-confirm", "--out", str(out_dir))

    assert result.returncode == 0, result.stderr
    prod_dirs = sorted(p for p in out_dir.iterdir() if p.is_dir())
    assert len(prod_dirs) == 1, f"expected one production, got {prod_dirs}"
    prod_dir = prod_dirs[0]
    assert prod_dir.name.startswith("prod_"), prod_dir.name
    assert (prod_dir / "production.json").is_file()
    assert (prod_dir / "audit.jsonl").is_file()


def test_production_console_script_run_help_exits_zero() -> None:
    """The ``production`` console-script entry declared in pyproject.toml
    must continue to work for the ``run`` subcommand after wiring. The
    shim created by ``pip install -e .`` is a one-liner that calls the
    same ``src.cli.__main__:main`` we test directly via ``-m src.cli``;
    resolving it through ``importlib.metadata`` exercises the entry-point
    chain even when the ``production`` binary is not on PATH."""
    from importlib.metadata import entry_points

    production_ep = next(
        (
            ep
            for ep in entry_points(group="console_scripts")
            if ep.name == "production"
        ),
        None,
    )
    assert production_ep is not None, (
        "production entry point must be declared in pyproject.toml"
    )

    # Invoke the entry-point target with the same argv the console shim
    # would receive. Returns the dispatcher's exit code; --help returns 0.
    from src.cli.__main__ import main as dispatcher_main

    returncode = dispatcher_main(argv=["run", "--help"])
    assert returncode == 0

