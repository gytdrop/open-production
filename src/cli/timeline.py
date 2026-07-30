"""``production timeline <production_id>`` ï¿½ replay a production's audit trail.

Reads the ``audit.jsonl`` written by ``ProductionService`` and renders a
human-readable timeline: every gate decision, state transition, system event,
timeline assembly, and snapshot, in the order they happened. This is the most
direct way to make the audit trail visible to anyone running the demo.

Usage:
    python -m src.cli.timeline prod_9915e6697a12
    python -m src.cli.timeline prod_9915e6697a12 --json
    python -m src.cli.timeline prod_9915e6697a12 --summary
    python -m src.cli.timeline ./prod_9915e6697a12  # explicit path

Exit codes:
    0  production found and rendered
    1  usage error / production not found
    2  audit found but unreadable
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Bootstrap ``sys.path`` so internal subpackages (agents / audit / validation /
# tools / etc.) are importable via their bare names (``from schema.X`` /
# ``from agents.X``). pytest already does this via ``pyproject.toml``'s
# ``pythonpath = ["src"]``, but a ``python -m src.cli.<subcmd>`` invocation
# only sees the project root on ``sys.path``, so without this bootstrap
# transitive imports (e.g. ``from schema.production_document`` inside
# ``src/service/style_library.py``) fail with ``ModuleNotFoundError``.
_THIS_DIR = Path(__file__).resolve().parent
_SRC_ROOT = _THIS_DIR.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from src.cli._production_dir import (
    ProductionNotFoundError,
    find_production_dir,
    load_audit_entries,
    load_production_header,
)


# ---------------------------------------------------------------------------
# Decision / action-type styling.
# A small emoji-free renderer keeps the output readable in any terminal and
# safe to paste into a Markdown report.
# ---------------------------------------------------------------------------
_PASS_DECISIONS: frozenset[str] = frozenset(
    {"accepted", "pass", "publish_ok", "ok", "approved"}
)
_FAIL_DECISIONS: frozenset[str] = frozenset(
    {"rejected", "fail", "blocked", "sources_insufficient", "contradiction_detected"}
)


def _classify_decision(status: str | None) -> str:
    """Return one of ``"pass"``, ``"fail"``, ``"warn"``, ``"-"``."""
    if not status:
        return "-"
    s = status.lower()
    if s in _PASS_DECISIONS:
        return "pass"
    if s in _FAIL_DECISIONS:
        return "fail"
    return "warn"


_GLYPH = {"pass": "+", "fail": "x", "warn": "~", "-": " "}


def _ts_display(ts: str | None, first_ts: datetime | None) -> str:
    """Format an ISO-8601 timestamp as ``HH:MM:SS.mmm (+offset)``.

    ``first_ts`` is the first timestamp in the run; if it is provided, the
    function prints ``+0.000s`` offsets so the reader can scan durations
    at a glance.
    """
    if not ts:
        return "          "
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError:
        return ts[:23]
    if first_ts is not None:
        delta = (dt - first_ts).total_seconds()
        sign = "+" if delta >= 0 else "-"
        return f"+{abs(delta):6.3f}s"
    return dt.strftime("%H:%M:%S.") + dt.strftime("%f")[:3]


def _truncate(value: Any, width: int = 64) -> str:
    """Render ``value`` as a short single-line string for table cells."""
    if value is None:
        return ""
    s = str(value)
    if len(s) <= width:
        return s
    return s[: max(0, width - 1)] + "\u2026"


def _summarize_entry(entry: dict) -> tuple[str, str, str, str, str]:
    """Compress an audit entry into the five columns we print.

    Returns: ``(kind, actor, subject, decision_glyph, summary)``.
    """
    kind = str(entry.get("action_type") or "?")
    actor = str(entry.get("actor") or "?")
    decision = _classify_decision(entry.get("decision_status"))
    glyph = _GLYPH[decision]
    payload = entry.get("payload") if isinstance(entry.get("payload"), dict) else {}
    evidence = entry.get("evidence") if isinstance(entry.get("evidence"), dict) else {}

    if kind == "gate_decision":
        subject = str(entry.get("gate_name") or "?")
        if entry.get("claim_id"):
            subject += f":{entry['claim_id']}"
        summary = entry.get("reason") or entry.get("decision_status") or ""
    elif kind == "state_transition":
        subject = "->" + str(payload.get("next_state") or "?")
        summary = ""
    elif kind == "system":
        op = payload.get("operation") or "system"
        subject = str(op)
        summary_parts: list[str] = []
        for key in ("title", "branch_id", "label", "snap_id"):
            value = payload.get(key)
            if value:
                summary_parts.append(f"{key}={_truncate(value, 24)}")
        if payload.get("actor"):
            summary_parts.append(f"as={payload['actor']}")
        summary = " ".join(summary_parts)
    elif kind == "timeline_assembly":
        proposal = payload.get("proposal_label") or "edit"
        shots = payload.get("shot_count")
        dur = payload.get("total_duration_sec")
        subject = "editor"
        summary = f"{proposal} ({shots} shots, {dur}s)" if shots else proposal
    elif kind == "snapshot":
        label = payload.get("label") or "snapshot"
        subject = "snap"
        summary = f"{label} -> {(_truncate(payload.get('content_hash'), 12) or '')}"
    else:
        subject = kind
        summary = entry.get("reason") or json.dumps(payload, sort_keys=True) if payload else ""

    return kind, actor, subject, glyph, _truncate(summary, 72)


def _gate_counts(entries: list[dict]) -> dict[str, int]:
    """Count gate decisions by ``(gate_name, decision_status)``."""
    counts: dict[str, int] = {}
    for entry in entries:
        if entry.get("action_type") != "gate_decision":
            continue
        gate = entry.get("gate_name") or "?"
        status = entry.get("decision_status") or "?"
        key = f"{gate}:{status}"
        counts[key] = counts.get(key, 0) + 1
    return counts


def _state_progression(entries: list[dict]) -> list[str]:
    """Return the ordered list of state_transitions recorded in the run."""
    return [
        str((e.get("payload") or {}).get("next_state"))
        for e in entries
        if e.get("action_type") == "state_transition"
        and (e.get("payload") or {}).get("next_state")
    ]


def render_timeline(
    prod_dir: Path,
    *,
    header: dict | None = None,
    max_width: int = 100,
    summary_only: bool = False,
) -> str:
    """Render the production's audit trail as a text timeline.

    Args:
        prod_dir: Production directory containing ``audit.jsonl``.
        header: Optional production.json header (for title / state). The
            helper will re-read it if not supplied.
        max_width: Soft width for the summary column.

    Returns:
        A multi-line string suitable for printing to ``sys.stdout``.
    """
    if header is None:
        header = load_production_header(prod_dir)
    entries = load_audit_entries(prod_dir)

    title = (header or {}).get("title") or "(untitled)"
    state = (header or {}).get("state") or "?"
    prod_id = (header or {}).get("production_id") or prod_dir.name

    lines: list[str] = []
    lines.append(f"Production {prod_id} \u2014 {title}")
    lines.append(f"State: {state}    Artifacts: {prod_dir}")
    lines.append(f"Entries: {len(entries)}")

    if not entries:
        lines.append("")
        lines.append("(no audit entries recorded)")
        return "\n".join(lines)

    first_ts_str = entries[0].get("ts")
    try:
        first_ts = (
            datetime.fromisoformat(first_ts_str) if first_ts_str else None
        )
    except ValueError:
        first_ts = None
    last_ts_str = entries[-1].get("ts")
    try:
        last_ts = (
            datetime.fromisoformat(last_ts_str) if last_ts_str else None
        )
    except ValueError:
        last_ts = None

    duration_s: float | None = None
    if first_ts is not None and last_ts is not None:
        duration_s = (last_ts - first_ts).total_seconds()

    if first_ts is not None:
        lines.append(f"Started: {first_ts.isoformat()}")
    if last_ts is not None:
        lines.append(f"Ended:   {last_ts.isoformat()}")
    if duration_s is not None:
        lines.append(f"Duration: {duration_s:+.3f}s")

    progression = _state_progression(entries)
    if progression:
        lines.append("Progression: DRAFT \u2192 " + " \u2192 ".join(progression))

    counts = _gate_counts(entries)
    if counts:
        lines.append("Gate decisions:")
        for key in sorted(counts):
            lines.append(f"  {key:<48} {counts[key]}")

    lines.append("")
    if summary_only:
        return "\n".join(lines)

    lines.append(
        f"{'time':>10}  {'kind':<18} {'actor':<28} {'subject':<22} {' ':>2}  summary"
    )
    lines.append("-" * max_width)

    for entry in entries:
        kind, actor, subject, glyph, summary = _summarize_entry(entry)
        ts = _ts_display(entry.get("ts"), first_ts)
        ts_cell = ts if first_ts is not None else (entry.get("ts") or "")[:19]
        lines.append(
            f"{ts_cell:>10}  {kind:<18} {actor[:28]:<28} {subject[:22]:<22} {glyph:>2}  {summary}"
        )

    return "\n".join(lines)


def _render_json(prod_dir: Path, header: dict | None = None) -> str:
    """Render the production as a single JSON document."""
    if header is None:
        header = load_production_header(prod_dir)
    entries = load_audit_entries(prod_dir)
    return json.dumps(
        {
            "header": header,
            "audit_dir": str(prod_dir),
            "entry_count": len(entries),
            "gate_decisions": _gate_counts(entries),
            "state_progression": _state_progression(entries),
            "entries": entries,
        },
        indent=2,
        sort_keys=True,
    )


# ---------------------------------------------------------------------------
# CLI entry point.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Console encoding.
# Windows defaults to cp1252 which chokes on the unicode glyphs the renderer
# emits (right-arrow, em-dash, ellipsis). Reconfigure stdout to UTF-8 with
# a replace fallback so the script works on any platform. We do this lazily
# inside main() so importing the module has no side effects.
# ---------------------------------------------------------------------------
def _ensure_utf8_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        # Either too-old Python or a non-reconfigurable stream (e.g. pytest
        # capture). The CLI will still emit readable ASCII in that case.
        pass


def main(argv: list[str] | None = None) -> int:
    """Parse argv, render the timeline, and return a POSIX exit code."""
    parser = argparse.ArgumentParser(
        prog="production timeline",
        description=(
            "Replay a production's audit trail as a readable timeline. "
            "Surfaces every gate decision, state transition, system event, "
            "and snapshot in the order they happened."
        ),
    )
    parser.add_argument(
        "production_id",
        help=(
            "Production id (e.g. prod_9915e6697a12) or an explicit path to "
            "the production directory."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the timeline as a single JSON document instead of the text table.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print only the header + gate counts + state progression (skip the per-event table).",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Override the project root used to locate production directories.",
    )

    _ensure_utf8_stdout()
    args = parser.parse_args(argv)

    try:
        prod_dir = find_production_dir(args.production_id, project_root=args.project_root)
    except ProductionNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    header = load_production_header(prod_dir)

    if args.json:
        print(_render_json(prod_dir, header=header))
        return 0

    text = render_timeline(prod_dir, header=header, summary_only=args.summary)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
