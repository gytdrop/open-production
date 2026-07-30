"""``production trace <sha256>`` â€” render an asset / production lineage DAG.

Walks ``audit.jsonl`` + ``production.json`` for the target production and
renders the content-addressed lineage as a tree: assets (Reference.sha256
materialized via ``asset://<sha256[:8]>``), generations
(``GenerationResult.output_sha256``), snapshots (``VersionSnapshot.
content_hash``), branches (``Branch``), and merges (audit events whose
``action_type == "merge"``), connected by derivation edges rooted at the
production or the matched asset.

Usage:
    python -m src.cli.trace prod_9915e6697a12
    python -m src.cli.trace <sha256>
    python -m src.cli.trace prod_9915e6697a12 --mermaid

Exit codes:
    0  lineage traced and rendered
    1  usage error / target not found / invalid hash
    2  cycle detected in the lineage graph
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


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
# Validation helpers.
# Public SHA256_RE accepts a single canonical sha256 spelling: 64 lowercase hex chars.: 64 lowercase hex chars. Asset
# content-addressing in the kernel normalizes to this form before hashing.
# ---------------------------------------------------------------------------
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

# Production id (``prod_<suffix>``) — accepted when tracing an entire
# production. We don't validate further: the production resolver will look up
# the directory via ``find_production_dir``.
_PROD_PREFIX = "prod_"


# ---------------------------------------------------------------------------
# Errors.
# ---------------------------------------------------------------------------
class TraceUsageError(ValueError):
    """Raised when the CLI target cannot be resolved to a production or hash."""


# ---------------------------------------------------------------------------
# DAG node model.
# ---------------------------------------------------------------------------
@dataclass
class TraceNode:
    """A single vertex in the lineage DAG.

    Attributes:
        id: Unique stable identifier across the trace; used as the rendering
            row label and as the Mermaid node id.
        kind: One of ``production``, ``asset``, ``ref``, ``generation``,
            ``snapshot``, ``branch``, ``merge``.
        label: A short single-line description shown in the ASCII tree.
        sha256: The content hash carried by this node, when one exists. We
            truncate it to 8 chars in the renderer; store full here.
        parents: Node ids this node derives from.
        children: Node ids derived from this node.
    """
    id: str
    kind: str
    label: str
    sha256: str | None = None
    parents: list[str] = field(default_factory=list)
    children: list[str] = field(default_factory=list)


@dataclass
class TraceResult:
    """Container returned by :func:`build_dag`."""
    prod_dir: Path
    header: dict
    nodes: list[TraceNode]
    roots: list[str]  # node ids with no parents (RAW: not yet deduped into a tree)
    notices: list[str] = field(default_factory=list)  # non-fatal hints


# ---------------------------------------------------------------------------
# Target resolution.
# ---------------------------------------------------------------------------
def _validate_sha256(value: str) -> str:
    """Return the canonical sha256 string or raise :class:`TraceUsageError`."""
    if not SHA256_RE.match(value):
        raise TraceUsageError(
            f"invalid sha256 {value!r}: expected 64 lowercase hex characters"
        )
    return value


def _iter_production_dirs(project_root: Path) -> Iterable[Path]:
    """Yield every directory under known storage roots that owns an audit.jsonl.

    Mirrors the search order used by :func:`find_production_dir` but does not
    stop at the first match \u2014 the trace command needs to scan across
    productions when given a raw sha256, since content-addressed assets can be
    referenced from any production's state.
    """
    seen: set[Path] = set()
    candidates: list[Path] = []

    def _try(parent: Path) -> None:
        if not parent.is_dir():
            return
        for child in parent.iterdir():
            if not child.is_dir():
                continue
            if (child / "audit.jsonl").is_file():
                resolved = child.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    candidates.append(resolved)

    for rel in ("output/public-demo", "output/productions"):
        _try(project_root / rel)
    # Project root \u2014 ships with the ``prod_9915e6697a12`` fixture.
    _try(project_root)

    # Sort so repeated runs resolve the same way.
    candidates.sort()
    return candidates


def _production_contains_sha(prod_dir: Path, sha: str) -> bool:
    """Return True if any reference, snapshot or generation hash matches ``sha``."""
    state_path = prod_dir / "production.json"
    if state_path.is_file():
        try:
            data = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = None
        if isinstance(data, dict):
            if _scan_for_sha(data, sha):
                return True

    for entry in load_audit_entries(prod_dir):
        payload = entry.get("payload")
        if isinstance(payload, dict) and _scan_for_sha(payload, sha):
            return True
        if _scan_for_sha(entry, sha):
            return True
    return False


def _scan_for_sha(obj: Any, sha: str) -> bool:
    """Recursive search for ``sha`` in any string field of ``obj``."""
    target = sha.lower()
    if isinstance(obj, dict):
        return any(_scan_for_sha(v, target) for v in obj.values())
    if isinstance(obj, list):
        return any(_scan_for_sha(v, target) for v in obj)
    if isinstance(obj, str):
        return obj.lower() == target
    return False


def resolve_target(
    target: str,
    project_root: Path | None = None,
) -> tuple[Path, str | None]:
    """Resolve a CLI target to (production_dir, sha256_or_None).

    Args:
        target: Either a production id (``prod_...``), a path to a directory
            that owns an ``audit.jsonl``, or a 64-char sha256.
        project_root: Optional repository root. Defaults to CWD.

    Returns:
        A tuple ``(production_dir, sha256)``. ``sha256`` is None when the
        target was a production id or directory path.

    Raises:
        TraceUsageError: when the input cannot be parsed.
        ProductionNotFoundError: when no matching production can be located.
    """
    root = Path(project_root) if project_root is not None else Path.cwd()

    # 1. Production id (``prod_<suffix>``) or explicit path. Try the shared
    #    resolver first; this honors the same search order as `production
    #    timeline <id>`.
    if target.startswith(_PROD_PREFIX) or Path(target).is_dir():
        try:
            prod_dir = find_production_dir(target, project_root=root)
        except ProductionNotFoundError:
            # No stored production by that id \u2014 only valid if it was a
            # malformed id (not a path). Re-raise to keep exit semantics.
            raise
        return prod_dir, None

    # 2. Sha256 hash \u2014 search every known production for a match.
    sha = _validate_sha256(target)
    for candidate in _iter_production_dirs(root):
        if _production_contains_sha(candidate, sha):
            return candidate, sha

    raise ProductionNotFoundError(
        f"sha256 {sha!r} not found in any known production under {root}"
    )


# ---------------------------------------------------------------------------
# DAG construction.
# ---------------------------------------------------------------------------
def build_dag(
    prod_dir: Path,
    target_sha: str | None = None,
) -> TraceResult:
    """Walk audit + state files under ``prod_dir`` and produce a TraceResult."""
    header = load_production_header(prod_dir)
    entries = load_audit_entries(prod_dir)

    state_path = prod_dir / "production.json"
    state: dict = {}
    if state_path.is_file():
        try:
            loaded = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            loaded = {}
        if isinstance(loaded, dict):
            state = loaded

    notices: list[str] = []
    nodes: list[TraceNode] = []
    by_id: dict[str, TraceNode] = {}

    def _add(node: TraceNode) -> TraceNode:
        if node.id in by_id:
            return by_id[node.id]
        by_id[node.id] = node
        nodes.append(node)
        return node

    def _link(parent_id: str, child_id: str) -> None:
        """Add a parent \u2192 child edge, ignoring self-edges and duplicates."""
        if not parent_id or not child_id or parent_id == child_id:
            return
        parent = by_id.get(parent_id)
        child = by_id.get(child_id)
        if parent is None or child is None:
            return
        if child_id not in parent.children:
            parent.children.append(child_id)
        if parent_id not in child.parents:
            child.parents.append(parent_id)

    production_id = header.get("production_id") or prod_dir.name
    prod_node = _add(
        TraceNode(
            id=f"production:{production_id}",
            kind="production",
            label=f"production {production_id}",
            sha256=None,
        )
    )

    # ------------------------------------------------------------------
    # References (assets / refs).
    # ------------------------------------------------------------------
    references = state.get("references") or []
    if isinstance(references, list):
        for ref in references:
            if not isinstance(ref, dict):
                continue
            ref_id = ref.get("id")
            if not ref_id:
                continue
            sha = ref.get("sha256")
            if isinstance(sha, str) and SHA256_RE.match(sha):
                node = _add(
                    TraceNode(
                        id=f"asset:{sha}",
                        kind="asset",
                        label=f"asset {_short(ref_id)}",
                        sha256=sha,
                    )
                )
            else:
                node = _add(
                    TraceNode(
                        id=f"ref:{ref_id}",
                        kind="ref",
                        label=f"ref {_short(ref_id)}",
                        sha256=None,
                    )
                )
            _link(prod_node.id, node.id)

    # ------------------------------------------------------------------
    # Branches + their snapshots.
    # ------------------------------------------------------------------
    branches = state.get("branches") or []
    if isinstance(branches, list):
        for branch in branches:
            if not isinstance(branch, dict):
                continue
            bid = branch.get("id")
            if not bid:
                continue
            label = branch.get("name") or _short(bid)
            node = _add(
                TraceNode(
                    id=f"branch:{bid}",
                    kind="branch",
                    label=f"branch {_short(bid)} {label!r}",
                    sha256=None,
                )
            )
            _link(prod_node.id, node.id)

    snapshots = state.get("snapshots") or []
    if isinstance(snapshots, list):
        for snap in snapshots:
            if not isinstance(snap, dict):
                continue
            sid = snap.get("id")
            sha = snap.get("content_hash")
            if not sid:
                continue
            sha_str = sha if isinstance(sha, str) and SHA256_RE.match(sha) else None
            node = _add(
                TraceNode(
                    id=f"snapshot:{sid}",
                    kind="snapshot",
                    label=f"snapshot {_short(sid)}" + (
                        f" content={sha[:8]}" if sha_str else ""
                    ),
                    sha256=sha_str,
                )
            )
            snap_branch = snap.get("branch_id")
            if isinstance(snap_branch, str) and snap_branch:
                _link(f"branch:{snap_branch}", node.id)
            else:
                _link(prod_node.id, node.id)

    # ------------------------------------------------------------------
    # Generations \u2014 walk shots / generations inside scenes.
    # ------------------------------------------------------------------
    scenes = state.get("scenes") or []
    if isinstance(scenes, list):
        for scene in scenes:
            if not isinstance(scene, dict):
                continue
            shots = scene.get("shots") or []
            if not isinstance(shots, list):
                continue
            for shot in shots:
                if not isinstance(shot, dict):
                    continue
                shot_id = shot.get("id") or "?"
                gen = shot.get("generation") if isinstance(shot.get("generation"), dict) else None
                if not gen:
                    continue
                out_sha = gen.get("output_sha256")
                inputs = gen.get("input_sha256s") or []
                if not isinstance(out_sha, str) or not SHA256_RE.match(out_sha):
                    continue
                gen_node = _add(
                    TraceNode(
                        id=f"generation:{out_sha}",
                        kind="generation",
                        label=f"generation {_short(shot_id)} -> {out_sha[:8]}",
                        sha256=out_sha,
                    )
                )
                _link(prod_node.id, gen_node.id)
                if isinstance(inputs, list):
                    for input_sha in inputs:
                        if isinstance(input_sha, str) and SHA256_RE.match(input_sha):
                            asset_node = _add(
                                TraceNode(
                                    id=f"asset:{input_sha}",
                                    kind="asset",
                                    label=f"asset input {input_sha[:8]}",
                                    sha256=input_sha,
                                )
                            )
                            _link(prod_node.id, asset_node.id)
                            _link(asset_node.id, gen_node.id)

    # ------------------------------------------------------------------
    # Merge events (audit-based).
    # ------------------------------------------------------------------
    for entry in entries:
        if entry.get("action_type") == "merge":
            payload = entry.get("payload") if isinstance(entry.get("payload"), dict) else {}
            src = payload.get("source_branch_id")
            if isinstance(src, str) and src:
                merge_id = f"merge:{entry.get('id', _short(src))}"
                node = _add(
                    TraceNode(
                        id=merge_id,
                        kind="merge",
                        label=f"merge {_short(payload.get('label') or src)}",
                        sha256=None,
                    )
                )
                _link(f"branch:{src}", node.id)

    # ------------------------------------------------------------------
    # Optional focus: when target_sha is provided, prune to the connected
    # subgraph anchored at the node that carries it.
    # ------------------------------------------------------------------
    roots: list[str]
    if target_sha:
        focus_id = _find_node_for_sha(nodes, target_sha)
        if focus_id is None:
            notices.append(
                f"sha256 {target_sha!r} not found inside {production_id}; "
                "rendering entire production graph anyway."
            )
            roots = [prod_node.id]
        else:
            keep = _reachable_subgraph(nodes, focus_id)
            kept_nodes = [n for n in nodes if n.id in keep]
            pruned = [n.id for n in nodes if n.id not in keep]
            if pruned:
                notices.append(
                    f"pruned {len(pruned)} unrelated node(s); focusing on {focus_id}."
                )
            nodes = kept_nodes
            # Render the full context: pick the kept subgraphs actual roots
            # (no parents in the kept set) so ancestors and descendants both
            # appear around the focused node.
            roots = [n.id for n in nodes if not n.parents]
    else:
        roots = [prod_node.id]

    # ------------------------------------------------------------------
    # Cycle detection \u2014 refuse to render a cyclic graph.
    # ------------------------------------------------------------------
    _detect_cycle(nodes)

    return TraceResult(
        prod_dir=prod_dir,
        header=header,
        nodes=nodes,
        roots=roots,
        notices=notices,
    )


def _find_node_for_sha(nodes: list[TraceNode], sha: str) -> str | None:
    """Return the node id whose ``sha256`` equals ``sha``, if any."""
    for node in nodes:
        if node.sha256 and node.sha256.lower() == sha.lower():
            return node.id
    return None


def _reachable_subgraph(nodes: list[TraceNode], focus_id: str) -> set[str]:
    """Walk parents + children of ``focus_id`` collecting every reachable id."""
    by_id = {n.id: n for n in nodes}
    seen: set[str] = set()
    stack: list[str] = [focus_id]
    while stack:
        nid = stack.pop()
        if nid in seen or nid not in by_id:
            continue
        seen.add(nid)
        node = by_id[nid]
        for parent in node.parents:
            if parent not in seen:
                stack.append(parent)
        for child in node.children:
            if child not in seen:
                stack.append(child)
    return seen


def _detect_cycle(nodes: list[TraceNode]) -> None:
    """Raise :class:`TraceUsageError` if the subgraph has any cycle."""
    by_id = {n.id: n for n in nodes}
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {n.id: WHITE for n in nodes}

    def dfs(start: str) -> None:
        stack: list[tuple[str, int]] = [(start, 0)]
        path: list[str] = []
        while stack:
            nid, idx = stack[-1]
            if idx == 0:
                color[nid] = GRAY
                path.append(nid)
            node = by_id[nid]
            children = node.children
            if idx < len(children):
                stack[-1] = (nid, idx + 1)
                child = children[idx]
                c = color.get(child, WHITE)
                if c == GRAY:
                    cycle = " -> ".join(path[path.index(child):] + [child])
                    raise TraceUsageError(
                        f"cycle detected in lineage graph: {cycle}"
                    )
                if c == WHITE:
                    stack.append((child, 0))
            else:
                color[nid] = BLACK
                path.pop()
                stack.pop()

    for n in nodes:
        if color[n.id] == WHITE:
            dfs(n.id)


# ---------------------------------------------------------------------------
# Rendering.
# ---------------------------------------------------------------------------
def _short(value: str, width: int = 12) -> str:
    """Compact id for table cells: ``"<short suffix>"``."""
    if not value:
        return "?"
    if len(value) <= width:
        return value
    return "\u2026" + value[-width:]


def _node_role_label(node: TraceNode) -> str:
    """Compose ``[ROLE]`` affix: ROOT, LEAF, both, or empty."""
    parts: list[str] = []
    if not node.parents:
        parts.append("ROOT")
    if not node.children:
        parts.append("LEAF")
    return " ".join(f"[{p}]" for p in parts)


def _ascii_row(node: TraceNode, prefix: str, is_last: bool) -> str:
    branch_glyph = "`-- " if is_last else "+-- "
    indent = prefix + branch_glyph
    role = _node_role_label(node)
    role_cell = f" {role}" if role else ""
    sha_cell = ""
    if node.sha256:
        sha_cell = f" sha={node.sha256[:8]}"
    return f"{indent}{node.label}{sha_cell}{role_cell}"


def _render_ascii(result: TraceResult) -> str:
    """Render the DAG as a stable-width ASCII tree."""
    by_id = {n.id: n for n in result.nodes}
    lines: list[str] = []

    header = result.header
    title = header.get("title") if isinstance(header, dict) else None
    title_suffix = f" ({title!r})" if title else ""
    state = header.get("state") if isinstance(header, dict) else None
    lines.append(f"production {result.prod_dir.name}{title_suffix}")
    if state:
        lines.append(f"state: {state}")
    lines.append(f"nodes: {len(result.nodes)}")

    if not result.nodes:
        lines.append("(no lineage nodes recorded)")
        return "\n".join(lines)

    lines.append("")
    rows = _render_subtree(by_id, result.roots)
    lines.extend(rows)
    if result.notices:
        lines.append("")
        for notice in result.notices:
            lines.append(f"notice: {notice}")
    return "\n".join(lines)


def _render_subtree(
    by_id: dict[str, TraceNode],
    roots: list[str],
) -> list[str]:
    """Pre-order tree walk emitting ``"+-- "``/``"|   "`` rows."""
    rows: list[str] = []
    seen: set[str] = set()

    def walk(node_id: str, prefix: str, is_last: bool) -> None:
        if node_id in seen:
            return
        seen.add(node_id)
        node = by_id[node_id]
        rows.append(_ascii_row(node, prefix, is_last))
        children = [c for c in node.children if c in by_id]
        child_prefix = prefix + ("    " if is_last else "|   ")
        for i, child_id in enumerate(children):
            walk(child_id, child_prefix, i == len(children) - 1)

    for i, rid in enumerate(roots):
        if rid not in by_id:
            continue
        if i > 0:
            rows.append("")
        walk(rid, "", True)
    return rows


def _render_mermaid(result: TraceResult) -> str:
    """Render the DAG as a Mermaid ``flowchart TD`` document."""
    lines: list[str] = ["flowchart TD"]
    by_id = {n.id: n for n in result.nodes}

    def _mid(node_id: str) -> str:
        return re.sub(r"[^A-Za-z0-9_]", "_", node_id)

    def _label(node: TraceNode) -> str:
        sha_part = f" sha={node.sha256[:8]}" if node.sha256 else ""
        return f"{node.kind}: {node.label}{sha_part}"

    for node in result.nodes:
        lines.append(f"  {_mid(node.id)}[\"{_label(node)}\"]")
    for node in result.nodes:
        for child in node.children:
            if child not in by_id:
                continue
            lines.append(f"  {_mid(node.id)} --> {_mid(child)}")
    return "\n".join(lines)


def render_trace(
    result: TraceResult,
    fmt: str = "ascii",
) -> str:
    """Public render entry point. ``fmt`` is ``"ascii"`` or ``"mermaid"``."""
    if fmt == "mermaid":
        return _render_mermaid(result)
    if fmt == "ascii":
        return _render_ascii(result)
    raise TraceUsageError(f"unknown render format {fmt!r}")


# ---------------------------------------------------------------------------
# CLI entry point.
# ---------------------------------------------------------------------------
def _ensure_utf8_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


def main(argv: list[str] | None = None) -> int:
    """Parse argv, render the lineage DAG, and return a POSIX exit code."""
    parser = argparse.ArgumentParser(
        prog="production trace",
        description=(
            "Trace an asset or production lineage. Walks audit.jsonl + "
            "production.json to render a derivation graph of assets, "
            "generations, snapshots, branches, and merges."
        ),
    )
    parser.add_argument(
        "target",
        help=(
            "Target to trace. Either a production id (prod_<12 hex>), a "
            "path to a production directory, or a 64-char sha256 of an "
            "asset."
        ),
    )
    parser.add_argument(
        "--mermaid",
        action="store_true",
        help="Emit a Mermaid flowchart instead of the ASCII tree.",
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
        prod_dir, sha = resolve_target(args.target, project_root=args.project_root)
    except ProductionNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except TraceUsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        result = build_dag(prod_dir, target_sha=sha)
    except TraceUsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(render_trace(result, fmt="mermaid" if args.mermaid else "ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

