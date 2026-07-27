"""
ProductionService — the runtime that owns Production state.

Companion to ACT-8 (CLI bridge design). This implements the subset of the
design doc that's needed for the prototype window:

  - init()         create a new Production in DRAFT
  - load()         reconstruct from production.json + audit.jsonl
  - save()         atomic write of production.json, append to audit.jsonl
  - status()       return full Production as JSON
  - log()          tail the audit journal with optional filters
  - apply_event()  pure: never mutates input, returns a new Production

Out of scope for the prototype window (per ACT-8 §9 scope cuts):
  - snapshot / branch / merge
  - real-time collaboration
  - reviewer-loop integration
  - consistency-contract enforcement as a hard gate

The class is intentionally small. It exists to give the two front-ends
(Guided Flow + Agent Console) a single source of truth.
"""
from __future__ import annotations

from .production_service import (
    ProductionService,
    ProductionNotFound,
    StorageError,
)

__all__ = ["ProductionService", "ProductionNotFound", "StorageError"]


# backward-compat helper for legacy code paths that build AuditEntry
# directly from recorder-style gate_decision calls
def audit_entry_from_gate_decision(**kwargs) -> "AuditEntry":  # noqa: F821
    """Deprecated: prefer src.schema.production_document.audit_entry_from_gate_decision."""
    from src.schema.production_document import audit_entry_from_gate_decision as _h
    return _h(**kwargs)
