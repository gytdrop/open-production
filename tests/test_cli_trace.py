"""Tests for ``src.cli.trace`` — the asset / production lineage DAG renderer.

Covers the target resolver, the DAG builder (with assets, refs, generations,
snapshots, branches, and merges), the ASCII / Mermaid renderers, the cycle
detector, and the ``python -m src.cli.trace`` entry point itself via
subprocess. Goal: lock in the user-visible behavior so asset lineage stays
a first-class deliverable alongside ``production timeline``.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from src.cli._production_dir import ProductionNotFoundError
from src.cli.trace import (
    SHA256_RE,
    TraceNode,
    TraceUsageError,
    build_dag,
    main,
    render_trace,
    resolve_target,
)


# ---------------------------------------------------------------------------
# Test fixtures.
# ---------------------------------------------------------------------------
REAL_SHA = "4470eb15f4b5c9dc18f15817af21260530b364567faaa0b9fac98a45b1aa23d6"
ALT_SHA = "deadbeef" + "0" * 56  # 64 chars


def _write_production(
    prod_dir: Path,
    *,
    production_id: str,
    title: str = "Fixture",
    references: list[dict] | None = None,
    snapshots: list[dict] | None = None,
    branches: list[dict] | None = None,
    scenes: list[dict] | None = None,
    audit_entries: list[dict] | None = None,
) -> Path:
    """Write a self-contained production.json + audit.jsonl pair under prod_dir."""
    prod_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "production_id": production_id,
        "state": "PUBLISHED",
        "title": title,
        # `load_production_header` looks for `metadata.title` or
        # `audit_trail[0].payload.title`. Mirror that so the title
        # survives into the header dict.
        "metadata": {"title": title},
        "audit_trail": (
            [{"action_type": "system",
              "payload": {"operation": "init", "title": title}}]
            + (audit_entries or [])
        ),
        "references": references or [],
        "snapshots": snapshots or [],
        "branches": branches or [],
        "scenes": scenes or [],
    }
    (prod_dir / "production.json").write_text(json.dumps(state), encoding="utf-8")
    if audit_entries:
        (prod_dir / "audit.jsonl").write_text(
            "\n".join(json.dumps(e) for e in audit_entries) + "\n", encoding="utf-8"
        )
    else:
        (prod_dir / "audit.jsonl").write_text("", encoding="utf-8")
    return prod_dir


@pytest.fixture()
def prod_with_real_sha(tmp_path: Path) -> Path:
    """Synthetic production that owns the snapshot content_hash from the real fixture."""
    return _write_production(
        tmp_path / "prod_fixturesha",
        production_id="prod_fixturesha",
        title="Asset Holder",
        snapshots=[
            {
                "id": "snap_hold001",
                "branch_id": None,
                "label": "trunk",
                "content_hash": REAL_SHA,
                "taken_at": "2026-07-29T00:00:00+00:00",
                "taken_by": "test",
            }
        ],
    )


@pytest.fixture()
def prod_with_merge(tmp_path: Path) -> Path:
    """Production with two branches, snapshots, and a merge audit event."""
    branches = [
        {"id": "branch_a01", "name": "trunk", "created_at": "2026-07-29T00:00:00+00:00",
         "created_by": "user", "locked": False},
        {"id": "branch_b02", "name": "alt", "created_at": "2026-07-29T00:00:05+00:00",
         "created_by": "user", "locked": True},
    ]
    snapshots = [
        {"id": "snap_root001", "branch_id": "branch_a01",
         "content_hash": REAL_SHA, "label": "tip"},
        {"id": "snap_alt002", "branch_id": "branch_b02",
         "content_hash": ALT_SHA, "label": "alt-tip"},
    ]
    audit = [
        {
            "id": "evt_merge_001",
            "ts": "2026-07-29T00:00:10+00:00",
            "actor": "user",
            "action_type": "merge",
            "gate_name": None,
            "claim_id": None,
            "decision_status": None,
            "reason": "merge alt into trunk",
            "evidence": {},
            "payload": {
                "operation": "merge",
                "source_branch_id": "branch_b02",
                "source_branch_name": "alt",
                "label": "merge/alt",
            },
            "state_before": None,
            "state_after": None,
        },
    ]
    return _write_production(
        tmp_path / "prod_merge",
        production_id="prod_merge",
        title="Merge Test",
        branches=branches,
        snapshots=snapshots,
        audit_entries=audit,
    )


@pytest.fixture()
def prod_with_generation(tmp_path: Path) -> Path:
    """Production with one GenerationResult.output_sha256 (8-char short)."""
    return _write_production(
        tmp_path / "prod_gen",
        production_id="prod_gen",
        title="Generation Test",
        scenes=[
            {
                "id": "scene_test",
                "name": "Scene 1",
                "shots": [
                    {
                        "id": "shot_test_01",
                        "intent": "test",
                        "duration_sec": 4.0,
                        "generation": {
                            "output_sha256": ALT_SHA,
                            "input_sha256s": [REAL_SHA],
                        },
                    }
                ],
            }
        ],
    )


@pytest.fixture()
def prod_with_cycle(tmp_path: Path) -> Path:
    """A production whose audit + state produces a cyclic DAG.

    `build_dag` constructs edges from structured state; the only edge
    that flows backward through the kernel is `merge <- source_branch`
    (merge derives from a source branch). We force a cycle by hand-crafting
    two merges whose `source_branch_id` is the other merge\'s target
    branch, which combined with the production -> branch edges forms the
    loop `branch_x -> merge_y -> branch_y -> merge_x -> branch_x`.
    """
    return _write_production(
        tmp_path / "prod_cycle",
        production_id="prod_cycle",
        title="Cycle Test",
        branches=[
            {"id": "branch_x", "name": "x", "locked": False},
            {"id": "branch_y", "name": "y", "locked": False},
        ],
        audit_entries=[
            {
                "id": "evt_merge_x",
                "ts": "2026-07-29T00:00:00+00:00",
                "actor": "user",
                "action_type": "merge",
                "gate_name": None,
                "claim_id": None,
                "decision_status": None,
                "reason": "merge branch_y into branch_x",
                "evidence": {},
                "payload": {
                    "operation": "merge",
                    "source_branch_id": "branch_y",
                    "source_branch_name": "y",
                    "label": "merge/x",
                },
                "state_before": None,
                "state_after": None,
            },
            {
                "id": "evt_merge_y",
                "ts": "2026-07-29T00:00:01+00:00",
                "actor": "user",
                "action_type": "merge",
                "gate_name": None,
                "claim_id": None,
                "decision_status": None,
                "reason": "merge branch_x into branch_y",
                "evidence": {},
                "payload": {
                    "operation": "merge",
                    "source_branch_id": "branch_x",
                    "source_branch_name": "x",
                    "label": "merge/y",
                },
                "state_before": None,
                "state_after": None,
            },
        ],
    )


# ---------------------------------------------------------------------------
# SHA validation
# ---------------------------------------------------------------------------
class TestSha256Validation:
    def test_regex_accepts_64_lowercase_hex(self) -> None:
        assert SHA256_RE.match(REAL_SHA)
        assert SHA256_RE.match("a" * 64)
        assert SHA256_RE.match("0" * 64)
        assert SHA256_RE.match("0123456789abcdef" * 4)

    @pytest.mark.parametrize("bad", ["", "abc", "ABCDEF" + "0" * 58, "Z" * 64])
    def test_regex_rejects_malformed(self, bad: str) -> None:
        assert not SHA256_RE.match(bad)


# ---------------------------------------------------------------------------
# Target resolution
# ---------------------------------------------------------------------------
class TestResolveTarget:
    def test_resolves_explicit_path(self, tmp_path: Path) -> None:
        d = tmp_path / "prod_path"
        _write_production(d, production_id="prod_path")
        prod_dir, sha = resolve_target(str(d), project_root=tmp_path)
        assert prod_dir.resolve() == d.resolve()
        assert sha is None

    def test_resolves_production_id_from_storage_root(self, tmp_path: Path) -> None:
        public = tmp_path / "output" / "public-demo"
        target = _write_production(
            public / "prod_idxx", production_id="prod_idxx"
        )
        prod_dir, sha = resolve_target("prod_idxx", project_root=tmp_path)
        assert prod_dir == target.resolve()
        assert sha is None

    def test_resolves_sha_to_production_with_match(self, prod_with_real_sha: Path) -> None:
        # The fixture sits directly under tmp_path; iter_production_dirs
        # picks up productions rooted at the supplied project_root as well as
        # any `output/public-demo`/`output/productions` subdirs.
        prod_dir, sha = resolve_target(
            REAL_SHA, project_root=prod_with_real_sha.parent
        )
        assert prod_dir == prod_with_real_sha.resolve()
        assert sha == REAL_SHA

    def test_sha_not_found_raises(self, tmp_path: Path) -> None:
        # A production with no matching hash.
        _write_production(tmp_path / "prod_empty", production_id="prod_empty")
        with pytest.raises(ProductionNotFoundError):
            resolve_target(
                "f" * 64, project_root=tmp_path / "prod_empty"
            )

    @pytest.mark.parametrize("bad", ["not-a-hash", "ABCD" + "0" * 60, "abc"])
    def test_malformed_sha_raises_clean_error(self, bad: str, tmp_path: Path) -> None:
        with pytest.raises(TraceUsageError):
            resolve_target(bad, project_root=tmp_path)


# ---------------------------------------------------------------------------
# DAG building
# ---------------------------------------------------------------------------
class TestBuildDag:
    def test_minimal_production_yields_root_node(self, tmp_path: Path) -> None:
        d = tmp_path / "prod_min"
        _write_production(d, production_id="prod_min", title="Minimal")
        result = build_dag(d)
        kinds = [n.kind for n in result.nodes]
        assert "production" in kinds
        assert result.roots == ["production:prod_min"]
        assert any("prod_min" in n.label for n in result.nodes)

    def test_references_appear_as_ref_or_asset(self, tmp_path: Path) -> None:
        d = tmp_path / "prod_ref"
        _write_production(
            d,
            production_id="prod_ref",
            references=[
                {"id": "ref_aaaa1111", "kind": "image", "label": "thumb",
                 "sha256": None},
                {"id": "ref_bbbb2222", "kind": "image", "label": "frame",
                 "sha256": REAL_SHA},
            ],
        )
        result = build_dag(d)
        kinds = sorted({n.kind for n in result.nodes})
        assert "ref" in kinds
        assert "asset" in kinds
        asset_node = next(n for n in result.nodes if n.kind == "asset")
        assert asset_node.sha256 == REAL_SHA

    def test_branches_and_snapshots_are_linked(self, tmp_path: Path) -> None:
        d = tmp_path / "prod_bs"
        _write_production(
            d,
            production_id="prod_bs",
            branches=[{"id": "branch_z9", "name": "z", "locked": False}],
            snapshots=[{
                "id": "snap_z9_001",
                "branch_id": "branch_z9",
                "content_hash": REAL_SHA,
            }],
        )
        result = build_dag(d)
        branch_node = next(n for n in result.nodes if n.kind == "branch")
        snap_node = next(n for n in result.nodes if n.kind == "snapshot")
        assert snap_node.id in branch_node.children
        assert branch_node.id in snap_node.parents
        assert snap_node.sha256 == REAL_SHA

    def test_merges_appear_with_source_branch_as_parent(self, prod_with_merge: Path) -> None:
        result = build_dag(prod_with_merge)
        merge_nodes = [n for n in result.nodes if n.kind == "merge"]
        branch_b = next(
            n for n in result.nodes if n.id == "branch:branch_b02"
        )
        assert len(merge_nodes) == 1
        assert merge_nodes[0].id in branch_b.children

    def test_generations_carry_output_sha(self, prod_with_generation: Path) -> None:
        result = build_dag(prod_with_generation)
        gens = [n for n in result.nodes if n.kind == "generation"]
        assert len(gens) == 1
        assert gens[0].sha256 == ALT_SHA
        # input_sha referenced via asset node
        assets = [n for n in result.nodes if n.kind == "asset"]
        assert any(a.sha256 == REAL_SHA for a in assets)
        assert gens[0].id in [
            c
            for a in assets
            if a.sha256 == REAL_SHA
            for c in a.children
        ]

    def test_target_sha_prunes_to_focus_subgraph(
        self, prod_with_real_sha: Path
    ) -> None:
        result = build_dag(prod_with_real_sha, target_sha=REAL_SHA)
        # The focused node must be present, and the kept set must form a
        # connected subgraph (the snapshot + its ancestors).
        ids = {n.id for n in result.nodes}
        assert "snapshot:snap_hold001" in ids
        # The reachable subgraph from the snapshot includes its parents
        # (here just the production root).
        assert "production:prod_fixturesha" in ids

    def test_target_sha_not_in_graph_keeps_everything_with_notice(
        self, prod_with_real_sha: Path
    ) -> None:
        result = build_dag(prod_with_real_sha, target_sha="f" * 64)
        assert any("not found" in n for n in result.notices)
        # Production root is still rendered.
        assert result.roots == ["production:prod_fixturesha"]

    def test_cycle_raises_usage_error(self) -> None:
        from src.cli.trace import _detect_cycle
        a = TraceNode(id="A", kind="branch", label="A")
        b = TraceNode(id="B", kind="branch", label="B")
        a.children.append("B")
        b.children.append("A")
        with pytest.raises(TraceUsageError, match="cycle detected"):
            _detect_cycle([a, b])

    def test_build_dag_does_not_cycle_on_realistic_state(self, prod_with_merge: Path) -> None:
        # Sanity: a normal merge fixture does not trip the cycle detector.
        result = build_dag(prod_with_merge)
        # Confirm the merge + branches exist and the graph is acyclic by
        # inspecting parent/child degrees on those nodes.
        branch_b = next(n for n in result.nodes if n.id == "branch:branch_b02")
        merges = [n for n in result.nodes if n.kind == "merge"]
        assert all(branch_b.id in m.parents or m.id in branch_b.children for m in merges)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
class TestRenderTrace:
    def test_ascii_renders_root_and_leaves(self, tmp_path: Path) -> None:
        d = tmp_path / "prod_render"
        _write_production(
            d,
            production_id="prod_render",
            title="Render",
            references=[{
                "id": "ref_render01", "kind": "image", "label": "x",
                "sha256": None,
            }],
        )
        result = build_dag(d)
        text = render_trace(result, fmt="ascii")
        assert "prod_render" in text
        assert "[ROOT]" in text  # production node
        assert "[LEAF]" in text  # the lone ref
        # ASCII tree glyphs.
        assert "+--" in text or "`--" in text

    def test_ascii_truncates_sha_to_8(self, tmp_path: Path) -> None:
        d = tmp_path / "prod_sha_short"
        _write_production(
            d,
            production_id="prod_sha_short",
            snapshots=[{
                "id": "snap_sha", "branch_id": None,
                "content_hash": REAL_SHA,
            }],
        )
        result = build_dag(d)
        text = render_trace(result, fmt="ascii")
        assert REAL_SHA[:8] in text
        # Full 64-char hash should NOT appear in the ASCII output.
        assert REAL_SHA not in text

    def test_mermaid_starts_with_flowchart_and_has_edges(
        self, prod_with_real_sha: Path
    ) -> None:
        result = build_dag(prod_with_real_sha)
        text = render_trace(result, fmt="mermaid")
        assert text.startswith("flowchart TD") or text.startswith("graph TD")
        # At least one derivation edge.
        assert "-->" in text

    def test_mermaid_emits_one_node_per_dag_node(
        self, prod_with_merge: Path
    ) -> None:
        result = build_dag(prod_with_merge)
        text = render_trace(result, fmt="mermaid")
        lines = text.splitlines()
        # First line is the diagram type.
        assert lines[0] in ("flowchart TD", "graph TD")
        # Each subsequent line is either ``node["label"]`` or ``A --> B``.
        node_lines = [
            ln for ln in lines[1:] if ln.strip().startswith('node_')
            or re.match(r"\s+[A-Za-z0-9_]+\[", ln)
        ]
        edge_lines = [ln for ln in lines[1:] if "-->" in ln]
        assert len(node_lines) >= len(result.nodes)
        assert len(edge_lines) >= 1


# ---------------------------------------------------------------------------
# main() and the python -m entry point
# ---------------------------------------------------------------------------
class TestMain:
    def test_main_production_id(self, tmp_path: Path, capsys) -> None:
        d = tmp_path / "prod_main"
        _write_production(d, production_id="prod_main", title="Main Test")
        rc = main([str(d)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "prod_main" in out
        assert "Main Test" in out

    def test_main_with_real_fixture(
        self, capsys, repo_root: Path
    ) -> None:
        rc = main(["prod_9915e6697a12", "--project-root", str(repo_root)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "prod_9915e6697a12" in out
        assert REAL_SHA[:8] in out

    def test_main_with_mermaid(self, tmp_path: Path, capsys) -> None:
        d = tmp_path / "prod_mermaid"
        _write_production(d, production_id="prod_mermaid")
        rc = main([str(d), "--mermaid"])
        assert rc == 0
        out = capsys.readouterr().out
        assert out.startswith("flowchart TD") or out.startswith("graph TD")

    def test_main_missing_production_returns_one(self, capsys) -> None:
        rc = main(["prod_does_not_exist_xyz"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "not found" in err

    def test_main_malformed_sha_returns_one(self, capsys) -> None:
        rc = main(["not-a-hash"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "invalid sha256" in err
        # No Python stack trace should be emitted.
        assert "Traceback" not in err

    @pytest.mark.parametrize(
        "bad", ["short", "Z" * 64, "0123456789ABCDEF" * 4, "not_a_sha256"]
    )
    def test_main_various_malformed_sha_clean_error(
        self, bad: str, capsys
    ) -> None:
        rc = main([bad])
        assert rc == 1
        err = capsys.readouterr().err
        assert "Traceback" not in err
        assert "invalid sha256" in err

    def test_main_cycle_returns_two(self, tmp_path: Path, capsys) -> None:
        """`main` exits with code 2 when the cycle detector raises.

        The kernel never produces cyclic data, so we monkey-patch
        :func:uild_dag to raise `TraceUsageError` and confirm the
        CLI surfaces it on stderr without a stack trace.
        """
        import src.cli.trace as trace_mod

        def _fake_resolve(target, project_root=None):
            return (tmp_path, None)

        def _boom(prod_dir, target_sha=None):
            raise TraceUsageError("cycle detected in lineage graph: A -> B -> A")

        original_resolve = trace_mod.resolve_target
        original_build = trace_mod.build_dag
        trace_mod.resolve_target = _fake_resolve
        trace_mod.build_dag = _boom
        try:
            rc = main(["prod_does_not_matter"])
        finally:
            trace_mod.resolve_target = original_resolve
            trace_mod.build_dag = original_build
        assert rc == 2
        err = capsys.readouterr().err
        assert "cycle detected" in err
        assert "Traceback" not in err

    def test_subprocess_invocation(self, tmp_path: Path) -> None:
        d = tmp_path / "prod_sub"
        _write_production(d, production_id="prod_sub", title="Sub")
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.trace", str(d)],
            capture_output=True,
            text=True,
            cwd=str(Path.cwd()),
        )
        assert result.returncode == 0, result.stderr
        assert "prod_sub" in result.stdout

    def test_subprocess_mermaid_invocation(self, tmp_path: Path) -> None:
        d = tmp_path / "prod_sub_m"
        _write_production(d, production_id="prod_sub_m")
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.trace", str(d), "--mermaid"],
            capture_output=True,
            text=True,
            cwd=str(Path.cwd()),
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.startswith("flowchart TD") or result.stdout.startswith(
            "graph TD"
        )

    def test_subprocess_malformed_hash(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.trace", "not-a-hash"],
            capture_output=True,
            text=True,
            cwd=str(Path.cwd()),
        )
        assert result.returncode == 1
        assert "invalid sha256" in result.stderr
        assert "Traceback" not in result.stderr


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def repo_root() -> Path:
    """Return the absolute path to the Open_Production repository root."""
    return Path(__file__).resolve().parent.parent
