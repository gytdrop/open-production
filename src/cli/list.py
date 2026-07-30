"""``production list`` -- enumerate every production on disk.

Discovers every ``prod_<id>/`` directory under the project root (or the
``--out`` search root) that contains an ``audit.jsonl``, reads each
``production.json`` for state + intent topic + created_at, and renders a
one-line-per-production table sorted newest-first. This is the small
utility you reach for every time you wonder "what productions exist?"
while building the web frontend -- the CLI counterpart to the web app`s
discovery step.

Usage:
    python -m src.cli.list                       # list every production under cwd
    python -m src.cli.list --out output         # list productions under output/
    python -m src.cli.list --filter PUBLISHED   # narrow to one state
    python -m src.cli.list --json               # machine-readable array

Exit codes:
    0  always (list is informational; never a gate)
    1  usage error (bad --filter value)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path


# Bootstrap ``sys.path`` so internal subpackages (schema / service / audit)
# are importable via their bare names when this file is invoked as
# ``python -m src.cli.list``. pytest already does this via pyproject.toml.
_THIS_DIR = Path(__file__).resolve().parent
_SRC_ROOT = _THIS_DIR.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from src.cli._production_dir import (  # noqa: E402
    _DEFAULT_SEARCH_DIRS,
    load_audit_entries,
    load_production_header,
)


# ---------------------------------------------------------------------------
# ANSI renderer (mirrors timeline / trace / doctor / compare / run).
# ---------------------------------------------------------------------------
_USE_ANSI: bool = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
_BOLD = "\x1b[1m" if _USE_ANSI else ""
_DIM = "\x1b[2m" if _USE_ANSI else ""
_RESET = "\x1b[0m" if _USE_ANSI else ""

_STATE_COLOURS: dict[str, str] = {
    "DRAFT": "\x1b[33m",          # yellow
    "BRIEFED": "\x1b[36m",        # cyan
    "IN_PRODUCTION": "\x1b[35m",  # magenta
    "IN_REVIEW": "\x1b[34m",      # blue
    "APPROVED": "\x1b[32m",       # green
    "PUBLISHED": "\x1b[1;32m",    # bold green
}
_KNOWN_STATES: tuple[str, ...] = (
    "DRAFT",
    "BRIEFED",
    "IN_PRODUCTION",
    "IN_REVIEW",
    "APPROVED",
    "PUBLISHED",
)


def _ensure_utf8_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


# ---------------------------------------------------------------------------
# Discovery.
# ---------------------------------------------------------------------------
def _is_production_dir(child: Path) -> bool:
    """A production directory is a ``prod_*`` subdir with an audit.jsonl."""
    return (
        child.is_dir()
        and child.name.startswith("prod_")
        and (child / "audit.jsonl").is_file()
    )


def discover_production_dirs(search_root: Path) -> list[Path]:
    """Return every production directory under ``search_root``.

    Walks the same known storage roots the timeline / trace / doctor /
    compare siblings use (``output/public-demo/``, ``output/productions/``)
    plus ``search_root`` itself, dedupes by resolved path, and returns
    the directories sorted by name (oldest prod id first; the table
    renderer re-sorts newest-first by created_at).
    """
    seen: set[str] = set()
    found: list[Path] = []

    def _maybe_add(child: Path) -> None:
        if not _is_production_dir(child):
            return
        if child.name in seen:
            return
        seen.add(child.name)
        found.append(child)

    # 1. Known storage roots (relative to search_root).
    for parent_rel in _DEFAULT_SEARCH_DIRS:
        parent = search_root / parent_rel
        if not parent.is_dir():
            continue
        for child in sorted(parent.iterdir(), key=lambda p: p.name):
            _maybe_add(child)

    # 2. search_root directly (legacy / manual write locations).
    if search_root.is_dir():
        for child in sorted(search_root.iterdir(), key=lambda p: p.name):
            _maybe_add(child)

    return found


# ---------------------------------------------------------------------------
# Summarisation.
# ---------------------------------------------------------------------------
def _safe_iso(ts: str | None) -> str:
    """Return ``YYYY-MM-DDTHH:MM`` (truncated ISO) or ``"-"`` if unparseable."""
    if not ts:
        return "-"
    try:
        dt = datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        return ts[:16] if len(ts) >= 16 else "-"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M")


def _summarise(prod_dir: Path) -> dict | None:
    """Build a one-row dict for ``prod_dir``.

    Returns ``None`` if the directory has no usable ``production.json``
    (e.g. it was written by a future recorder that emits a different
    shape). Skipping -- rather than crashing -- is the right behaviour
    for a discovery command.
    """
    header = load_production_header(prod_dir)
    production_id = header.get("production_id") or prod_dir.name
    state = header.get("state") or "UNKNOWN"
    # Topic: prefer intent.topic (the original user input); fall back to
    # the metadata title (what the publish manifest calls the production);
    # fall back to "-" if neither is set.
    intent_topic = None
    state_path = prod_dir / "production.json"
    if state_path.is_file():
        try:
            raw = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raw = None
        if isinstance(raw, dict):
            intent = raw.get("intent")
            if isinstance(intent, dict):
                intent_topic = intent.get("topic")
            if not intent_topic:
                metadata = raw.get("metadata")
                if isinstance(metadata, dict):
                    manifest = metadata.get("publish_manifest")
                    if isinstance(manifest, dict):
                        intent_topic = manifest.get("title")
            created_at = raw.get("created_at") or header.get("updated_at")
        else:
            created_at = header.get("updated_at")
    else:
        created_at = header.get("updated_at")

    entries = load_audit_entries(prod_dir)
    return {
        "production_id": production_id,
        "state": state,
        "topic": intent_topic or "-",
        "created_at": _safe_iso(created_at),
        "entries": len(entries),
        "_prod_dir": str(prod_dir),
    }


def _sort_key(summary: dict) -> tuple[str, str]:
    """Sort newest-first; tie-break by production id."""
    return (summary["created_at"], summary["production_id"])


# ---------------------------------------------------------------------------
# Renderers.
# ---------------------------------------------------------------------------
def render_table(summaries: Sequence[dict], *, use_ansi: bool = _USE_ANSI) -> str:
    """Render the fixed-width text table, sorted newest-first.

    Sorts a *copy* of ``summaries`` so callers do not have to pre-sort.
    ANSI escapes are emitted only when ``use_ansi`` is true; pass
    ``use_ansi=False`` to honour a ``--no-color`` flag or ``NO_COLOR`` env var.
    """
    bold = "\x1b[1m" if use_ansi else ""
    dim = "\x1b[2m" if use_ansi else ""
    reset = "\x1b[0m" if use_ansi else ""

    def _state_color(state: str) -> str:
        if not use_ansi:
            return ""
        return _STATE_COLOURS.get(state, "")

    headers = ("PRODUCTION ID", "STATE", "INTENT TOPIC", "CREATED", "ENTRIES")
    if not summaries:
        return f"{dim}no productions found{reset}"

    # Newest-first; tie-break by production_id descending so the ordering
    # is stable when many productions share a created_at bucket.
    ordered = sorted(
        summaries,
        key=lambda s: (s["created_at"], s["production_id"]),
        reverse=True,
    )

    rows: list[tuple[str, ...]] = []
    for s in ordered:
        rows.append(
            (
                s["production_id"],
                s["state"],
                s["topic"],
                s["created_at"],
                str(s["entries"]),
            )
        )

    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def _fmt_row(cells: tuple[str, ...], colour: str = "") -> str:
        parts = [cells[i].ljust(widths[i]) for i in range(len(cells))]
        line = "  ".join(parts)
        if colour:
            return f"{colour}{line}{reset}"
        return line

    lines = [
        bold + _fmt_row(headers) + reset,
        _fmt_row(tuple("-" * w for w in widths), dim),
    ]
    for row in rows:
        colour = _state_color(row[1])
        lines.append(_fmt_row(row, colour))
    return "\n".join(lines)


def render_json(summaries: Sequence[dict]) -> str:
    """Render as a JSON array of plain dicts (drops the internal _prod_dir)."""
    payload = [
        {
            "production_id": s["production_id"],
            "state": s["state"],
            "topic": s["topic"],
            "created_at": s["created_at"],
            "entries": s["entries"],
        }
        for s in summaries
    ]
    return json.dumps(payload, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# CLI plumbing.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="production list",
        description=(
            "Enumerate every production under the search root. Lists "
            "production_id, state, intent topic, created timestamp, and "
            "audit-entry count for each prod_<id>/ directory the dispatcher "
            "can find. Sorted newest-first by created_at."
        ),
    )
    parser.add_argument(
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
    parser.add_argument(
        "--filter",
        dest="filter_state",
        default=None,
        choices=_KNOWN_STATES,
        help=(
            "Only show productions in this state. One of: "
            + " | ".join(_KNOWN_STATES)
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON array instead of the text table.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colours (also respects NO_COLOR env var).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    _ensure_utf8_stdout()
    args = parser.parse_args(argv)

    search_root = (args.out.expanduser() if args.out is not None else Path.cwd()).resolve()

    prod_dirs = discover_production_dirs(search_root)
    summaries = [s for s in (_summarise(p) for p in prod_dirs) if s is not None]
    if args.filter_state is not None:
        summaries = [s for s in summaries if s["state"] == args.filter_state]
    summaries.sort(key=_sort_key, reverse=True)

    use_ansi = _USE_ANSI and not args.no_color
    if args.json:
        print(render_json(summaries))
    else:
        print(render_table(summaries, use_ansi=use_ansi))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
