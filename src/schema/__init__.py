"""
src.schema — Production Document schema (Python dataclasses) + canonical JSON Schema.

The Python dataclasses in `production_document` are the typed mirror of
`docs/schema/production-document.schema.json`. The JSON Schema file is the
source of truth for validation; the dataclasses are for ergonomic Python use.

Import everything from here:

    from src.schema import Production, AuditEntry, IntentDocument, ...

Or import the bridge helper that converts legacy recorder calls:

    from src.schema import audit_entry_from_gate_decision
"""
from .production_document import (
    # enums / literals
    ProductionState, ShotStatus, ActionType, ReferenceKind,
    StyleTokenKind, CameraMovement, CameraFraming,
    # dataclasses
    IntentDocument, Reference, ConsistencyContract, Character,
    Environment, StyleToken, BrandKit, MoodSpec, CameraSpec,
    LightingSpec, AudioSpec, CharacterReference, GenerationResult,
    Shot, Scene, Timeline, Branch, VersionSnapshot, AuditEntry,
    Production,
    # helpers
    audit_entry_from_gate_decision, utc_now_iso,
)

__all__ = [
    "ProductionState", "ShotStatus", "ActionType", "ReferenceKind",
    "StyleTokenKind", "CameraMovement", "CameraFraming",
    "IntentDocument", "Reference", "ConsistencyContract", "Character",
    "Environment", "StyleToken", "BrandKit", "MoodSpec", "CameraSpec",
    "LightingSpec", "AudioSpec", "CharacterReference", "GenerationResult",
    "Shot", "Scene", "Timeline", "Branch", "VersionSnapshot", "AuditEntry",
    "Production",
    "audit_entry_from_gate_decision", "utc_now_iso",
]