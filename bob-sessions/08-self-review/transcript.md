# Bob Session 8 — Code Review (Self-transcript)

> **Note:** This is a self-transcript produced because Bob's session 8 paused
> on a premise mismatch — the named service file (`src/service/production_service.py`)
> did not exist at the time of the original prompt-A submission, so the review
> could not cite live code. The critique below is the closest analog: a tight
> review of the actual shipped Phase 1 code paths, produced by the same agent
> against the committed codebase before Phase 3 changes.
>
> The resolutions (T2, T3, T8) are linked at the bottom.

---

## What I would change for a production-grade codebase

### 1 · `EvidenceGate.process()` mutates the caller's dict

**Severity:** Medium

```python
# src/validation/gates.py:16-20 — before T2
def process(self, claim: dict) -> dict:
    source_ids = claim.get("source_ids") or []
    if not source_ids:
        claim["status"] = "rejected"   # mutates input
        claim["reason"] = "no source_ids"
    else:
        claim["status"] = "accepted"
        claim["reason"] = "has sources"
    return claim
```

This is a silent mutation bug. The caller at `demo_flow.py:172` guarded against it
with `ev_gate.process(dict(claim))` — a shallow copy that any future caller is unlikely
to remember. The fix is simple: return a new dict.

```python
# After T2
def process(self, claim: dict) -> dict:
    source_ids = claim.get("source_ids") or []
    if not source_ids:
        return {**claim, "status": "rejected", "reason": "no source_ids"}
    return {**claim, "status": "accepted", "reason": "has sources"}
```

**Fixed in T2.** Test added: `test_evidence_gate_does_not_mutate_input`.

---

### 2 · `FIXTURE_CLAIMS` and `FIXTURE_METADATA` are module-level constants, not injectable

**Severity:** Low-Medium

`build_demo_report()` always uses the module-level `FIXTURE_CLAIMS` and `FIXTURE_METADATA`.
Any test that wants to verify different shapes (e.g. zero claims, invalid metadata) must
either monkey-patch the module globals or call the function with full side effects.
The natural fix is optional parameters that default to the fixtures.

**Fixed in T3.** Two new tests: `test_build_demo_report_accepts_custom_claims`,
`test_build_demo_report_accepts_custom_metadata`.

---

### 3 · `AuditRecorder.__init__()` truncates the file on construction — keep as-is

**Severity:** Low (acceptable for the demo scope)

The recorder truncates its output file the moment it is instantiated. In a long-running
service this would be a bug (you'd lose prior audit trail on restart). For the demo — where
every demo run is a fresh session — this is intentional: the user always gets a clean file
without needing to manage rotation.

**Decision:** Keep as-is. Documented here for visibility. If the recorder is promoted to
a production-grade audit store, it should accept an `append: bool = False` flag.

---

### 4 · `pick_default_angle_id()` uses `ord(topic[0])` — keep, but document

**Severity:** Very low

```python
# src/demo_flow.py:68
idx = ord(topic[0].lower()) % len(ANGLE_IDS)
```

The hash is deterministic (the stability test confirms it), but a reader who doesn't know
the intent of this line might assume it is a bug or a placeholder. A one-line comment
explaining "deterministic hash to vary defaults across topics without any randomness"
would be sufficient.

**Decision:** Keep for submission. A comment is the right follow-up, not a refactor.

---

## §26 Differentiator gaps visible from the Phase 1 commit

The following gaps were identified when cross-referencing `open-production-plan.md` §26
against `docs/judge-pack/differentiators.md` and the committed source:

| Differentiator | Gap | Resolution |
|---|---|---|
| 01 · Production Document | Section cited schema docs but not `ProductionService` (the live serialization path) | T8: added `src/service/production_service.py` cites |
| 05 · Reviewer Agent | Section cited only `VisualQualityGate`; `ConsistencyContractGate` was only a dataclass, not an enforcing gate | T4: implemented `ConsistencyContractGate.check()`; T8: updated section 05 cite |
| 05 · Reviewer Agent | Agent Console UI (crew-facing event log visualiser) is absent from shipped code | T8: added honest deferral note |

---

## Resolution index

| Task | What it fixed |
|---|---|
| T2 | `EvidenceGate.process()` mutation hazard; 1 new test |
| T3 | `build_demo_report()` fixture injectability; 2 new tests |
| T4 | `ConsistencyContractGate.check()` implemented; 4 new tests |
| T8 | `differentiators.md` sections 01 and 05 updated with live code cites + honest deferral note |

---

*Self-transcript produced 2026-07-27 by IBM Bob during Phase 3 build. Covers Phase 1 code (pre-T2/T3 state). All resolutions applied and test suite verified at 73+ passing.*
