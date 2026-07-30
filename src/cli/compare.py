"""
production compare <prod_a> <prod_b> -- side-by-side diff of two productions.

Reads two production directories, reuses the ProductionService.branch_compare()
field shape (state / scenes / shots / characters / reviewer score / content
hash / audit events) plus the AuditRecorder-readable audit.jsonl from each
side, and emits a readable diff. This is the 4th observability tool on the
timeline/trace/doctor scaffolding and the one that surfaces the proposal-
first loop: the system proposes 3 angles, 3 shots, 3 colors -- compare
makes those proposals visible side by side.

Usage:
    python -m src.cli.compare prod_aaa prod_bbb
    python -m src.cli.compare prod_aaa prod_bbb --mermaid
    python -m src.cli.compare prod_aaa prod_bbb --only scenes
    python -m src.cli.compare prod_aaa prod_bbb --json

Exit codes:
    0  always (compare is informational; never a gate)
    1  usage error / production not found
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
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
)
from src.schema.production_document import Production


# ---------------------------------------------------------------------------
# ANSI renderer.
# Mirrors the timeline / trace / doctor pattern: emoji-free glyphs, auto-
# disabled when stdout is not a TTY or NO_COLOR is set, and a clean fallback
# to plain ASCII in pipelines.
# ---------------------------------------------------------------------------
def _ansi_enabled(force_off: bool = False) -> bool:
    if force_off:
        return False
    if os.environ.get("NO_COLOR") is not None:
        return False
    return sys.stdout.isatty()


_USE_ANSI: bool = _ansi_enabled()
_CYAN = "\x1b[36m" if _USE_ANSI else ""
_YELLOW = "\x1b[33m" if _USE_ANSI else ""
_BOLD = "\x1b[1m" if _USE_ANSI else ""
_DIM = "\x1b[2m" if _USE_ANSI else ""
_RED = "\x1b[31m" if _USE_ANSI else ""
_GREEN = "\x1b[32m" if _USE_ANSI else ""
_RESET = "\x1b[0m" if _USE_ANSI else ""


# ---------------------------------------------------------------------------
# Errors.
# ---------------------------------------------------------------------------
class CompareUsageError(ValueError):
    """Raised when the CLI cannot resolve the target productions."""


# ---------------------------------------------------------------------------
# Axis loading.
#
# The CLI takes two production directories, but the existing
# ProductionService.branch_compare() operates on a single Production with
# two branch ids. We load each side through ProductionService.load() (so the
# SHA-256 sidecar is verified and _dict_to_production is reused) and then
# read the same field shapes that branch_compare() reads.
# ---------------------------------------------------------------------------
def _load_production(prod_dir: Path) -> Production:
    """Load a Production from prod_dir via ProductionService."""
    from src.service.production_service import ProductionService

    svc = ProductionService(storage_dir=prod_dir.parent)
    return svc.load(prod_dir.name)


def _count_shots(prod: Production) -> int:
    return sum(len(scene.shots) for scene in prod.scenes)


def _reviewer_score(prod: Production):
    """Average reviewer verdict score across all shots.

    Mirrors the score-aggregation logic inside ProductionService.
    branch_compare(). This CLI is the public surface for that comparison
    shape; the existing service method is wired up here, not reimplemented.
    """
    scores = []
    for scene in prod.scenes:
        for shot in scene.shots:
            if shot.generation and shot.generation.reviewer_verdict:
                v = shot.generation.reviewer_verdict.get("score")
                if v is None:
                    continue
                try:
                    scores.append(float(v))
                except (TypeError, ValueError):
                    pass
    if not scores:
        return None
    return round(sum(scores) / len(scores), 3)


def _content_root_hash(prod_dir: Path):
    """Return the 8-char content root hash for prod_dir.

    Prefers the production.json.sha256 sidecar (same source as
    ProductionService.load()). Falls back to a live SHA-256 of
    production.json if the sidecar is absent.
    """
    sidecar = prod_dir / "production.json.sha256"
    if sidecar.is_file():
        try:
            text = sidecar.read_text(encoding="utf-8").strip()
        except OSError:
            text = ""
        if text:
            return text[:8]
    state = prod_dir / "production.json"
    if state.is_file():
        try:
            digest = hashlib.sha256(state.read_bytes()).hexdigest()
            return digest[:8]
        except OSError:
            return None
    return None


# ---------------------------------------------------------------------------
# Axes: the seven side-by-side rows.
# Each axis is (name, value_a, value_b, delta). For non-numeric axes delta
# is None (the renderer shows diff/same instead).
# ---------------------------------------------------------------------------
def _build_axes(prod_a, prod_b, prod_dir_a, prod_dir_b):
    score_a = _reviewer_score(prod_a)
    score_b = _reviewer_score(prod_b)
    score_delta = None
    if score_a is not None and score_b is not None:
        score_delta = round(score_b - score_a, 3)
    scenes_a = len(prod_a.scenes)
    scenes_b = len(prod_b.scenes)
    shots_a = _count_shots(prod_a)
    shots_b = _count_shots(prod_b)
    chars_a = len(prod_a.characters)
    chars_b = len(prod_b.characters)
    events_a = len(prod_a.audit_trail)
    events_b = len(prod_b.audit_trail)
    hash_a = _content_root_hash(prod_dir_a)
    hash_b = _content_root_hash(prod_dir_b)

    return [
        ("state", prod_a.state, prod_b.state, None),
        ("scenes", scenes_a, scenes_b, scenes_b - scenes_a),
        ("shots", shots_a, shots_b, shots_b - shots_a),
        ("characters", chars_a, chars_b, chars_b - chars_a),
        ("reviewer score", score_a, score_b, score_delta),
        ("content root hash", hash_a, hash_b, None),
        ("audit events", events_a, events_b, events_b - events_a),
    ]


# ---------------------------------------------------------------------------
# Divergence.
#
# Two productions share a common ancestor when their audit trails agree at
# some aligned index. We pair entries by position and call two entries
# "matching" when their action_type, state_after, and payload are all equal.
# The common ancestor is the latest matching pair; entries past it are the
# divergence list rendered per event.
# ---------------------------------------------------------------------------
def _events_match(a, b):
    return (
        a.get("action_type") == b.get("action_type")
        and a.get("state_after") == b.get("state_after")
        and a.get("payload") == b.get("payload")
    )


def _summarize_change(entry):
    """Render an audit entry as a short one-line description of the change."""
    if entry is None:
        return "(absent)"
    action = entry.get("action_type") or "?"
    payload = entry.get("payload") if isinstance(entry.get("payload"), dict) else {}
    reason = entry.get("reason") or ""
    if action == "snapshot":
        label = payload.get("label") or ""
        quoted = chr(39).join(["", label, ""]) if label else ""
        return ("snapshot " + quoted) if label else "snapshot"
    if action == "system":
        op = payload.get("operation") or ""
        if op == "create_branch":
            label = payload.get("label") or ""
            return "create_branch " + chr(39) + label + chr(39)
        if op == "init":
            title = payload.get("title") or ""
            return "init " + chr(39) + title + chr(39)
        if op == "archive":
            return "archive"
        return op or "system"
    if action == "state_transition":
        return "-> " + str(payload.get("next_state") or "?")
    if action == "timeline_assembly":
        label = payload.get("proposal_label") or ""
        return ("timeline " + chr(39) + label + chr(39)) if label else "timeline_assembly"
    if action == "gate_decision":
        gate = entry.get("gate_name") or ""
        claim = entry.get("claim_id") or ""
        status = entry.get("decision_status") or "?"
        return f"{gate}:{claim} = {status}"
    if reason:
        return f"{action} ({reason[:60]})"
    if payload:
        return f"{action} {json.dumps(payload, sort_keys=True)[:48]}"
    return action


def _summarize_with_state(entry):
    """Render an entry as summary plus an optional state_after=... suffix."""
    if entry is None:
        return "(absent)"
    summary = _summarize_change(entry)
    sa = entry.get("state_after")
    if sa:
        return f"{summary} (state_after={sa})"
    return summary


def _compute_divergence(entries_a, entries_b):
    """Find the latest matching pair and return paired divergence events."""
    last_match = None
    divergences = []
    min_len = min(len(entries_a), len(entries_b))
    for i in range(min_len):
        a, b = entries_a[i], entries_b[i]
        if _events_match(a, b):
            last_match = i
        else:
            divergences.append({"idx": i, "ev_a": a, "ev_b": b})
    for i in range(min_len, len(entries_a)):
        divergences.append({"idx": i, "ev_a": entries_a[i], "ev_b": None})
    for i in range(min_len, len(entries_b)):
        divergences.append({"idx": i, "ev_a": None, "ev_b": entries_b[i]})
    return last_match, divergences


# ---------------------------------------------------------------------------
# Comparable wrapper.
# ---------------------------------------------------------------------------
class CompareResult:
    """Container returned by build_compare()."""

    def __init__(self, prod_dir_a, prod_dir_b, prod_a, prod_b, axes,
                 common_ancestor_idx, divergence_events):
        self.prod_dir_a = prod_dir_a
        self.prod_dir_b = prod_dir_b
        self.prod_a = prod_a
        self.prod_b = prod_b
        self.axes = axes
        self.common_ancestor_idx = common_ancestor_idx
        self.divergence_events = divergence_events
        self.same_production = prod_dir_a.resolve() == prod_dir_b.resolve()


def build_compare(prod_dir_a, prod_dir_b):
    """Build a CompareResult for two production directories."""
    prod_a = _load_production(prod_dir_a)
    prod_b = _load_production(prod_dir_b)
    axes = _build_axes(prod_a, prod_b, prod_dir_a, prod_dir_b)
    entries_a = load_audit_entries(prod_dir_a)
    entries_b = load_audit_entries(prod_dir_b)
    ancestor_idx, divergence = _compute_divergence(entries_a, entries_b)
    return CompareResult(
        prod_dir_a=prod_dir_a,
        prod_dir_b=prod_dir_b, prod_a=prod_a, prod_b=prod_b,
        axes=axes, common_ancestor_idx=ancestor_idx,
        divergence_events=divergence,
    )


# ---------------------------------------------------------------------------
# Rendering.
# ---------------------------------------------------------------------------
_ONLY_ALIASES = {
    "scenes": "scenes",
    "shots": "shots",
    "characters": "characters",
    "reviewer": "reviewer score",
    "hashes": "content root hash",
    "events": "audit events",
}


def _format_value(value):
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _format_delta(delta, value_a, value_b):
    if delta is None:
        return "diff" if value_a != value_b else "same"
    if isinstance(delta, float):
        if delta > 0:
            return f"+{delta:.2f}"
        if delta < 0:
            return f"{delta:.2f}"
        return "0"
    if delta > 0:
        return f"+{delta}"
    if delta < 0:
        return str(delta)
    return "0"


def _truncate(value, width):
    if len(value) <= width:
        return value
    return value[: max(0, width - 1)] + chr(8230)


def render_compare(result, *, only=None, use_color=None):
    """Render a CompareResult as a side-by-side ASCII table.

    only filters the table to a single axis (one of the values in
    _ONLY_ALIASES). use_color overrides automatic TTY detection.
    """
    if use_color is None:
        use_color = _USE_ANSI
    cyan = _CYAN if use_color else ""
    yellow = _YELLOW if use_color else ""
    bold = _BOLD if use_color else ""
    dim = _DIM if use_color else ""
    red = _RED if use_color else ""
    green = _GREEN if use_color else ""
    reset = _RESET if use_color else ""

    id_a = result.prod_a.id
    id_b = result.prod_b.id
    title = bold + "compare" + reset + ": " + cyan + id_a + reset + " vs " + cyan + id_b + reset
    if result.same_production:
        title += "  " + dim + "(same production)" + reset
    lines = [title, "=" * 80]

    target_axis = None
    if only is not None:
        if only not in _ONLY_ALIASES:
            raise CompareUsageError(
                f"unknown --only value {only!r}; expected one of "
                + ", ".join(sorted(_ONLY_ALIASES))
            )
        target_axis = _ONLY_ALIASES[only]

    col_axis = 22
    col_value = 22
    col_delta = 10
    header = (
        "Axis".ljust(col_axis) + " "
        + _truncate(id_a, col_value).ljust(col_value) + " "
        + _truncate(id_b, col_value).ljust(col_value) + " "
        + "Delta".rjust(col_delta)
    )
    lines.append(header)
    lines.append("-" * (col_axis + col_value * 2 + col_delta + 3))

    shown_axes = 0
    for name, value_a, value_b, delta in result.axes:
        if target_axis is not None and name != target_axis:
            continue
        shown_axes += 1
        rendered_a = _format_value(value_a)
        rendered_b = _format_value(value_b)
        delta_str = _format_delta(delta, value_a, value_b)
        if delta is not None and isinstance(delta, (int, float)):
            if delta > 0:
                delta_str = green + delta_str + reset
            elif delta < 0:
                delta_str = red + delta_str + reset
        line = (
            name.ljust(col_axis) + " "
            + _truncate(rendered_a, col_value).ljust(col_value) + " "
            + _truncate(rendered_b, col_value).ljust(col_value) + " "
            + delta_str.rjust(col_delta)
        )
        lines.append(line)

    lines.append("")

    div_count = len(result.divergence_events)
    if result.common_ancestor_idx is not None:
        ancestor_label = _describe_ancestor(result)
        lines.append(
            "divergence events (since common ancestor): " + yellow + str(div_count) + reset
        )
        lines.append("common ancestor: " + ancestor_label)
    else:
        lines.append(
            "no common ancestor -- showing top-level diff only ("
            + yellow + str(div_count) + reset + " divergent event(s))"
        )
    lines.append("")

    if only is None and result.divergence_events:
        for pair in result.divergence_events:
            lines.append(_format_divergence(pair, result, dim=dim, reset=reset))

    if shown_axes == 0 and only is not None:
        lines.append(f"(no data for axis {only!r})")
    return chr(10).join(lines)


def _describe_ancestor(result):
    if result.common_ancestor_idx is None:
        return "(none)"
    idx = result.common_ancestor_idx
    a_entries = load_audit_entries(result.prod_dir_a)
    b_entries = load_audit_entries(result.prod_dir_b)
    if idx >= len(a_entries) or idx >= len(b_entries):
        return f"event #{idx}"
    entry = a_entries[idx]
    eid = entry.get("id") or ""
    return f"{eid} (event #{idx})"


def _format_divergence(pair, result, *, dim="", reset=""):
    """Render a divergence pair as a side-by-side single-line statement."""
    idx = pair.get("idx", -1)
    ev_a = pair.get("ev_a")
    ev_b = pair.get("ev_b")
    summary_a = _summarize_with_state(ev_a)
    summary_b = _summarize_with_state(ev_b)
    ra = (ev_a.get("reason") or "").strip() if ev_a else ""
    rb = (ev_b.get("reason") or "").strip() if ev_b else ""
    if ev_a and ev_b:
        line = (
            f"  {dim}at event {idx + 1}:{reset} "
            f"{result.prod_a.id} applied \"" + summary_a + "\", "
            f"{result.prod_b.id} applied \"" + summary_b + "\"."
        )
        if ra or rb:
            line += (
                f"  Rationale: {result.prod_a.id}=" + (ra or "(none)")
                + "; " + result.prod_b.id + "=" + (rb or "(none)") + "."
            )
        return line
    if ev_a:
        line = (
            f"  {dim}at event {idx + 1}:{reset} "
            f"{result.prod_a.id} applied \"" + summary_a + "\", "
            f"{result.prod_b.id} {dim}(absent){reset}."
        )
        if ra:
            line += f"  Rationale: {ra}."
        return line
    line = (
        f"  {dim}at event {idx + 1}:{reset} "
        f"{result.prod_a.id} {dim}(absent){reset}, "
        f"{result.prod_b.id} applied \"" + summary_b + "\"."
    )
    if rb:
        line += f"  Rationale: {rb}."
    return line


# ---------------------------------------------------------------------------
# Mermaid.
# ---------------------------------------------------------------------------
def render_mermaid(result):
    """Render the divergence graph as a Mermaid flowchart TD."""
    lines = ["flowchart TD"]
    prod_a_id = "a_" + _mangle(result.prod_a.id)
    prod_b_id = "b_" + _mangle(result.prod_b.id)
    lines.append(
        "  " + prod_a_id + "[\"" + result.prod_a.id
        + "<br/>state=" + result.prod_a.state
        + "<br/>scenes=" + str(len(result.prod_a.scenes))
        + " shots=" + str(_count_shots(result.prod_a)) + "\"]"
    )
    lines.append(
        "  " + prod_b_id + "[\"" + result.prod_b.id
        + "<br/>state=" + result.prod_b.state
        + "<br/>scenes=" + str(len(result.prod_b.scenes))
        + " shots=" + str(_count_shots(result.prod_b)) + "\"]"
    )
    if result.common_ancestor_idx is not None:
        anc_label = _describe_ancestor(result)
        anc_id = "c_ancestor"
        lines.append("  " + anc_id + "[\"common ancestor<br/>" + _mangle(anc_label) + "\"]")
        lines.append("  " + anc_id + " --> " + prod_a_id)
        lines.append("  " + anc_id + " --> " + prod_b_id)
    else:
        lines.append("  " + prod_a_id + " -->|no common ancestor| " + prod_b_id)
    div = len(result.divergence_events)
    if div:
        lines.append("  c_div[\"divergence events: " + str(div) + "\"]")
        lines.append("  " + prod_a_id + " -.-> c_div")
        lines.append("  " + prod_b_id + " -.-> c_div")
    return chr(10).join(lines)


def _mangle(value):
    """Make a string safe for inclusion inside a Mermaid node label."""
    safe = value.replace(chr(34), chr(39)).replace(chr(10), " ")
    safe = safe.replace("<", "(").replace(">", ")")
    return safe


# ---------------------------------------------------------------------------
# JSON rendering.
# ---------------------------------------------------------------------------
def render_json(result):
    """Render the comparison as a single JSON document."""
    axes = []
    for name, value_a, value_b, delta in result.axes:
        axes.append({
            "axis": name,
            "value_a": value_a,
            "value_b": value_b,
            "delta": delta,
            "match": value_a == value_b,
        })
    payload = {
        "prod_a": {
            "id": result.prod_a.id,
            "dir": str(result.prod_dir_a),
            "state": result.prod_a.state,
            "title": result.prod_a.title,
        },
        "prod_b": {
            "id": result.prod_b.id,
            "dir": str(result.prod_dir_b),
            "state": result.prod_b.state,
            "title": result.prod_b.title,
        },
        "same_production": result.same_production,
        "axes": axes,
        "common_ancestor_idx": result.common_ancestor_idx,
        "divergence_count": len(result.divergence_events),
        "divergence_events": [
            {
                "idx": pair.get("idx"),
                "prod_a": pair.get("ev_a"),
                "prod_b": pair.get("ev_b"),
            }
            for pair in result.divergence_events
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


# ---------------------------------------------------------------------------
# CLI entry point.
# ---------------------------------------------------------------------------
def _ensure_utf8_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


def main(argv=None):
    """Parse argv, render the comparison, and return a POSIX exit code."""
    parser = argparse.ArgumentParser(
        prog="production compare",
        description=(
            "Diff two productions side by side. Surfaces the proposal-first "
            "loop -- 3 angles, 3 shots, 3 colors -- by aligning the two "
            "branch tips on a single table plus a per-event divergence "
            "list. Reuses ProductionService.branch_compare() field shape."
        ),
    )
    parser.add_argument(
        "prod_a",
        help=(
            "Production id (e.g. prod_9915e6697a12) or path to a "
            "production directory."
        ),
    )
    parser.add_argument(
        "prod_b",
        help="Production id or path to compare against prod_a.",
    )
    parser.add_argument(
        "--mermaid",
        action="store_true",
        help="Emit a Mermaid flowchart of the divergence graph.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON document instead of the text table.",
    )
    parser.add_argument(
        "--only",
        metavar="AXIS",
        default=None,
        help=(
            "Show only one axis (scenes|shots|characters|reviewer|"
            "hashes|events). Replaces the table with the single row plus "
            "the divergence count."
        ),
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colours (also respects NO_COLOR env var).",
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
        prod_dir_a = find_production_dir(args.prod_a, project_root=args.project_root)
        prod_dir_b = find_production_dir(args.prod_b, project_root=args.project_root)
    except ProductionNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        result = build_compare(prod_dir_a, prod_dir_b)
    except CompareUsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.mermaid:
        print(render_mermaid(result))
        return 0
    if args.json:
        print(render_json(result))
        return 0

    try:
        text = render_compare(result, only=args.only, use_color=not args.no_color)
    except CompareUsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())