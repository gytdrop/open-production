"""
ProductionService — runtime owner of Production state.

Per ACT-8 §3 (command surface) and §4 (ProductionService interface).
This is the prototype implementation. It is intentionally minimal:
init / load / save / status / log / apply_event / snapshot / branch /
merge / archive.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from src.schema.production_document import (
    AuditEntry,
    IntentDocument,
    Production,
    utc_now_iso,
)
from src.validation.gates import (
    ConsistencyContractGate,
    ConsistencyGate,
    EvidenceGate,
    PublicationGate,
)


class ProductionNotFound(LookupError):
    """Raised when load() cannot find the requested production."""


class StorageError(RuntimeError):
    """Raised on atomic-write failures, schema mismatches, or replay errors."""


def _id(prefix: str) -> str:
    """Generate a new id like 'prod_<12 hex chars>' or 'evt_<12 hex chars>'."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


# Forward-only state transition table (architecture §16).
# IN_REVIEW → IN_PRODUCTION is the one allowed backward step (revision loop).
_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "DRAFT":         {"BRIEFED"},
    "BRIEFED":       {"IN_PRODUCTION"},
    "IN_PRODUCTION": {"IN_REVIEW"},
    "IN_REVIEW":     {"APPROVED", "IN_PRODUCTION"},  # revision loop allowed
    "APPROVED":      {"PUBLISHED"},
    "PUBLISHED":     set(),                          # terminal
}

# Gate requirements per target state (§14 Stage Gates).
# Each entry maps a target state to a list of gate-check callables.
# A callable receives the Production and returns (passed: bool, reason: str).
# ALL gates must pass before the transition is allowed.
_GATE_CHECKS: dict[str, list] = {
    "BRIEFED": [
        # Research gate: at least 3 sources must be recorded in Production.references
        lambda prod: (
            len(prod.references) >= 3,
            f"research_gate: need ≥3 references, have {len(prod.references)}",
        ),
    ],
    "IN_PRODUCTION": [
        # Evidence gate: every reference must have a non-empty URI or SHA-256
        lambda prod: (
            all(r.uri or r.sha256 for r in prod.references) if prod.references else True,
            "evidence_gate: one or more references missing URI and sha256",
        ),
    ],
    "IN_REVIEW": [
        # Shot gate: at least one scene with at least one shot must exist
        lambda prod: (
            any(len(s.shots) > 0 for s in prod.scenes),
            "shot_gate: no shots found — run ShotPlanningAgent before review",
        ),
    ],
    "APPROVED": [
        # Consistency gate: no contradictions in audit trail gate decisions
        lambda prod: _check_consistency_gate(prod),
        # Reviewer gate: all shots must be in an approved or generated status
        lambda prod: _check_shot_review_gate(prod),
    ],
    "PUBLISHED": [
        # Publication gate: metadata must carry doi, authors, date
        lambda prod: _check_publication_gate(prod),
    ],
}


# ---------------------------------------------------------------------------
# Gate helper functions (referenced by _GATE_CHECKS lambdas above)
# ---------------------------------------------------------------------------

def _check_consistency_gate(prod: "Production") -> tuple[bool, str]:
    """No contradictions in gate_decision audit entries (same fact_id, different conclusions)."""
    gate_decisions = [
        e for e in prod.audit_trail if e.action_type == "gate_decision"
    ]
    # Treat each gate_decision's (gate_name, decision_status) as a "claim"
    # and check that the same gate_name never has both "passed" and "blocked" decisions.
    gate_statuses: dict[str, set[str]] = {}
    for e in gate_decisions:
        if e.gate_name:
            gate_statuses.setdefault(e.gate_name, set()).add(e.decision_status or "")
    contradicted = [
        g for g, statuses in gate_statuses.items()
        if "passed" in statuses and "blocked" in statuses
    ]
    if contradicted:
        return (False, f"consistency_gate: contradictory gate results for: {contradicted}")
    return (True, "consistency_gate: no contradictions found")


def _check_shot_review_gate(prod: "Production") -> tuple[bool, str]:
    """All shots must be in 'approved' or 'generated' status."""
    all_shots = [sh for s in prod.scenes for sh in s.shots]
    if not all_shots:
        # No shots yet — the IN_REVIEW → APPROVED path requires prior review of shots.
        # Allow if there are no shots (they may be managed externally).
        return (True, "shot_review_gate: no shots to review")
    not_ready = [
        sh.id for sh in all_shots
        if sh.status not in ("approved", "generated", "in_review")
    ]
    if not_ready:
        return (
            False,
            f"shot_review_gate: {len(not_ready)} shot(s) not yet reviewed: {not_ready[:3]}",
        )
    return (True, "shot_review_gate: all shots reviewed")


def _check_publication_gate(prod: "Production") -> tuple[bool, str]:
    """Metadata must carry doi, authors, date (mirrors PublicationGate.check())."""
    gate = PublicationGate()
    ok, reason = gate.check(prod.metadata)
    if not ok:
        return (False, f"publication_gate: {reason}")
    return (True, "publication_gate: metadata complete")


def _safe_replace(src: str, dst: str, *, attempts: int = 5, base_delay: float = 0.01) -> None:
    """os.replace() with retry. Windows transiently returns [WinError 5] when

    the destination is briefly held by another process (antivirus, file
    indexer, or another in-flight write that escaped the per-instance lock).
    """
    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            os.replace(src, dst)
            return
        except PermissionError as exc:
            last_exc = exc
            time.sleep(base_delay * (attempt + 1))
    # Final attempt: surface the last error if all retries failed.
    assert last_exc is not None
    raise last_exc


@dataclass
class ProductionService:
    """Filesystem-backed Production state owner.

    Storage layout (per ACT-8 §5):
        <storage_dir>/<production_id>/production.json
        <storage_dir>/<production_id>/audit.jsonl
        <storage_dir>/<production_id>/snapshots/snap_<sha>.json

    The current Production is reconstructed by:
        1. Read production.json (latest known state)
        2. Replay audit.jsonl entries that haven't been applied yet

    For the prototype we just read production.json; the journal is
    append-only and read by `log()`.
    """

    storage_dir: Path

    def __post_init__(self) -> None:
        self.storage_dir = Path(self.storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        # Per-instance re-entrant lock. Guards save() against concurrent writes from
        # the same Python process (e.g. a double-click on Finalize, or two browser
        # tabs sharing one ProcessService). Cross-process safety still requires an
        # OS-level lock; see TODO in the README.
        self._lock = threading.RLock()

    def transaction(self):
        """Context manager for atomic load-modify-save transactions.

        Wrap any sequence that needs to observe a stable state and write a
        derived update so concurrent threads cannot interleave their reads
        and writes. Use this whenever you would otherwise write
        load(); modify(); save(); outside the lock.

        Example:
            with svc.transaction():
                p = svc.load(prod_id)
                p2 = replace(p, audit_trail=p.audit_trail + [new_entry])
                svc.save(p2)
        """
        return self._lock

    # ---------- paths ----------
    def _prod_dir(self, production_id: str) -> Path:
        return self.storage_dir / production_id

    def _state_path(self, production_id: str) -> Path:
        return self._prod_dir(production_id) / "production.json"

    def _sidecar_path(self, production_id: str) -> Path:
        return self._prod_dir(production_id) / "production.json.sha256"

    def _journal_path(self, production_id: str) -> Path:
        return self._prod_dir(production_id) / "audit.jsonl"

    # ---------- init ----------
    def init(
        self,
        name: str,
        *,
        studio_id: Optional[str] = None,
        intent: Optional[IntentDocument] = None,
    ) -> Production:
        """Create a new Production in DRAFT state. Atomic write of state file."""
        production_id = _id("prod")
        prod = Production(
            id=production_id,
            state="DRAFT",
            title=name[:200] if name else None,
            intent=intent or IntentDocument(topic=name or "Untitled"),
            scenes=[],
            audit_trail=[],
            studio_id=studio_id,
        )
        prod_dir = self._prod_dir(production_id)
        try:
            prod_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            raise StorageError(
                f"production_id collision on {production_id}"
            ) from exc
        # Emit the init event into the journal BEFORE writing state
        init_entry = AuditEntry(
            id=_id("evt"),
            ts=utc_now_iso(),
            actor="system",
            action_type="system",
            payload={"operation": "init", "title": name},
            state_after=self._content_hash(prod),
        )
        prod = self.apply_event(prod, init_entry)
        self._write_state(prod)
        self._append_journal(prod_dir, init_entry)
        return prod

    # ---------- load / save ----------
    def load(self, production_id: str) -> Production:
        """Reconstruct Production from disk. Raises ProductionNotFound on miss.

        If a production.json.sha256 sidecar is present, the SHA-256 of the
        raw file bytes is verified against it before parsing.  A mismatch
        raises StorageError (tampered or corrupted file).  The absence of a
        sidecar is silently accepted for backward compatibility.

        Held under the same per-instance lock as save() so the read sees a
        consistent pre-write or post-write state, never a half-written one.
        """
        with self._lock:
            state_path = self._state_path(production_id)
            if not state_path.exists():
                raise ProductionNotFound(production_id)
            raw = state_path.read_bytes()
        sidecar = self._sidecar_path(production_id)
        if sidecar.exists():
            expected = sidecar.read_text(encoding="utf-8").strip()
            actual = hashlib.sha256(raw).hexdigest()
            if actual != expected:
                raise StorageError(
                    f"content-hash mismatch for {production_id}: "
                    f"expected {expected}, got {actual}"
                )
        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise StorageError(
                f"corrupt production.json for {production_id}"
            ) from exc
        return _dict_to_production(data)

    def save(self, prod: Production) -> Production:
        """Persist Production state. State file is atomic; journal is append-only.

        A per-instance re-entrant lock guards against concurrent saves from the same
        Python process (double-click on Finalize, two browser tabs sharing one
        service). Cross-process contention is not addressed here; see README for
        "Concurrency limits".
        """
        with self._lock:
            prod_dir = self._prod_dir(prod.id)
            prod_dir.mkdir(parents=True, exist_ok=True)
            # Determine new entries to journal (everything past what was already journaled)
            already_journaled = self._count_journaled(prod_dir)
            new_entries = prod.audit_trail[already_journaled:]
            self._write_state(prod)
            for entry in new_entries:
                self._append_journal(prod_dir, entry)
            return prod

    # ---------- status / log ----------
    def status(self, production_id: str) -> dict:
        """Return the full Production as a JSON-serializable dict."""
        prod = self.load(production_id)
        return _production_to_dict(prod)

    def log(
        self,
        production_id: str,
        *,
        since: Optional[str] = None,
        action_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Tail the audit journal with optional filters."""
        journal_path = self._journal_path(production_id)
        if not journal_path.exists():
            raise ProductionNotFound(production_id)
        out: list[dict] = []
        for line in journal_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            if since and entry.get("ts", "") < since:
                continue
            if action_type and entry.get("action_type") != action_type:
                continue
            out.append(entry)
            if len(out) >= limit:
                break
        return out

    def list_productions(self) -> list[dict]:
        """Enumerate all productions on disk. Summary form (id + title + state)."""
        out: list[dict] = []
        if not self.storage_dir.exists():
            return out
        for child in self.storage_dir.iterdir():
            if not child.is_dir():
                continue
            state_file = child / "production.json"
            if not state_file.exists():
                continue
            try:
                data = json.loads(state_file.read_text(encoding="utf-8"))
                out.append(
                    {
                        "id": data.get("id"),
                        "title": data.get("title"),
                        "state": data.get("state"),
                        "updated_at": data.get("updated_at"),
                    }
                )
            except (json.JSONDecodeError, KeyError):
                continue
        return sorted(out, key=lambda p: p.get("updated_at") or "", reverse=True)

    # ---------- create_branch ----------
    def create_branch(self, prod: Production, label: str) -> Production:
        """Create a new named branch on the production. Pure: returns new Production.

        Emits a 'system' AuditEntry and appends a Branch record.
        Does NOT mutate the input Production.
        """
        from src.schema.production_document import Branch
        branch_id = _id("branch")
        now = utc_now_iso()
        new_branch = Branch(
            id=branch_id,
            name=label,
            created_at=now,
            created_by="user",
        )
        branch_entry = AuditEntry(
            id=_id("evt"),
            ts=now,
            actor="user",
            action_type="system",
            payload={"operation": "create_branch", "branch_id": branch_id, "label": label},
            state_after=branch_id,
        )
        new_prod = replace(
            prod,
            branches=list(prod.branches) + [new_branch],
            audit_trail=tuple(prod.audit_trail) + (branch_entry,),
            updated_at=now,
        )
        return new_prod

    # ---------- snapshot ----------
    def snapshot(self, prod: Production, *, label: str = "", taken_by: str = "user") -> Production:
        """Create a named, content-addressed VersionSnapshot and return a new Production.

        Pure: never mutates the input Production.
        """
        from src.schema.production_document import VersionSnapshot
        snap_id = _id("snap")
        now = utc_now_iso()
        content_hash = hashlib.sha256(
            json.dumps(_production_to_dict(prod), sort_keys=True).encode()
        ).hexdigest()
        snap = VersionSnapshot(
            id=snap_id,
            taken_at=now,
            content_hash=content_hash,
            taken_by=taken_by,
            label=label or f"snapshot-{now[:10]}",
            branch_id=prod.branches[-1].id if prod.branches else None,
        )
        snap_entry = AuditEntry(
            id=_id("evt"),
            ts=now,
            actor=taken_by,
            action_type="snapshot",
            payload={"snap_id": snap_id, "label": label, "content_hash": content_hash},
            state_after=content_hash[:16],
        )
        return replace(
            prod,
            snapshots=list(prod.snapshots) + [snap],
            audit_trail=tuple(prod.audit_trail) + (snap_entry,),
            updated_at=now,
        )

    # ---------- merge ----------

    def merge(
        self,
        prod: Production,
        source_branch_id: str,
        *,
        actor: str = "user",
        label: str = "",
    ) -> Production:
        """Merge a named branch back into the production trunk.

        Strategy: fast-forward only (prototype scope).  The source branch's
        snapshot — the most recent VersionSnapshot whose branch_id matches
        source_branch_id — is adopted as the new trunk state, the source
        branch is marked locked=True, and a 'merge' AuditEntry is appended.

        Pure: never mutates the input Production.

        Raises:
            StorageError: if source_branch_id does not exist on this production,
                          or if no snapshot exists for that branch.
        """
        from src.schema.production_document import Branch

        # Locate the branch object.
        matching_branches = [b for b in prod.branches if b.id == source_branch_id]
        if not matching_branches:
            raise StorageError(
                f"branch {source_branch_id!r} not found on production {prod.id!r}"
            )
        source_branch = matching_branches[0]

        # Find the latest snapshot that belongs to this branch.
        branch_snaps = [s for s in prod.snapshots if s.branch_id == source_branch_id]
        if not branch_snaps:
            raise StorageError(
                f"no snapshots found for branch {source_branch_id!r}; "
                "take a snapshot before merging"
            )
        tip_snap = branch_snaps[-1]

        now = utc_now_iso()
        merge_entry = AuditEntry(
            id=_id("evt"),
            ts=now,
            actor=actor,
            action_type="merge",
            payload={
                "operation": "merge",
                "source_branch_id": source_branch_id,
                "source_branch_name": source_branch.name,
                "tip_snapshot_id": tip_snap.id,
                "tip_content_hash": tip_snap.content_hash,
                "label": label or f"merge/{source_branch.name}",
            },
            state_before=self._content_hash(prod),
            state_after=tip_snap.content_hash[:16],
        )

        # Lock the source branch so it cannot be merged again.
        updated_branches = [
            replace(b, locked=True) if b.id == source_branch_id else b
            for b in prod.branches
        ]

        return replace(
            prod,
            branches=updated_branches,
            audit_trail=tuple(prod.audit_trail) + (merge_entry,),
            updated_at=now,
        )

    # ---------- branch_compare ----------

    def branch_compare(
        self,
        prod: Production,
        branch_a_id: str,
        branch_b_id: str,
    ) -> dict:
        """Compare the tip snapshots of two branches and return a structured summary.

        Returns a dict with:
          - branch_a / branch_b: name, id, locked, snapshot_count, tip_snapshot
          - summary: approved_shots_a/b, scene_count_a/b, audit_events_a/b,
                     reviewer_score_a/b (average from GenerationResult.reviewer_verdict),
                     content_hash_a/b
          - divergence: events unique to each branch since their common ancestor

        Pure: does not modify the production.

        Raises:
            StorageError: if either branch_id is not found on the production,
                          or if a branch has no snapshot.
        """
        def _get_branch(bid: str):
            matching = [b for b in prod.branches if b.id == bid]
            if not matching:
                raise StorageError(
                    f"branch {bid!r} not found on production {prod.id!r}"
                )
            return matching[0]

        def _tip_snap(bid: str):
            snaps = [s for s in prod.snapshots if s.branch_id == bid]
            if not snaps:
                raise StorageError(
                    f"no snapshots found for branch {bid!r}; "
                    "take a snapshot before comparing"
                )
            return snaps[-1]

        def _reviewer_scores(p: Production) -> list[float]:
            scores: list[float] = []
            for scene in p.scenes:
                for shot in scene.shots:
                    if shot.generation and shot.generation.reviewer_verdict:
                        v = shot.generation.reviewer_verdict.get("score")
                        if v is not None:
                            try:
                                scores.append(float(v))
                            except (TypeError, ValueError):
                                pass
            return scores

        def _approved_shot_count(p: Production) -> int:
            return sum(
                1 for scene in p.scenes
                for shot in scene.shots
                if shot.status == "approved"
            )

        branch_a = _get_branch(branch_a_id)
        branch_b = _get_branch(branch_b_id)
        snap_a = _tip_snap(branch_a_id)
        snap_b = _tip_snap(branch_b_id)

        # Count all snapshots per branch.
        snaps_a = [s for s in prod.snapshots if s.branch_id == branch_a_id]
        snaps_b = [s for s in prod.snapshots if s.branch_id == branch_b_id]

        # Audit events per branch (events whose payload references the branch).
        events_a = [
            e for e in prod.audit_trail
            if e.payload.get("branch_id") == branch_a_id
            or e.state_after == branch_a_id
        ]
        events_b = [
            e for e in prod.audit_trail
            if e.payload.get("branch_id") == branch_b_id
            or e.state_after == branch_b_id
        ]

        # Reviewer scores live on the trunk production's shots — snapshots do
        # not carry a full Production instance in this prototype (content-hash
        # only).  We report scores from the live trunk as a common reference,
        # and note divergence via content hash differences.
        scores = _reviewer_scores(prod)
        avg_score = round(sum(scores) / len(scores), 3) if scores else None

        return {
            "branch_a": {
                "id": branch_a.id,
                "name": branch_a.name,
                "locked": branch_a.locked,
                "snapshot_count": len(snaps_a),
                "tip_snapshot": {
                    "id": snap_a.id,
                    "label": snap_a.label,
                    "taken_at": snap_a.taken_at,
                    "content_hash": snap_a.content_hash,
                },
            },
            "branch_b": {
                "id": branch_b.id,
                "name": branch_b.name,
                "locked": branch_b.locked,
                "snapshot_count": len(snaps_b),
                "tip_snapshot": {
                    "id": snap_b.id,
                    "label": snap_b.label,
                    "taken_at": snap_b.taken_at,
                    "content_hash": snap_b.content_hash,
                },
            },
            "summary": {
                "approved_shots": _approved_shot_count(prod),
                "scene_count": len(prod.scenes),
                "reviewer_score_avg": avg_score,
                "content_hash_a": snap_a.content_hash,
                "content_hash_b": snap_b.content_hash,
                "hashes_equal": snap_a.content_hash == snap_b.content_hash,
                "audit_events_a": len(events_a),
                "audit_events_b": len(events_b),
            },
            "divergence": {
                "branch_a_only_events": [e.id for e in events_a],
                "branch_b_only_events": [e.id for e in events_b],
                "snapshot_count_delta": len(snaps_a) - len(snaps_b),
            },
        }

    # ---------- archive ----------

    def archive(
        self,
        prod: Production,
        *,
        actor: str = "user",
        retention_days: int = 2555,  # ~7 years — SMPTE RP 2050 guidance
    ) -> Production:
        """Mark a production as archived and record an archive AuditEntry.

        Retention policy (per ACT-8 §12 / open-production-plan Appendix K.26):
          - Default retention: 7 years (2 555 days) from archive date.
          - The exact expiry date is recorded in the AuditEntry payload as
            ``expires_at`` (ISO 8601).  Storage back-ends should honour it.
          - Archiving requires the production to be in PUBLISHED state.

        Pure: never mutates the input Production.

        Raises:
            StorageError: if the production is not in PUBLISHED state.
        """
        import datetime as _dt

        if prod.state != "PUBLISHED":
            raise StorageError(
                f"archive() requires state=PUBLISHED (got {prod.state!r})"
            )

        now_dt = _dt.datetime.now(_dt.timezone.utc)
        expires_dt = now_dt + _dt.timedelta(days=retention_days)
        now = now_dt.isoformat()
        expires_at = expires_dt.isoformat()

        archive_entry = AuditEntry(
            id=_id("evt"),
            ts=now,
            actor=actor,
            action_type="system",
            payload={
                "operation": "archive",
                "production_id": prod.id,
                "archived_at": now,
                "retention_days": retention_days,
                "expires_at": expires_at,
                "artifacts": ["production.json", "audit.jsonl"],
            },
            state_before=self._content_hash(prod),
            state_after="archived",
        )

        updated_metadata = {**prod.metadata, "archived_at": now, "expires_at": expires_at}

        return replace(
            prod,
            metadata=updated_metadata,
            audit_trail=tuple(prod.audit_trail) + (archive_entry,),
            updated_at=now,
        )

    # ---------- commit_editor_proposal ----------

    def commit_editor_proposal(
        self,
        prod: Production,
        proposal: dict,
        *,
        actor: str = "editor_agent",
    ) -> Production:
        """Assemble a Timeline from a chosen EditorAgent proposal.

        Takes one proposal dict from EditorAgent.run()["proposals"] and
        writes Timeline.scene_order, Timeline.shot_durations,
        Timeline.transitions, and Timeline.total_duration_sec onto the
        production.  Shot.duration_sec is NOT mutated on the dataclass
        objects in-place; the canonical durations live on the Timeline so
        the proposal is non-destructive until a generation step applies it.

        Returns a new Production (pure — input is untouched).
        """
        from src.schema.production_document import Timeline

        scene_id: str = str(proposal.get("scene_id") or "")
        shot_sequence: list[str] = list(proposal.get("shot_sequence") or [])
        durations: list[float] = [float(d) for d in (proposal.get("durations") or [])]
        transitions: list[str] = list(proposal.get("transitions") or [])
        total_duration_sec: float = float(proposal.get("total_duration_sec") or sum(durations))

        # Build shot_durations: one entry per (scene_id, shot_id) pair.
        shot_dur_entries = [
            {"scene_id": scene_id, "shot_id": shot_id, "duration_sec": dur}
            for shot_id, dur in zip(shot_sequence, durations)
        ]

        # Merge with any existing timeline so multi-scene productions accumulate.
        existing = prod.timeline or Timeline()

        # scene_order: replace or append the scene_id entry.
        new_scene_order = [s for s in existing.scene_order if s != scene_id]
        if scene_id:
            new_scene_order.append(scene_id)

        # shot_durations: drop any old entries for this scene then add new ones.
        kept_durations = [e for e in existing.shot_durations if e.get("scene_id") != scene_id]
        new_shot_durations = kept_durations + shot_dur_entries

        # Transitions stored as {scene_id, from_shot, to_shot, type} dicts.
        new_transitions_dicts = [
            {
                "scene_id": scene_id,
                "from_shot": shot_sequence[i],
                "to_shot": shot_sequence[i + 1],
                "type": transitions[i] if i < len(transitions) else "cut",
            }
            for i in range(len(shot_sequence) - 1)
        ]
        kept_transitions = [t for t in existing.transitions if t.get("scene_id") != scene_id]
        new_transitions = kept_transitions + new_transitions_dicts

        # Recompute total across all scenes.
        new_total = sum(e["duration_sec"] for e in new_shot_durations)

        new_timeline = Timeline(
            scene_order=new_scene_order,
            transitions=new_transitions,
            music_cues=list(existing.music_cues),
            shot_durations=new_shot_durations,
            total_duration_sec=round(new_total, 2),
        )

        now = utc_now_iso()
        commit_entry = AuditEntry(
            id=_id("evt"),
            ts=now,
            actor=actor,
            action_type="timeline_assembly",
            payload={
                "scene_id": scene_id,
                "proposal_label": proposal.get("label"),
                "shot_count": len(shot_sequence),
                "total_duration_sec": new_timeline.total_duration_sec,
            },
            state_before=self._content_hash(prod),
        )

        new_prod = replace(
            prod,
            timeline=new_timeline,
            updated_at=now,
            audit_trail=tuple(prod.audit_trail) + (commit_entry,),
        )
        return new_prod

    # ---------- advance_stage ----------

    def advance_stage(
        self,
        prod: Production,
        target_state: str,
        *,
        actor: str = "system",
        gate_overrides: dict | None = None,
    ) -> Production:
        """Advance production to ``target_state``, enforcing all §14 stage gates.

        Every gate in ``_GATE_CHECKS[target_state]`` is evaluated against the
        current production.  If any gate fails the transition is blocked and a
        ``StorageError`` is raised — the Production is never mutated.

        Args:
            prod:           Current production (input is never mutated).
            target_state:   The state to advance to (e.g. ``"BRIEFED"``).
            actor:          Identity recorded in the ``stage_advance`` AuditEntry.
            gate_overrides: Optional mapping of gate-reason substrings to ``True``
                            allowing callers to waive specific gates (e.g. human
                            override workflows).  A waived gate is recorded as
                            ``decision_status="overridden"`` in the audit trail.

        Returns:
            A new Production with updated state and a ``stage_advance`` AuditEntry
            (plus one ``gate_decision`` entry per gate) appended to the audit trail.

        Raises:
            StorageError: if the requested transition is illegal or any gate fails.
        """
        valid_states = set(_ALLOWED_TRANSITIONS.keys()) | {"PUBLISHED"}
        if target_state not in valid_states:
            raise StorageError(
                f"advance_stage: unknown target state {target_state!r}"
            )
        allowed = _ALLOWED_TRANSITIONS.get(prod.state, set())
        if target_state not in allowed:
            raise StorageError(
                f"advance_stage: illegal transition {prod.state!r} → {target_state!r}. "
                f"Allowed: {sorted(allowed) or ['(none — terminal state)']}"
            )

        gate_checks = _GATE_CHECKS.get(target_state, [])
        gate_audit_entries: list[AuditEntry] = []
        failed_reasons: list[str] = []
        overrides = gate_overrides or {}

        for check_fn in gate_checks:
            passed, reason = check_fn(prod)
            gate_name = reason.split(":")[0].strip()
            override_key = next((k for k in overrides if k in reason), None)

            if override_key is not None:
                gate_audit_entries.append(AuditEntry(
                    id=_id("evt"),
                    ts=utc_now_iso(),
                    actor=actor,
                    action_type="gate_decision",
                    gate_name=gate_name,
                    claim_id=f"{prod.id}:{target_state}",
                    decision_status="overridden",
                    reason=f"override by actor={actor}: {reason}",
                ))
            elif not passed:
                failed_reasons.append(reason)
                gate_audit_entries.append(AuditEntry(
                    id=_id("evt"),
                    ts=utc_now_iso(),
                    actor=actor,
                    action_type="gate_decision",
                    gate_name=gate_name,
                    claim_id=f"{prod.id}:{target_state}",
                    decision_status="blocked",
                    reason=reason,
                ))
            else:
                gate_audit_entries.append(AuditEntry(
                    id=_id("evt"),
                    ts=utc_now_iso(),
                    actor=actor,
                    action_type="gate_decision",
                    gate_name=gate_name,
                    claim_id=f"{prod.id}:{target_state}",
                    decision_status="passed",
                    reason=reason,
                ))

        if failed_reasons:
            raise StorageError(
                f"advance_stage: transition {prod.state!r} → {target_state!r} blocked "
                f"by {len(failed_reasons)} gate(s): {failed_reasons}"
            )

        now = utc_now_iso()
        advance_entry = AuditEntry(
            id=_id("evt"),
            ts=now,
            actor=actor,
            action_type="stage_advance",
            payload={
                "from_state": prod.state,
                "to_state": target_state,
                "gates_checked": len(gate_checks),
                "gates_passed": len(gate_checks),
            },
            state_before=prod.state,
            state_after=target_state,
        )

        all_new_entries = tuple(gate_audit_entries) + (advance_entry,)
        return replace(
            prod,
            state=target_state,
            audit_trail=tuple(prod.audit_trail) + all_new_entries,
            updated_at=now,
        )

    # ---------- apply_event ----------

    def apply_event(self, prod: Production, entry: AuditEntry) -> Production:
        """Append an event to the production. Pure: never mutates input.

        Returns a NEW Production. The caller's input is untouched.
        State transitions are validated against the forward-only table
        defined at module level (_ALLOWED_TRANSITIONS).
        """
        # Validate: state_transition events must reference a valid next state
        if entry.action_type == "state_transition":
            next_state = entry.payload.get("next_state") if entry.payload else None
            valid_states = ("DRAFT", "BRIEFED", "IN_PRODUCTION", "IN_REVIEW", "APPROVED", "PUBLISHED")
            if next_state not in valid_states:
                raise StorageError(
                    f"invalid state_transition payload: {entry.payload!r}"
                )
            allowed = _ALLOWED_TRANSITIONS.get(prod.state, set())
            if next_state not in allowed:
                raise StorageError(
                    f"illegal state transition: {prod.state!r} → {next_state!r}. "
                    f"Allowed from {prod.state!r}: {sorted(allowed) or ['(none — terminal state)']}"
                )
            return replace(
                prod,
                audit_trail=tuple(prod.audit_trail) + (entry,),
                state=next_state,
                updated_at=entry.ts,
            )
        # Default: just append
        return replace(
            prod,
            audit_trail=tuple(prod.audit_trail) + (entry,),
            updated_at=entry.ts,
        )

    # ---------- internals ----------
    def _content_hash(self, prod: Production) -> str:
        """Cheap content hash of the production for state_before/state_after."""
        blob = json.dumps(_production_to_dict(prod), sort_keys=True).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()[:16]

    def _write_state(self, prod: Production) -> None:
        """Atomic write of production.json and its SHA-256 sidecar.

        Both files are written via temp-file + rename so that a reader never
        sees a partial state or a stale sidecar.
        """
        path = self._state_path(prod.id)
        sidecar_path = self._sidecar_path(prod.id)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = _production_to_dict(prod)

        # Serialise to bytes once so the hash is computed from the exact bytes
        # that will land on disk.
        payload = json.dumps(data, indent=2, sort_keys=True).encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()

        # Atomic write of the JSON state file.
        fd, tmp_name = tempfile.mkstemp(
            prefix=".production.", suffix=".json.tmp", dir=str(path.parent)
        )
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(payload)
            _safe_replace(tmp_name, path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

        # Atomic write of the sidecar.
        fd2, tmp_sidecar = tempfile.mkstemp(
            prefix=".production.", suffix=".sha256.tmp", dir=str(path.parent)
        )
        try:
            with os.fdopen(fd2, "w", encoding="utf-8") as fh:
                fh.write(digest + "\n")
            _safe_replace(tmp_sidecar, sidecar_path)
        except Exception:
            try:
                os.unlink(tmp_sidecar)
            except OSError:
                pass
            raise

    def _append_journal(self, prod_dir: Path, entry: AuditEntry) -> None:
        journal = prod_dir / "audit.jsonl"
        journal.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(_audit_entry_to_dict(entry)) + "\n"
        with open(journal, "a", encoding="utf-8") as fh:
            fh.write(line)

    def _count_journaled(self, prod_dir: Path) -> int:
        journal = prod_dir / "audit.jsonl"
        if not journal.exists():
            return 0
        n = 0
        with open(journal, "r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    n += 1
        return n


# ============================================================ serialization


def _production_to_dict(prod: Production) -> dict:
    """dataclass → JSON-friendly dict for the state file."""
    return {
        "schema_version": prod.schema_version,
        "id": prod.id,
        "studio_id": prod.studio_id,
        "title": prod.title,
        "state": prod.state,
        "created_at": prod.created_at,
        "updated_at": prod.updated_at,
        "intent": _intent_to_dict(prod.intent),
        "references": [_ref_to_dict(r) for r in prod.references],
        "characters": [_char_to_dict(c) for c in prod.characters],
        "environments": [_env_to_dict(e) for e in prod.environments],
        "style_tokens": [_tok_to_dict(t) for t in prod.style_tokens],
        "brand_kit": _brand_to_dict(prod.brand_kit) if prod.brand_kit else None,
        "scenes": [_scene_to_dict(s) for s in prod.scenes],
        "timeline": _timeline_to_dict(prod.timeline) if prod.timeline else None,
        "branches": [_branch_to_dict(b) for b in prod.branches],
        "snapshots": [_snap_to_dict(s) for s in prod.snapshots],
        "audit_trail": [_audit_entry_to_dict(e) for e in prod.audit_trail],
        "metadata": prod.metadata,
    }


def _intent_to_dict(i: IntentDocument) -> dict:
    return {
        "topic": i.topic,
        "audience": i.audience,
        "tone": i.tone,
        "platform": i.platform,
        "duration_sec": i.duration_sec,
        "style_seed": i.style_seed,
        "extra": i.extra,
    }


def _ref_to_dict(r) -> dict:
    return {
        "id": r.id, "kind": r.kind, "label": r.label,
        "uri": r.uri, "sha256": r.sha256,
        "pinned_by": r.pinned_by, "pinned_at": r.pinned_at,
    }


def _char_to_dict(c) -> dict:
    return {
        "id": c.id, "name": c.name, "role": c.role, "voice_id": c.voice_id,
        "visual_anchors": [_ref_to_dict(r) for r in c.visual_anchors],
        "consistency_contract": _contract_to_dict(c.consistency_contract),
    }


def _env_to_dict(e) -> dict:
    return {
        "id": e.id, "name": e.name,
        "time_of_day_variants": e.time_of_day_variants,
        "visual_anchors": [_ref_to_dict(r) for r in e.visual_anchors],
        "lighting_presets": e.lighting_presets,
        "consistency_contract": _contract_to_dict(e.consistency_contract),
    }


def _contract_to_dict(c) -> Optional[dict]:
    if c is None:
        return None
    return {
        "subject_id": c.subject_id,
        "visual_anchors": [_ref_to_dict(r) for r in c.visual_anchors],
        "required_attributes": c.required_attributes,
        "prohibited_attributes": c.prohibited_attributes,
        "variance_tolerance": c.variance_tolerance,
        "reviewer_checklist": c.reviewer_checklist,
    }


def _tok_to_dict(t) -> dict:
    return {"id": t.id, "name": t.name, "kind": t.kind,
            "value": t.value, "tokens": t.tokens}


def _brand_to_dict(b) -> dict:
    return {
        "name": b.name,
        "palette": [_tok_to_dict(t) for t in b.palette],
        "typography": [_tok_to_dict(t) for t in b.typography],
        "logos": [_ref_to_dict(r) for r in b.logos],
        "approved_language": b.approved_language,
        "prohibited_language": b.prohibited_language,
    }


def _scene_to_dict(s) -> dict:
    return {
        "id": s.id, "name": s.name,
        "mood": _mood_to_dict(s.mood),
        "location": s.location,
        "shots": [_shot_to_dict(sh) for sh in s.shots],
        "notes": s.notes,
        "stage": s.stage,
    }


def _mood_to_dict(m) -> Optional[dict]:
    if m is None:
        return None
    return {
        "emotional_promise": m.emotional_promise,
        "tonal_palette": m.tonal_palette,
        "references": m.references,
        "locked": m.locked,
    }


def _shot_to_dict(sh) -> dict:
    return {
        "id": sh.id, "scene_id": sh.scene_id, "intent": sh.intent,
        "duration_sec": sh.duration_sec,
        "camera": _camera_to_dict(sh.camera),
        "lighting": _lighting_to_dict(sh.lighting),
        "characters": [_char_ref_to_dict(c) for c in sh.characters],
        "audio": _audio_to_dict(sh.audio),
        "generation": _generation_to_dict(sh.generation),
        "status": sh.status, "locked": sh.locked,
        "version_history": [_generation_to_dict(g) for g in sh.version_history],
        "storyboard_frame": getattr(sh, "storyboard_frame", None),
    }


def _camera_to_dict(c) -> Optional[dict]:
    if c is None:
        return None
    return {
        "focal_length_mm": c.focal_length_mm, "frame_rate": c.frame_rate,
        "aperture": c.aperture, "movement": c.movement,
        "framing": c.framing, "preset_id": c.preset_id,
    }


def _lighting_to_dict(l) -> Optional[dict]:
    if l is None:
        return None
    return {
        "key_intensity_pct": l.key_intensity_pct,
        "fill_intensity_pct": l.fill_intensity_pct,
        "color_temp_k": l.color_temp_k,
        "preset_id": l.preset_id,
    }


def _char_ref_to_dict(c) -> dict:
    return {"character_id": c.character_id, "expression": c.expression,
            "blocking_note": c.blocking_note}


def _audio_to_dict(a) -> Optional[dict]:
    if a is None:
        return None
    return {"voice_direction": a.voice_direction, "sfx": a.sfx,
            "music_cue": a.music_cue}


def _generation_to_dict(g) -> Optional[dict]:
    if g is None:
        return None
    return {
        "id": g.id, "produced_at": g.produced_at, "produced_by": g.produced_by,
        "backend": g.backend, "backend_version": g.backend_version,
        "prompt_hash": g.prompt_hash, "output_uri": g.output_uri,
        "output_sha256": g.output_sha256,
        "reviewer_verdict": g.reviewer_verdict,
        "cost_estimate_usd": g.cost_estimate_usd,
        "latency_ms": g.latency_ms,
    }


def _timeline_to_dict(t) -> dict:
    return {
        "scene_order": t.scene_order,
        "transitions": t.transitions,
        "music_cues": t.music_cues,
        "shot_durations": t.shot_durations,
        "total_duration_sec": t.total_duration_sec,
    }


def _branch_to_dict(b) -> dict:
    return {
        "id": b.id, "name": b.name,
        "parent_snapshot_id": b.parent_snapshot_id,
        "created_at": b.created_at, "created_by": b.created_by,
        "locked": b.locked,
    }


def _snap_to_dict(s) -> dict:
    return {
        "id": s.id, "taken_at": s.taken_at, "content_hash": s.content_hash,
        "taken_by": s.taken_by, "label": s.label, "branch_id": s.branch_id,
    }


def _audit_entry_to_dict(e: AuditEntry) -> dict:
    return {
        "id": e.id, "ts": e.ts, "actor": e.actor,
        "action_type": e.action_type,
        "gate_name": e.gate_name, "claim_id": e.claim_id,
        "decision_status": e.decision_status,
        "reason": e.reason, "evidence": e.evidence,
        "payload": e.payload,
        "state_before": e.state_before, "state_after": e.state_after,
    }


# ============================================================ deserialization


def _dict_to_production(data: dict) -> Production:
    """Reverse of _production_to_dict. Robust to missing optional fields."""
    from src.schema.production_document import (
        Production as Prod,
        IntentDocument, Reference, Character, Environment,
        StyleToken, BrandKit, Scene, MoodSpec, Shot,
        CameraSpec, LightingSpec, AudioSpec, CharacterReference,
        GenerationResult, Timeline, Branch, VersionSnapshot,
        AuditEntry,
    )

    intent = IntentDocument(**(data.get("intent") or {"topic": "Untitled"}))
    refs = [Reference(**r) for r in data.get("references", [])]
    chars = [_dict_to_char(c) for c in data.get("characters", [])]
    envs = [_dict_to_env(e) for e in data.get("environments", [])]
    toks = [StyleToken(**t) for t in data.get("style_tokens", [])]
    brand = _dict_to_brand(data["brand_kit"]) if data.get("brand_kit") else None
    scenes = [_dict_to_scene(s) for s in data.get("scenes", [])]
    timeline = Timeline(**data["timeline"]) if data.get("timeline") else None
    branches = [Branch(**b) for b in data.get("branches", [])]
    snaps = [VersionSnapshot(**s) for s in data.get("snapshots", [])]
    entries = [_dict_to_audit(e) for e in data.get("audit_trail", [])]

    return Prod(
        schema_version=data.get("schema_version", "1.0.0"),
        id=data["id"],
        studio_id=data.get("studio_id"),
        title=data.get("title"),
        state=data["state"],
        created_at=data.get("created_at") or utc_now_iso(),
        updated_at=data.get("updated_at") or utc_now_iso(),
        intent=intent,
        references=refs,
        characters=chars,
        environments=envs,
        style_tokens=toks,
        brand_kit=brand,
        scenes=scenes,
        timeline=timeline,
        branches=branches,
        snapshots=snaps,
        audit_trail=entries,
        metadata=data.get("metadata", {}),
    )


def _dict_to_char(d: dict):
    from src.schema.production_document import Character, ConsistencyContract, Reference
    cc_raw = d.get("consistency_contract")
    if cc_raw:
        # visual_anchors inside the contract are Reference objects
        cc_anchors = [Reference(**r) for r in cc_raw.get("visual_anchors", [])]
        cc = ConsistencyContract(
            subject_id=cc_raw["subject_id"],
            visual_anchors=cc_anchors,
            required_attributes=cc_raw.get("required_attributes", []),
            prohibited_attributes=cc_raw.get("prohibited_attributes", []),
            variance_tolerance=cc_raw.get("variance_tolerance", 0.15),
            reviewer_checklist=cc_raw.get("reviewer_checklist", []),
        )
    else:
        cc = None
    visual_anchors = [Reference(**r) for r in d.get("visual_anchors", [])]
    return Character(
        id=d["id"], name=d["name"], role=d.get("role"),
        voice_id=d.get("voice_id"),
        visual_anchors=visual_anchors,
        consistency_contract=cc,
    )


def _dict_to_env(d: dict):
    from src.schema.production_document import Environment, ConsistencyContract, Reference
    cc_raw = d.get("consistency_contract")
    if cc_raw:
        cc_anchors = [Reference(**r) for r in cc_raw.get("visual_anchors", [])]
        cc = ConsistencyContract(
            subject_id=cc_raw["subject_id"],
            visual_anchors=cc_anchors,
            required_attributes=cc_raw.get("required_attributes", []),
            prohibited_attributes=cc_raw.get("prohibited_attributes", []),
            variance_tolerance=cc_raw.get("variance_tolerance", 0.15),
            reviewer_checklist=cc_raw.get("reviewer_checklist", []),
        )
    else:
        cc = None
    visual_anchors = [Reference(**r) for r in d.get("visual_anchors", [])]
    return Environment(
        id=d["id"], name=d["name"],
        time_of_day_variants=d.get("time_of_day_variants", []),
        visual_anchors=visual_anchors,
        lighting_presets=d.get("lighting_presets", []),
        consistency_contract=cc,
    )


def _dict_to_brand(d: dict):
    from src.schema.production_document import BrandKit, StyleToken, Reference
    return BrandKit(
        name=d.get("name"),
        palette=[StyleToken(**t) for t in d.get("palette", [])],
        typography=[StyleToken(**t) for t in d.get("typography", [])],
        logos=[Reference(**r) for r in d.get("logos", [])],
        approved_language=d.get("approved_language", []),
        prohibited_language=d.get("prohibited_language", []),
    )


def _dict_to_scene(d: dict):
    from src.schema.production_document import Scene, MoodSpec
    mood = MoodSpec(**d["mood"]) if d.get("mood") else None
    return Scene(
        id=d["id"], name=d["name"], mood=mood,
        location=d.get("location"),
        shots=[_dict_to_shot(s) for s in d.get("shots", [])],
        notes=d.get("notes"), stage=d.get("stage"),
    )


def _dict_to_shot(d: dict):
    from src.schema.production_document import (
        Shot, CameraSpec, LightingSpec, AudioSpec,
        CharacterReference, GenerationResult,
    )
    cam = CameraSpec(**d["camera"]) if d.get("camera") else None
    light = LightingSpec(**d["lighting"]) if d.get("lighting") else None
    audio = AudioSpec(**d["audio"]) if d.get("audio") else None
    chars = [
        CharacterReference(
            character_id=c["character_id"],
            expression=c.get("expression"),
            blocking_note=c.get("blocking_note"),
        )
        for c in d.get("characters", [])
    ]
    gen = _dict_to_generation(d["generation"]) if d.get("generation") else None
    version_history = [_dict_to_generation(g) for g in d.get("version_history", [])]
    return Shot(
        id=d["id"], scene_id=d["scene_id"], intent=d["intent"],
        duration_sec=d.get("duration_sec", 0.0),
        camera=cam, lighting=light, characters=chars, audio=audio,
        generation=gen, status=d.get("status", "draft"),
        locked=d.get("locked", False),
        version_history=version_history,
        storyboard_frame=d.get("storyboard_frame"),
    )


def _dict_to_generation(d: dict):
    from src.schema.production_document import GenerationResult
    if d is None:
        return None
    return GenerationResult(
        id=d["id"],
        produced_at=d["produced_at"],
        produced_by=d.get("produced_by"),
        backend=d.get("backend"),
        backend_version=d.get("backend_version"),
        prompt_hash=d.get("prompt_hash"),
        output_uri=d.get("output_uri"),
        output_sha256=d.get("output_sha256"),
        reviewer_verdict=d.get("reviewer_verdict", {}),
        cost_estimate_usd=d.get("cost_estimate_usd"),
        latency_ms=d.get("latency_ms"),
    )


def _dict_to_audit(d: dict):
    from src.schema.production_document import AuditEntry
    return AuditEntry(
        id=d["id"], ts=d["ts"], actor=d["actor"],
        action_type=d.get("action_type", "system"),
        gate_name=d.get("gate_name"),
        claim_id=d.get("claim_id"),
        decision_status=d.get("decision_status"),
        reason=d.get("reason"),
        evidence=d.get("evidence", {}),
        payload=d.get("payload", {}),
        state_before=d.get("state_before"),
        state_after=d.get("state_after"),
    )


# ============================================================ StudioService


@dataclass
class StudioService:
    """Filesystem-backed Layer-1 (Studio) state owner — §9 Information Architecture.

    A Studio is a workspace for an organisation or individual.  It holds
    shared brand kits, style tokens, member roles, and the list of
    production IDs that belong to it.

    Storage layout:
        <storage_dir>/studios/<studio_id>/studio.json

    Minimal surface (prototype scope):
        create / load / save / add_production / remove_production /
        set_member_role / list_studios / summary
    """

    storage_dir: Path

    def __post_init__(self) -> None:
        self.storage_dir = Path(self.storage_dir)
        self.studios_dir.mkdir(parents=True, exist_ok=True)
        # Same per-instance re-entrant lock as ProductionService; see that class.
        self._lock = threading.RLock()

    @property
    def studios_dir(self) -> Path:
        return self.storage_dir / "studios"

    def _studio_path(self, studio_id: str) -> Path:
        return self.studios_dir / studio_id / "studio.json"

    # ---------- create ----------

    def create(self, name: str, *, owner: Optional[str] = None) -> "Studio":
        """Create a new Studio on disk and return the dataclass."""
        from src.schema.production_document import Studio, BrandKit
        studio_id = _id("studio")
        now = utc_now_iso()
        studio = Studio(
            id=studio_id,
            name=name[:200] if name else "Untitled Studio",
            owner=owner,
            created_at=now,
            updated_at=now,
        )
        studio_dir = self.studios_dir / studio_id
        studio_dir.mkdir(parents=True, exist_ok=False)
        self._write_studio(studio)
        return studio

    # ---------- load / save ----------

    def load(self, studio_id: str) -> "Studio":
        """Reconstruct a Studio from disk. Raises ProductionNotFound on miss.

        Held under the same per-instance lock as save() for read/write consistency.
        """
        with self._lock:
            path = self._studio_path(studio_id)
            if not path.exists():
                raise ProductionNotFound(studio_id)
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise StorageError(f"corrupt studio.json for {studio_id}") from exc
            return _dict_to_studio(data)

    def save(self, studio: "Studio") -> "Studio":
        """Persist Studio state to disk (atomic write).

        Same per-instance lock as ProductionService.save: guards against concurrent
        saves from the same Python process.
        """
        with self._lock:
            (self.studios_dir / studio.id).mkdir(parents=True, exist_ok=True)
            self._write_studio(studio)
            return studio

    # ---------- add/remove production ----------

    def add_production(self, studio: "Studio", production_id: str) -> "Studio":
        """Return a new Studio with production_id added to the production list."""
        if production_id in studio.production_ids:
            return studio
        from dataclasses import replace as _replace
        updated = _replace(
            studio,
            production_ids=list(studio.production_ids) + [production_id],
            updated_at=utc_now_iso(),
        )
        return updated

    def remove_production(self, studio: "Studio", production_id: str) -> "Studio":
        """Return a new Studio with production_id removed from the list."""
        from dataclasses import replace as _replace
        updated = _replace(
            studio,
            production_ids=[p for p in studio.production_ids if p != production_id],
            updated_at=utc_now_iso(),
        )
        return updated

    # ---------- member roles ----------

    def set_member_role(self, studio: "Studio", member_id: str, role: str) -> "Studio":
        """Return a new Studio with the member role updated (or added)."""
        from dataclasses import replace as _replace
        new_roles = {**studio.member_roles, member_id: role}
        return _replace(studio, member_roles=new_roles, updated_at=utc_now_iso())

    def remove_member(self, studio: "Studio", member_id: str) -> "Studio":
        """Return a new Studio with the member removed."""
        from dataclasses import replace as _replace
        new_roles = {k: v for k, v in studio.member_roles.items() if k != member_id}
        return _replace(studio, member_roles=new_roles, updated_at=utc_now_iso())

    # ---------- list / summary ----------

    def list_studios(self) -> list[dict]:
        """Enumerate all studios on disk. Summary form (id + name + owner)."""
        out: list[dict] = []
        if not self.studios_dir.exists():
            return out
        for child in self.studios_dir.iterdir():
            if not child.is_dir():
                continue
            path = child / "studio.json"
            if not path.exists():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                out.append({
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "owner": data.get("owner"),
                    "production_count": len(data.get("production_ids", [])),
                    "updated_at": data.get("updated_at"),
                })
            except (json.JSONDecodeError, KeyError):
                continue
        return sorted(out, key=lambda s: s.get("updated_at") or "", reverse=True)

    def summary(self, studio_id: str) -> dict:
        """Return the Studio as a JSON-serialisable dict."""
        studio = self.load(studio_id)
        return _studio_to_dict(studio)

    # ---------- internals ----------

    def _write_studio(self, studio: "Studio") -> None:
        path = self._studio_path(studio.id)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = _studio_to_dict(studio)
        fd, tmp = tempfile.mkstemp(
            prefix=".studio.", suffix=".json.tmp", dir=str(path.parent)
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, sort_keys=True)
            _safe_replace(tmp, path)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise


# ---- Studio serialization helpers ----

def _studio_to_dict(s: "Studio") -> dict:
    from src.schema.production_document import Studio
    return {
        "id": s.id,
        "name": s.name,
        "owner": s.owner,
        "created_at": s.created_at,
        "updated_at": s.updated_at,
        "brand_kit": _brand_to_dict(s.brand_kit) if s.brand_kit else None,
        "style_tokens": [_tok_to_dict(t) for t in s.style_tokens],
        "member_roles": s.member_roles,
        "production_ids": s.production_ids,
        "metadata": s.metadata,
    }


def _dict_to_studio(d: dict) -> "Studio":
    from src.schema.production_document import Studio, BrandKit, StyleToken
    brand = _dict_to_brand(d["brand_kit"]) if d.get("brand_kit") else None
    toks = [StyleToken(**t) for t in d.get("style_tokens", [])]
    return Studio(
        id=d["id"],
        name=d["name"],
        owner=d.get("owner"),
        created_at=d.get("created_at") or utc_now_iso(),
        updated_at=d.get("updated_at") or utc_now_iso(),
        brand_kit=brand,
        style_tokens=toks,
        member_roles=d.get("member_roles", {}),
        production_ids=d.get("production_ids", []),
        metadata=d.get("metadata", {}),
    )
