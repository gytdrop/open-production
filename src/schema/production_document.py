"""
Production Document data model — Python mirror of production-document.schema.json.

Source of truth is the JSON Schema file (docs/schema/production-document.schema.json).
This module provides typed Python access via stdlib dataclasses — no new dependencies.

Design choices:
- Field names use snake_case to match Python convention (schema uses snake_case too).
- Enum-like fields use Literal types.
- Optional fields use Optional[T] = None with default.
- All ids are strings; the format pattern (e.g. ^prod_...) is enforced at construction
  by the `_validate_id_format` helper.
- The AuditEntry is append-only and its field shape is compatible with the existing
  src/audit/recorder.py:record_gate_decision interface.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Optional


# ----------------------------------------------------------------- helpers

def _validate_id_format(value: str, prefix: str) -> str:
    """ID format: <prefix>_<alphanumeric/dash/underscore>, min length."""
    if not value.startswith(f"{prefix}_"):
        raise ValueError(f"id must start with '{prefix}_' (got {value!r})")
    suffix = value[len(prefix) + 1 :]
    if len(suffix) < 4:
        raise ValueError(f"id suffix too short (got {len(suffix)} chars, need >=4)")
    if not all(c.isalnum() or c in "-_" for c in suffix):
        raise ValueError(f"id contains invalid chars (got {value!r})")
    return value


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ----------------------------------------------------------------- enums

ProductionState = Literal[
    "DRAFT", "BRIEFED", "IN_PRODUCTION", "IN_REVIEW", "APPROVED", "PUBLISHED"
]

ShotStatus = Literal[
    "draft", "in_production", "generated", "in_review", "approved", "rejected"
]

ActionType = Literal[
    "gate_decision", "decision", "lock", "unlock",
    "snapshot", "branch", "merge",
    "state_transition", "stage_advance", "override", "comment", "system"
]

ReferenceKind = Literal["image", "video", "audio", "text", "url"]

StyleTokenKind = Literal[
    "color", "texture", "lighting", "motion", "framing", "voice", "music", "composite"
]

CameraMovement = Literal[
    "static", "pan", "tilt", "dolly", "push_in", "pull_out", "handheld", "custom"
]

CameraFraming = Literal[
    "extreme_close", "close", "medium", "wide", "extreme_wide",
    "over_the_shoulder", "custom"
]


# ----------------------------------------------------------------- nested

@dataclass
class IntentDocument:
    topic: str
    audience: Optional[str] = None
    tone: Optional[str] = None
    platform: Optional[str] = None
    duration_sec: Optional[float] = None
    style_seed: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Reference:
    id: str
    kind: ReferenceKind
    label: str
    uri: Optional[str] = None
    sha256: Optional[str] = None
    pinned_by: Optional[str] = None
    pinned_at: Optional[str] = None

    def __post_init__(self):
        _validate_id_format(self.id, "ref")


@dataclass
class ConsistencyContract:
    """Spec the Reviewer agent gates generations against."""
    subject_id: str
    visual_anchors: list[Reference] = field(default_factory=list)
    required_attributes: list[str] = field(default_factory=list)
    prohibited_attributes: list[str] = field(default_factory=list)
    variance_tolerance: float = 0.15
    reviewer_checklist: list[str] = field(default_factory=list)


@dataclass
class Character:
    id: str
    name: str
    role: Optional[str] = None
    voice_id: Optional[str] = None
    visual_anchors: list[Reference] = field(default_factory=list)
    consistency_contract: Optional[ConsistencyContract] = None

    def __post_init__(self):
        _validate_id_format(self.id, "char")


@dataclass
class Environment:
    id: str
    name: str
    time_of_day_variants: list[str] = field(default_factory=list)
    visual_anchors: list[Reference] = field(default_factory=list)
    lighting_presets: list[str] = field(default_factory=list)
    consistency_contract: Optional[ConsistencyContract] = None

    def __post_init__(self):
        _validate_id_format(self.id, "env")


@dataclass
class StyleToken:
    id: str
    name: str
    kind: StyleTokenKind
    value: Any = None
    tokens: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        _validate_id_format(self.id, "tok")


@dataclass
class BrandKit:
    name: Optional[str] = None
    palette: list[StyleToken] = field(default_factory=list)
    typography: list[StyleToken] = field(default_factory=list)
    logos: list[Reference] = field(default_factory=list)
    approved_language: list[str] = field(default_factory=list)
    prohibited_language: list[str] = field(default_factory=list)


@dataclass
class MoodSpec:
    emotional_promise: Optional[str] = None
    tonal_palette: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    locked: bool = False


@dataclass
class CameraSpec:
    focal_length_mm: Optional[float] = None
    frame_rate: Optional[float] = None
    aperture: Optional[str] = None
    movement: Optional[CameraMovement] = None
    framing: Optional[CameraFraming] = None
    preset_id: Optional[str] = None


@dataclass
class LightingSpec:
    key_intensity_pct: Optional[float] = None
    fill_intensity_pct: Optional[float] = None
    color_temp_k: Optional[float] = None
    preset_id: Optional[str] = None


@dataclass
class AudioSpec:
    voice_direction: Optional[str] = None
    sfx: list[str] = field(default_factory=list)
    music_cue: Optional[str] = None


@dataclass
class CharacterReference:
    character_id: str
    expression: Optional[str] = None
    blocking_note: Optional[str] = None


@dataclass
class GenerationResult:
    id: str
    produced_at: str
    produced_by: Optional[str] = None
    backend: Optional[str] = None
    backend_version: Optional[str] = None
    prompt_hash: Optional[str] = None
    output_uri: Optional[str] = None
    output_sha256: Optional[str] = None
    reviewer_verdict: dict[str, Any] = field(default_factory=dict)
    cost_estimate_usd: Optional[float] = None
    latency_ms: Optional[int] = None

    def __post_init__(self):
        _validate_id_format(self.id, "gen")


@dataclass
class Shot:
    id: str
    scene_id: str
    intent: str
    duration_sec: float
    status: ShotStatus = "draft"
    camera: Optional[CameraSpec] = None
    lighting: Optional[LightingSpec] = None
    characters: list[CharacterReference] = field(default_factory=list)
    audio: Optional[AudioSpec] = None
    generation: Optional[GenerationResult] = None
    locked: bool = False
    version_history: list[GenerationResult] = field(default_factory=list)
    storyboard_frame: Optional[str] = None       # ASCII/SVG blocking diagram — StoryboardArtistAgent (K.2)
    color_spec: Optional[dict[str, Any]] = None  # ColoristAgent approved grade (K.9)
    motion_spec: Optional[dict[str, Any]] = None # AnimationDirectorAgent approved motion (Stage 18)

    def __post_init__(self):
        _validate_id_format(self.id, "shot")


@dataclass
class ColorSpec:
    """Per-shot or per-scene colour grade specification (K.9 ColoristAgent output)."""
    look_name: Optional[str] = None
    primary: dict[str, Any] = field(default_factory=dict)
    creative: dict[str, Any] = field(default_factory=dict)
    rationale: Optional[str] = None


@dataclass
class Scene:
    id: str
    name: str
    shots: list[Shot] = field(default_factory=list)
    mood: Optional[MoodSpec] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    stage: Optional[str] = None
    sound_palette: Optional[dict[str, Any]] = None   # SoundDesignerAgent output (K.6)
    music_cue: Optional[dict[str, Any]] = None       # MusicComposerAgent brief (K.7)
    color_look: Optional[ColorSpec] = None           # ColoristAgent approved look (K.9)

    def __post_init__(self):
        _validate_id_format(self.id, "scene")


@dataclass
class Timeline:
    scene_order: list[str] = field(default_factory=list)
    transitions: list[dict[str, Any]] = field(default_factory=list)
    music_cues: list[dict[str, Any]] = field(default_factory=list)
    # Assembled by ProductionService.commit_editor_proposal() from an EditorAgent proposal.
    # Each entry: {"scene_id": str, "shot_id": str, "duration_sec": float}
    shot_durations: list[dict[str, Any]] = field(default_factory=list)
    total_duration_sec: float = 0.0


@dataclass
class Branch:
    id: str
    name: str
    created_at: str
    parent_snapshot_id: Optional[str] = None
    created_by: Optional[str] = None
    locked: bool = False

    def __post_init__(self):
        _validate_id_format(self.id, "branch")


@dataclass
class VersionSnapshot:
    id: str
    taken_at: str
    content_hash: str
    taken_by: Optional[str] = None
    label: Optional[str] = None
    branch_id: Optional[str] = None

    def __post_init__(self):
        _validate_id_format(self.id, "snap")


@dataclass
class AuditEntry:
    """
    Append-only event log entry.

    Compatible with src/audit/recorder.py:record_gate_decision field shape.
    Extended with actor + action_type for non-gate events.
    """
    id: str
    ts: str
    actor: str
    action_type: ActionType
    gate_name: Optional[str] = None
    claim_id: Optional[str] = None
    decision_status: Optional[str] = None
    reason: Optional[str] = None
    evidence: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)
    state_before: Optional[str] = None
    state_after: Optional[str] = None

    def __post_init__(self):
        _validate_id_format(self.id, "evt")
        if self.action_type == "gate_decision":
            if not (self.gate_name and self.claim_id and self.decision_status):
                raise ValueError(
                    "gate_decision AuditEntry requires gate_name, claim_id, decision_status"
                )


# ----------------------------------------------------------------- root

@dataclass
class Studio:
    """Layer 1 of the three-layer information architecture (§9).

    A Studio is a workspace for an organisation or individual.
    It holds shared brand kits, asset libraries, member roles, and
    production presets — equivalent to a Figma Team.
    """
    id: str
    name: str
    owner: Optional[str] = None
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    brand_kit: Optional[BrandKit] = None
    style_tokens: list[StyleToken] = field(default_factory=list)
    member_roles: dict[str, str] = field(default_factory=dict)  # member_id → role
    production_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        _validate_id_format(self.id, "studio")


@dataclass
class Production:
    """The root document. All five views render slices of this state."""
    id: str
    state: ProductionState
    intent: IntentDocument
    scenes: list[Scene]
    audit_trail: list[AuditEntry]
    schema_version: str = "1.0.0"
    studio_id: Optional[str] = None
    title: Optional[str] = None
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    references: list[Reference] = field(default_factory=list)
    characters: list[Character] = field(default_factory=list)
    environments: list[Environment] = field(default_factory=list)
    style_tokens: list[StyleToken] = field(default_factory=list)
    brand_kit: Optional[BrandKit] = None
    timeline: Optional[Timeline] = None
    branches: list[Branch] = field(default_factory=list)
    snapshots: list[VersionSnapshot] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        _validate_id_format(self.id, "prod")
        if self.studio_id is not None:
            _validate_id_format(self.studio_id, "studio")


# ----------------------------------------------------------------- legacy bridge

def audit_entry_from_gate_decision(
    *,
    gate_name: str,
    claim_id: str,
    decision_status: str,
    reason: str = "",
    evidence: Optional[dict[str, Any]] = None,
    actor: str = "system",
    ts: Optional[str] = None,
) -> AuditEntry:
    """
    Bridge helper: convert a legacy record_gate_decision() call into the new
    AuditEntry shape. Use this in src/audit/recorder.py to keep backward
    compatibility with existing code.

    Returns a fully-formed AuditEntry. The caller is responsible for appending
    it to the production's audit_trail (or the JSONL file).
    """
    import hashlib
    import uuid

    entry_id = "evt_" + uuid.uuid4().hex[:12]
    return AuditEntry(
        id=entry_id,
        ts=ts or utc_now_iso(),
        actor=actor,
        action_type="gate_decision",
        gate_name=gate_name,
        claim_id=claim_id,
        decision_status=decision_status,
        reason=reason,
        evidence=evidence or {},
    )


__all__ = [
    # enums / literals
    "ProductionState", "ShotStatus", "ActionType", "ReferenceKind",
    "StyleTokenKind", "CameraMovement", "CameraFraming",
    # dataclasses
    "IntentDocument", "Reference", "ConsistencyContract", "Character",
    "Environment", "StyleToken", "BrandKit", "MoodSpec", "CameraSpec",
    "LightingSpec", "AudioSpec", "CharacterReference", "GenerationResult",
    "Shot", "ColorSpec", "Scene", "Timeline", "Branch", "VersionSnapshot",
    "AuditEntry", "Studio", "Production",
    # helpers
    "audit_entry_from_gate_decision", "utc_now_iso",
]