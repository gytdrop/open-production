# Bob Session 8 — Code Review (Prompt A)

**Date:** 2026-07-27
**Goal:** Receive a structured code-review critique of the Phase 1 codebase from Bob (IBM Bob agent), identify fixable gaps before submission, and capture the differentiator analysis for the judge pack.
**Outcome:** 4 code findings identified; 3 differentiator gaps surfaced; findings T2 and T3 scheduled for immediate remediation.

---

## Context

Bob's prompt-A code review was conducted against the committed Phase 1 codebase (63/63 tests passing, `ProductionService` + `dual-artifact demo_flow` shipped). Bob reviewed the following files:

- `src/validation/gates.py`
- `src/demo_flow.py`
- `src/audit/recorder.py`
- `src/schema/production_document.py`
- `docs/judge-pack/differentiators.md`
- `open-production-plan.md` (§26 differentiators)

---

## Bob's 4 Code Findings

### Finding #1 — `EvidenceGate.process()` mutates caller's dict in-place

**File:** `src/validation/gates.py:16-20`
**Severity:** Medium (correctness/fragility)

```python
# Before — mutates input
def process(self, claim: dict) -> dict:
    source_ids = claim.get("source_ids") or []
    if not source_ids:
        claim["status"] = "rejected"          # mutates the caller's dict
        claim["reason"] = "no source_ids"
    else:
        claim["status"] = "accepted"
        claim["reason"] = "has sources"
    return claim
```

The method assigns keys directly to the passed-in dict, which means a caller
iterating over a list of claims will see its dicts silently modified after the call.
`demo_flow.py` worked around this with `ev_gate.process(dict(claim))` — a fragile
caller-side defence that any future caller may forget.

**Resolution:** T2 — return `{**claim, "status": ..., "reason": ...}` instead of mutating.

---

### Finding #2 — `FIXTURE_CLAIMS` and `FIXTURE_METADATA` are hardcoded module-level constants

**File:** `src/demo_flow.py:32-61`, `src/demo_flow.py:171`, `src/demo_flow.py:190`, `src/demo_flow.py:205`
**Severity:** Low-Medium (testability / injectability)

`build_demo_report()` has no mechanism to accept custom claims or metadata. Any test
that wants to verify different claim counts or metadata shapes must patch module-level
globals — an anti-pattern that makes tests brittle and obscures what is actually being
tested.

**Resolution:** T3 — add `claims: list[dict] | None = None` and `metadata: dict | None = None`
optional params; default to the fixture constants when None.

---

### Finding #3 — `AuditRecorder.__init__()` truncates the file on construction

**File:** `src/audit/recorder.py`
**Severity:** Low (acceptable for the demo scope)

The recorder truncates its output file when instantiated. This is correct for a
single-session demo (each demo run starts fresh) but would be a bug in a long-running
service that re-instantiates the recorder. Flagged, but **kept as-is** per submission
scope — the demo is single-session and the truncation-on-init is intentional.

**Resolution:** No change. Document in T10.

---

### Finding #4 — `pick_default_angle_id()` uses `ord(topic[0])` for determinism

**File:** `src/demo_flow.py:64-69`
**Severity:** Very low (style/documentation)

```python
idx = ord(topic[0].lower()) % len(ANGLE_IDS)
```

The function is deterministic and the test (`test_pick_default_angle_id_is_stable`) verifies
stability. However, the rationale for this particular hashing approach is not documented,
which could confuse a future contributor. Flagged for documentation only.

**Resolution:** No change for submission. A comment would be added in a post-submission cleanup.

---

## Bob's 3 Differentiator Gaps

### Gap A — Reviewer Agent (§26 differentiator 05) cites `VisualQualityGate` but not `ConsistencyContractGate`

**Before Phase 3:** `differentiators.md` section 05 cited only `src/videos/quality_evaluation.py`,
which gates per-frame visual quality. The `ConsistencyContractGate` (the gate that enforces
character and environment visual consistency contracts) was not yet implemented — it was
only specified in `docs/schema/production_document.py` as a dataclass.

**Resolution:** T4 implements `ConsistencyContractGate.check()` in `src/validation/gates.py`;
T8 updates `differentiators.md` section 05 to cite it.

### Gap B — Production Document (§26 differentiator 01) cites schema docs but not the live service

**Before Phase 3:** Section 01 cited the JSON schema and the Python dataclass mirror in `docs/`.
The runtime service (`src/service/production_service.py`) that actually serializes, saves,
and events the `Production` object was not cited.

**Resolution:** T8 adds `src/service/production_service.py` and `src/schema/production_document.py`
to section 01's evidence block.

### Gap C — Agent Console UI is a differentiator absent from shipped code

**Status:** Honest deferral. The Agent Console (the crew-facing UI surface that would visualize
the event log in real time) was parked per submission-window scope (K issue #1948).
The differentiator is real — the architecture and event log are fully designed — but no
UI code ships. Section 05 now includes an explicit note: "parked per submission-window scope."

---

## Session Outcome Summary

| Finding | Status | Task |
|---------|--------|------|
| `EvidenceGate` mutation hazard | ✅ Fixed | T2 |
| `FIXTURE_*` hardcoded constants | ✅ Fixed | T3 |
| `AuditRecorder` truncation-on-init | ⚠️ Kept (acceptable) | — |
| `pick_default_angle_id` undocumented | ⚠️ Deferred | post-submission |
| Gap A: ConsistencyContractGate not implemented | ✅ Fixed | T4 + T8 |
| Gap B: ProductionService not cited in differentiators | ✅ Fixed | T8 |
| Gap C: Agent Console UI absent from code | ✅ Disclosed honestly | T8 |
