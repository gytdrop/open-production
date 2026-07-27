# Bob Session 3 — Tests and Gate-Validation Checks

**Date:** 2026-07-27  
**Goal:** Harden creative_reframing tests; write gate-validation suite.  
**Outcome:** See 3-line summary below.

---

## 3-line summary

Part A: Added two hardening tests to `test_creative_reframing.py` — one verifying that a partial LLM response (only 2 of 3 angles) triggers the retry path, and one verifying that a structurally malformed angle (missing `risk_focus`) drives both retries to fail and activates the deterministic fallback. No original tests were changed. Part B: Wrote `tests/test_gates.py` with 12 tests covering EvidenceGate, ConsistencyGate, and PublicationGate using shared pytest fixtures and no live API calls. One bug was flagged as a comment (empty `authors` list treated as missing). All 21 tests pass.

---

## Transcript

### Part A — Harden creative_reframing tests

**Bob review of existing `test_creative_reframing.py`:**

Checked against the 5 required paths:
- ✅ Happy path (mocked LLM returns valid JSON) — `test_happy_path_returns_three_angles`
- ✅ Malformed JSON retry path — `test_malformed_json_retries_and_succeeds`
- ✅ Missing-context safety — `test_missing_context_does_not_raise` (×3 via parametrize)
- ✅ Fallback (LLM fails twice) — `test_fallback_on_double_failure`
- ✅ Distinct `questions_to_address` — `test_angles_have_distinct_questions`

Two coverage gaps identified and closed:

1. **`test_partial_response_triggers_retry`** — the existing retry test only checks malformed JSON (parse failure). A more realistic failure mode is valid JSON with only 2 of 3 angle IDs. This test exercises that path: first call returns `{skeptic, advocate}` only, second call returns a valid 3-angle response.

2. **`test_angle_missing_required_key_uses_fallback`** — an angle can be valid JSON but missing a required key (`risk_focus`). Both attempts return this broken response → deterministic fallback fires. Tests that the fallback output references the topic.

### Part B — Gate-validation suite

Wrote `tests/test_gates.py` (168 lines) covering all three gates with pytest fixtures shared across tests.

**EvidenceGate (3 tests):**
- Rejection of uncited claim (no `source_ids`)
- Acceptance of cited claim
- Rejection includes a non-empty `reason` string (audit trail requirement)

**ConsistencyGate (5 tests):**
- Contradiction detected for same `fact_id`, differing `conclusion`
- Both claim objects surfaced in the result (gate does not pick a winner)
- No false positive for different `fact_id` values
- Empty claim list is safe (returns `[]`)
- Same fact_id + same conclusion is NOT a contradiction

**PublicationGate (4 tests):**
- Rejects missing DOI with a non-empty error string
- Rejects missing `authors` with a non-empty error string
- Accepts a fully populated metadata dict
- Returns `(False, str)` even for completely empty dict — never raises

**Bug flagged:**

In `test_publication_gate_rejects_missing_authors`, a comment notes:

> Bob flagged: `authors` is in `REQUIRED` but the check uses `not metadata.get("authors")`. An empty list `[]` is falsy — `gate.check({"doi": "x", "authors": [], "date": "y"})` returns `(False, "missing authors")` even though the key is present. This is arguably correct behaviour (empty list = no attribution), but it diverges from a key-presence contract. Flagged for Boris's review.

Production code was not modified.

---

## Files produced / modified

- `tests/test_creative_reframing.py` — 2 tests added (tests 6 and 7)
- `tests/test_gates.py` — new, 168 lines, 12 tests
