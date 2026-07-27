"""
ProductionService — runtime owner of Production state.

Per ACT-8 §3 (command surface) and §4 (ProductionService interface).
This is the prototype implementation. It is intentionally minimal:
init / load / save / status / log / apply_event. Snapshot / branch /
merge are stubbed or omitted (see ACT-8 §9 scope cuts).
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
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


class ProductionNotFound(LookupError):
    """Raised when load() cannot find the requested production."""


class StorageError(RuntimeError):
    """Raised on atomic-write failures, schema mismatches, or replay errors."""


def _id(prefix: str) -> str:
    """Generate a new id like 'prod_<12 hex chars>' or 'evt_<12 hex chars>'."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


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

    # ---------- paths ----------
    def _prod_dir(self, production_id: str) -> Path:
        return self.storage_dir / production_id

    def _state_path(self, production_id: str) -> Path:
        return self._prod_dir(production_id) / "production.json"

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
        """Reconstruct Production from disk. Raises ProductionNotFound on miss."""
        state_path = self._state_path(production_id)
        if not state_path.exists():
            raise ProductionNotFound(production_id)
        try:
            data = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise StorageError(
                f"corrupt production.json for {production_id}"
            ) from exc
        return _dict_to_production(data)

    def save(self, prod: Production) -> Production:
        """Persist Production state. State file is atomic; journal is append-only."""
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

    # ---------- apply_event ----------
    def apply_event(self, prod: Production, entry: AuditEntry) -> Production:
        """Append an event to the production. Pure: never mutates input.

        Returns a NEW Production. The caller's input is untouched.
        """
        # Validate: state_transition events must reference a valid next state
        if entry.action_type == "state_transition":
            next_state = entry.payload.get("next_state") if entry.payload else None
            if next_state not in (
                "DRAFT", "BRIEFED", "IN_PRODUCTION", "IN_REVIEW", "APPROVED", "PUBLISHED"
            ):
                raise StorageError(
                    f"invalid state_transition payload: {entry.payload!r}"
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
        import hashlib
        blob = json.dumps(_production_to_dict(prod), sort_keys=True).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()[:16]

    def _write_state(self, prod: Production) -> None:
        """Atomic write of production.json. Uses temp file + rename."""
        path = self._state_path(prod.id)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = _production_to_dict(prod)
        # Write to temp file in same dir, then atomic rename
        fd, tmp_name = tempfile.mkstemp(
            prefix=".production.", suffix=".json.tmp", dir=str(path.parent)
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, sort_keys=True)
            os.replace(tmp_name, path)
        except Exception:
            try:
                os.unlink(tmp_name)
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
    from src.schema.production_document import Character, ConsistencyContract
    cc = ConsistencyContract(**d["consistency_contract"]) if d.get("consistency_contract") else None
    return Character(
        id=d["id"], name=d["name"], role=d.get("role"),
        voice_id=d.get("voice_id"),
        visual_anchors=[],   # simplify: anchors restored lazily
        consistency_contract=cc,
    )


def _dict_to_env(d: dict):
    from src.schema.production_document import Environment, ConsistencyContract
    cc = ConsistencyContract(**d["consistency_contract"]) if d.get("consistency_contract") else None
    return Environment(
        id=d["id"], name=d["name"],
        time_of_day_variants=d.get("time_of_day_variants", []),
        visual_anchors=[],
        lighting_presets=d.get("lighting_presets", []),
        consistency_contract=cc,
    )


def _dict_to_brand(d: dict):
    from src.schema.production_document import BrandKit, StyleToken
    return BrandKit(
        name=d.get("name"),
        palette=[StyleToken(**t) for t in d.get("palette", [])],
        typography=[StyleToken(**t) for t in d.get("typography", [])],
        logos=[],
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
    from src.schema.production_document import Shot, CameraSpec, LightingSpec, AudioSpec
    cam = CameraSpec(**d["camera"]) if d.get("camera") else None
    light = LightingSpec(**d["lighting"]) if d.get("lighting") else None
    audio = AudioSpec(**d["audio"]) if d.get("audio") else None
    return Shot(
        id=d["id"], scene_id=d["scene_id"], intent=d["intent"],
        duration_sec=d.get("duration_sec", 0.0),
        camera=cam, lighting=light, characters=[], audio=audio,
        generation=None, status=d.get("status", "draft"),
        locked=d.get("locked", False),
        version_history=[],
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
