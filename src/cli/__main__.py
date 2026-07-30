"""Unified ``python -m src.cli`` production dispatcher.

Usage:
    python -m src.cli                       # list subcommands
    python -m src.cli timeline <prod_id>    # audit replay
    python -m src.cli trace <sha256>        # asset lineage
    python -m src.cli doctor [prod|--all]   # health report
    python -m src.cli compare <a> <b>       # side-by-side diff
    python -m src.cli run <topic>           # drive the full pipeline

After ``pip install -e .``, the equivalent short form is available as
``production <subcommand>``. Installation is optional; the module form above
is the canonical entry point.
"""
from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

# Make ``src`` importable when this file is invoked as a console script
# after ``pip install -e .``. The project uses a ``src/`` layout, so the
# package is only importable when ``src`` is on ``sys.path``; running it
# as ``python -m src.cli`` already has it, but the ``production`` script
# launcher must discover it on its own.
_THIS_DIR = Path(__file__).resolve().parent
_SRC_PARENT = _THIS_DIR.parent
if str(_SRC_PARENT) not in sys.path:
    sys.path.insert(0, str(_SRC_PARENT))

from src.cli import (
    compare,
    doctor,
    list as list_cmd,
    run,
    timeline,
    trace,
)


CommandMain = Callable[[list[str] | None], int]

_SUBCOMMAND_HELP: tuple[tuple[str, str], ...] = (
    ("timeline", "audit replay for a production"),
    ("trace", "asset lineage for a production or sha256"),
    ("doctor", "health report for a production or project"),
    ("compare", "side-by-side diff of two productions"),
    ("run", "drive the full 22-stage pipeline from an intent"),
    ("list", "enumerate every production on disk"),
)
_COMMAND_MAINS: dict[str, CommandMain] = {
    "timeline": timeline.main,
    "trace": trace.main,
    "doctor": doctor.main,
    "compare": compare.main,
    "run": run.main,
    "list": list_cmd.main,
}


def usage() -> str:
    """Return the usage block shown by bare invocation and ``--help``."""
    lines = ["Usage: python -m src.cli <subcmd>"]
    lines.extend(
        f"  {name:<11}{description}" for name, description in _SUBCOMMAND_HELP
    )
    lines.extend(
        (
            "",
            "Run 'python -m src.cli <subcmd> --help' for command-specific help.",
            "After 'pip install -e .', use 'production <subcmd>' as a shortcut.",
        )
    )
    return "\n".join(lines)


def _add_project_root(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Override the project root used to locate production directories.",
    )


def _build_parser() -> argparse.ArgumentParser:
    """Build the top-level parser with each command's accepted arguments."""
    parser = argparse.ArgumentParser(
        prog="python -m src.cli",
        usage=argparse.SUPPRESS,
        add_help=False,
    )
    subparsers = parser.add_subparsers(dest="subcommand", metavar="<subcmd>")

    timeline_parser = subparsers.add_parser(
        "timeline",
        prog="production timeline",
        description=(
            "Replay a production's audit trail as a readable timeline. "
            "Surfaces every gate decision, state transition, system event, "
            "and snapshot in the order they happened."
        ),
        help="audit replay for a production",
    )
    timeline_parser.add_argument(
        "production_id",
        help=(
            "Production id (e.g. prod_9915e6697a12) or an explicit path to "
            "the production directory."
        ),
    )
    timeline_parser.add_argument(
        "--json",
        action="store_true",
        help=(
            "Emit the timeline as a single JSON document instead of the text "
            "table."
        ),
    )
    timeline_parser.add_argument(
        "--summary",
        action="store_true",
        help=(
            "Print only the header + gate counts + state progression (skip "
            "the per-event table)."
        ),
    )
    _add_project_root(timeline_parser)

    trace_parser = subparsers.add_parser(
        "trace",
        prog="production trace",
        description=(
            "Trace an asset or production lineage. Walks audit.jsonl + "
            "production.json to render a derivation graph of assets, "
            "generations, snapshots, branches, and merges."
        ),
        help="asset lineage for a production or sha256",
    )
    trace_parser.add_argument(
        "target",
        help=(
            "Target to trace. Either a production id (prod_<12 hex>), a "
            "path to a production directory, or a 64-char sha256 of an asset."
        ),
    )
    trace_parser.add_argument(
        "--mermaid",
        action="store_true",
        help="Emit a Mermaid flowchart instead of the ASCII tree.",
    )
    _add_project_root(trace_parser)

    doctor_parser = subparsers.add_parser(
        "doctor",
        prog="production doctor",
        description=(
            "Emit a green / yellow / red health report. Closes the "
            "observability triad alongside production timeline (audit) and "
            "production trace (provenance)."
        ),
        help="health report for a production or project",
    )
    doctor_parser.add_argument(
        "production_id",
        nargs="?",
        default=None,
        help=(
            "Production id (e.g. prod_9915e6697a12), or an explicit path to a "
            "production directory. When omitted, run project-scoped checks "
            "against the project root."
        ),
    )
    doctor_parser.add_argument(
        "--all",
        action="store_true",
        help="Iterate every production directory under the project root.",
    )
    _add_project_root(doctor_parser)
    doctor_parser.add_argument(
        "--fast",
        dest="fast",
        action="store_true",
        default=True,
        help=(
            "Use --collect-only for the project-scoped pytest check. Pass "
            "--no-fast to run the full pytest suite instead."
        ),
    )
    doctor_parser.add_argument(
        "--no-fast",
        dest="fast",
        action="store_false",
        help="Run the full pytest suite for the project-scoped check.",
    )

    compare_parser = subparsers.add_parser(
        "compare",
        prog="production compare",
        description=(
            "Diff two productions side by side. Surfaces the proposal-first "
            "loop -- 3 angles, 3 shots, 3 colors -- by aligning the two "
            "branch tips on a single table plus a per-event divergence list."
        ),
        help="side-by-side diff of two productions",
    )
    compare_parser.add_argument(
        "prod_a",
        help=(
            "Production id (e.g. prod_9915e6697a12) or path to a production "
            "directory."
        ),
    )
    compare_parser.add_argument(
        "prod_b",
        help="Production id or path to compare against prod_a.",
    )
    compare_parser.add_argument(
        "--mermaid",
        action="store_true",
        help="Emit a Mermaid flowchart of the divergence graph.",
    )
    compare_parser.add_argument(
        "--json",
        action="store_true",
        help=(
            "Emit a machine-readable JSON document instead of the text table."
        ),
    )
    compare_parser.add_argument(
        "--only",
        metavar="AXIS",
        default=None,
        help=(
            "Show only one axis (scenes|shots|characters|reviewer|"
            "hashes|events). Replaces the table with the single row plus "
            "the divergence count."
        ),
    )
    compare_parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colours (also respects NO_COLOR env var).",
    )
    _add_project_root(compare_parser)

    run_parser = subparsers.add_parser(
        "run",
        prog="production run",
        description=(
            "Drive the full 22-stage production pipeline from an intent. "
            "The runner walks CreativeReframing -> ConfirmGate -> 20 stages, "
            "committing every proposal through ProductionService.apply_event "
            "and emitting gate decisions for evidence / consistency / "
            "consistency-contract / publication. With --no-confirm the runner "
            "uses AutoConfirmSink so the script is non-interactive."
        ),
        help="drive the full 22-stage pipeline from an intent",
    )
    # ``topic`` is a positional argument (matches src/cli/run.py). The
    # dispatcher mirrors run.py's argument shape so ``python -m src.cli
    # run --help`` and the validation call below agree with the subcommand;
    # forwarding then re-parses the same argv in run.main().
    run_parser.add_argument(
        "topic",
        help="Topic or one-line brief to drive the production.",
    )
    run_parser.add_argument(
        "--audience",
        default="educated_lay",
        help="Target audience descriptor (default: educated_lay).",
    )
    run_parser.add_argument(
        "--tone",
        default="neutral",
        help="Desired tone (default: neutral).",
    )
    run_parser.add_argument(
        "--platform",
        default="youtube",
        help="Intended publication platform (default: youtube).",
    )
    run_parser.add_argument(
        "--out",
        default="productions/",
        help="Output directory under which productions/prod_<id>/ is created.",
    )
    run_parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip the interactive ConfirmGate; use AutoConfirmSink.",
    )
    run_parser.add_argument(
        "--pick",
        default=None,
        help="With --no-confirm, force this angle. Must be one of: "
             "skeptic | advocate | contrarian.",
    )

    list_parser = subparsers.add_parser(
        "list",
        prog="production list",
        description=(
            "Enumerate every production under the search root. Lists "
            "production_id, state, intent topic, created timestamp, and "
            "audit-entry count for each prod_<id>/ directory the dispatcher "
            "can find. Sorted newest-first by created_at."
        ),
        help="enumerate every production on disk",
    )
    list_parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help=(
            "Override the search root (defaults to the current working "
            "directory). Looks for prod_<id>/ subdirs directly under this "
            "path and under output/public-demo/ + output/productions/ "
            "relative to it."
        ),
    )
    list_parser.add_argument(
        "--filter",
        dest="filter_state",
        default=None,
        choices=("DRAFT", "BRIEFED", "IN_PRODUCTION", "IN_REVIEW", "APPROVED", "PUBLISHED"),
        help=(
            "Only show productions in this state. One of: "
            "DRAFT | BRIEFED | IN_PRODUCTION | IN_REVIEW | APPROVED | PUBLISHED"
        ),
    )
    list_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON array instead of the text table.",
    )
    list_parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colours (also respects NO_COLOR env var).",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch a ``python -m src.cli`` invocation to its subcommand."""
    arguments = list(sys.argv[1:] if argv is None else argv)

    if not arguments or arguments[0] in {"-h", "--help"}:
        print(usage())
        return 0

    subcommand = arguments[0]
    if subcommand not in _COMMAND_MAINS:
        sys.stderr.write(
            f"unknown subcommand: {subcommand}\n"
            "Try 'python -m src.cli --help' for the list of subcommands.\n"
        )
        return 2

    parser = _build_parser()
    try:
        parser.parse_args(arguments)
    except SystemExit as exc:
        return int(exc.code)

    return_code = _COMMAND_MAINS[subcommand](arguments[1:])
    if subcommand == "compare" and return_code == 1:
        return 0
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
