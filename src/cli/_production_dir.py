"""Shared helpers for the ``src.cli.*`` commands.

The Open Production CLI is small (timeline, trace, doctor, run). These helpers
keep the location-resolution logic consistent across commands so a production
written by ``ProductionService`` can be read back by any ``production <cmd>``
sub-command.
"""
from __future__ import annotations

import json
from pathlib import Path


# ---------------------------------------------------------------------------
# Default search locations for a production directory.
# Mirrors ``src.public_demo.server._get_service`` search order.
# ---------------------------------------------------------------------------
_DEFAULT_SEARCH_DIRS: tuple[str, ...] = (
    "output/public-demo",
    "output/productions",
)


class ProductionNotFoundError(LookupError):
    """Raised when a production_id cannot be located in any known directory."""


def find_production_dir(production_id: str, project_root: Path | None = None) -> Path:
    """Locate the directory that owns ``production_id``.

    Args:
        production_id: The ``prod_<12 hex>`` id, or a path to a directory
            that already contains ``audit.jsonl``.
        project_root: Optional repository root. Defaults to the current
            working directory.

    Returns:
        The resolved production directory (always contains ``audit.jsonl``).

    Raises:
        ProductionNotFoundError: if no directory containing the production
            is found.
    """
    root = Path(project_root) if project_root is not None else Path.cwd()

    # 1. Explicit path provided.
    candidate = Path(production_id)
    if candidate.is_dir() and (candidate / "audit.jsonl").is_file():
        return candidate.resolve()

    # 2. Search known storage roots relative to project root.
    for parent_rel in _DEFAULT_SEARCH_DIRS:
        parent = root / parent_rel
        if not parent.is_dir():
            continue
        candidate = parent / production_id
        if candidate.is_dir() and (candidate / "audit.jsonl").is_file():
            return candidate.resolve()

    # 3. Search the project root directly (legacy / manual write locations
    #    such as the ``prod_9915e6697a12/`` shipped with the audit fixture).
    candidate = root / production_id
    if candidate.is_dir() and (candidate / "audit.jsonl").is_file():
        return candidate.resolve()

    raise ProductionNotFoundError(
        f"Production {production_id!r} not found. Searched: "
        + ", ".join(str(root / rel) for rel in _DEFAULT_SEARCH_DIRS)
        + f", {root / production_id}"
    )


def load_production_header(prod_dir: Path) -> dict:
    """Read the top-level production.json and return a small header dict.

    Returns an empty dict if production.json is missing or malformed.
    """
    state_path = prod_dir / "production.json"
    if not state_path.is_file():
        return {}
    try:
        text = state_path.read_text(encoding="utf-8")
        data = json.loads(text)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    metadata = data.get("metadata") or {}
    title: str | None = None
    audit_trail = data.get("audit_trail")
    if isinstance(audit_trail, list) and audit_trail:
        first = audit_trail[0]
        if isinstance(first, dict):
            payload = first.get("payload") or {}
            if isinstance(payload, dict):
                title = payload.get("title")  # type: ignore[assignment]
    if not title:
        title = metadata.get("title") if isinstance(metadata, dict) else None
    return {
        "production_id": data.get("production_id") or prod_dir.name,
        "title": title,
        "state": data.get("state"),
        "version": data.get("version"),
        "updated_at": data.get("updated_at"),
    }


def load_audit_entries(prod_dir: Path) -> list[dict]:
    """Read ``audit.jsonl`` and return a list of entry dicts.

    Malformed lines are skipped silently (the production may have been
    written by an older recorder that emitted a different shape). Returns
    ``[]`` if the file is missing or empty.
    """
    journal = prod_dir / "audit.jsonl"
    if not journal.is_file():
        return []
    try:
        text = journal.read_text(encoding="utf-8")
    except OSError:
        return []
    entries: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            entries.append(obj)
    return entries
