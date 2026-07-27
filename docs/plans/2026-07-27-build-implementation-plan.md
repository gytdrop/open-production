# Open Production — Build Implementation Plan

> Derived from `docs/plans/2026-07-27-master-build-playbook.md`.
> This document tracks all 11 tasks (T1-T11) through agent-mode implementation.
> Test floor invariant: `pytest tests/ -q` must report ≥63 passed at every phase boundary.

---

## Top-Level Overview

**Goal:** Complete Phase 3 (ConsistencyContract gate + fixture + example docs) and Phase 4
(code-review fix, fixture injectability, differentiators update, PNG renders) so the project
is submission-ready with ≥71 tests passing.

**Current state:** Phase 1 complete, 61 tests passing. All T1-T11 tasks pending.

**Approach:** Execute tasks in dependency order. Code tasks (T2→T3→T4→T5→T6) first,
then doc tasks (T1, T7, T8, T10) in parallel context, then visuals (T9), then final run (T11).

---

## Sub-Tasks

---

### T1 · Archive Bob's prompt-A transcript

**Intent:** Create the `bob-sessions/08-code-review/` session directory and populate it
with a `transcript.md` summarizing Bob's 4 code-review findings and 3 differentiator gaps.
This is an archival doc — no code changes.

**Expected Outcomes:**
- `bob-sessions/08-code-review/transcript.md` exists and is ≥2 KB
- `bob-sessions/08-code-review/spec.md` exists as a session spec stub

**Todo List:**
1. Create `bob-sessions/08-code-review/` directory
2. Write `transcript.md` summarizing Bob's 4 findings (EvidenceGate mutation, FIXTURE_CLAIMS hardcoding, AuditRecorder __init__ truncation, pick_default_angle_id via ord) and 3 differentiator gaps
3. Write `spec.md` with session prompt/context

**Relevant Context:**
- Playbook section T1 (line 46–49)
- Bob's 4 findings are listed in the playbook T10 section (lines 212–218)
- Sessions 01-07 in `bob-sessions/` are the reference format

**Status:** [ ] pending

---

### T2 · Fix `EvidenceGate.process` mutation hazard

**Intent:** Fix the bug where `EvidenceGate.process()` mutates the caller's dict in-place.
Return a new dict instead. Add 1 test asserting immutability.

**Expected Outcomes:**
- `src/validation/gates.py` `EvidenceGate.process()` returns `{**claim, ...}` instead of mutating
- `tests/test_gates.py` has 1 new test: `test_evidence_gate_does_not_mutate_input`
- Full suite ≥64 passed (was 61 + this 1 new test + 2 previously counted)

**Todo List:**
1. Read `src/validation/gates.py` lines 16–20
2. Replace mutation-in-place with new-dict return using `{**claim, "status": ..., "reason": ...}`
3. Read `src/demo_flow.py` to find the `dict(claim)` workaround and remove it if no longer needed
4. Add test `test_evidence_gate_does_not_mutate_input` to `tests/test_gates.py`
5. Run `pytest tests/test_gates.py -q` to confirm pass

**Relevant Context:**
- `src/validation/gates.py:16-20` — EvidenceGate.process (mutates input)
- `src/demo_flow.py:110` — `dict(claim)` workaround (remove after fix)
- Playbook T2 (lines 52–76) has exact before/after code

**Status:** [ ] pending

---

### T3 · Parameterize `FIXTURE_CLAIMS` and `FIXTURE_METADATA`

**Intent:** Add optional `claims` and `metadata` parameters to `build_demo_report()` so
callers can inject custom data. Defaults to existing module-level fixtures.
Add 2 tests for the new parameters.

**Expected Outcomes:**
- `src/demo_flow.py` `build_demo_report()` signature has `claims: list[dict] | None = None` and `metadata: dict | None = None`
- Internal usage of `FIXTURE_CLAIMS` and `FIXTURE_METADATA` falls back to them when params are None
- `tests/test_demo_flow.py` has 2 new tests: custom claims accepted, custom metadata accepted
- Full suite ≥66 passed

**Todo List:**
1. Read `src/demo_flow.py` full `build_demo_report()` function
2. Add `claims` and `metadata` optional params to signature
3. Replace hardcoded references to `FIXTURE_CLAIMS` and `FIXTURE_METADATA` with `claims`/`metadata` locals
4. Add 2 new tests to `tests/test_demo_flow.py`
5. Run `pytest tests/test_demo_flow.py -q` to confirm pass

**Relevant Context:**
- `src/demo_flow.py:89-96` — current signature (no claims/metadata params)
- Playbook T3 (lines 78–98) has exact new signature
- `FIXTURE_CLAIMS` at `src/demo_flow.py:32-54`, `FIXTURE_METADATA` at `src/demo_flow.py:56-61`

**Status:** [ ] pending

---

### T4 · Implement `ConsistencyContractGate.check()`

**Intent:** Add a new `ConsistencyContractGate` class to `src/validation/gates.py` with a
`check(contract, result)` method that returns `(bool, str)`. Stop-fast on first missing
required attribute, then check prohibited. 4 tests.

**Expected Outcomes:**
- `src/validation/gates.py` has `ConsistencyContractGate` class with `check()` method
- `tests/test_gates.py` has 4 new tests covering: missing-required, prohibited-present, empty-contract, tight-tolerance
- Full suite ≥70 passed

**Todo List:**
1. Read `src/validation/gates.py` to find the insertion point (after `PublicationGate`)
2. Add `ConsistencyContractGate` class with exact implementation from playbook T4 (lines 104-126)
3. Add 4 tests to `tests/test_gates.py`:
   - `test_ccgate_missing_required_attribute`
   - `test_ccgate_prohibited_attribute_present`
   - `test_ccgate_empty_contract_passes`
   - `test_ccgate_tight_tolerance_partial_match`
4. Run `pytest tests/test_gates.py -q` to confirm all pass

**Relevant Context:**
- `src/validation/gates.py` — add after last gate class
- Playbook T4 (lines 100-134) has exact class implementation and test case specs
- `variance_tolerance` threshold: ≤0.10 triggers detailed partial-match message

**Status:** [ ] pending

---

### T5 · Generate `examples/generate_consistency_violation_fixture.py`

**Intent:** Create a runnable script that writes a `production.json` + `consistency_violation_audit.jsonl`
pair to `output/consistency_violation/`, demonstrating a failed ConsistencyContract enforcement.
The fixture has 3 entries: gen-001 pass, gen-002 violation, production_blocked summary.

**Expected Outcomes:**
- `examples/generate_consistency_violation_fixture.py` exists and is runnable
- Running it creates `output/consistency_violation/production.json`
- Running it creates `output/consistency_violation/consistency_violation_audit.jsonl` with ≥3 entries
- Entry 2 has `decision_status: "contract_violated"` and reason naming `red_scarf`

**Todo List:**
1. Read `examples/generate_audit_fixture.py` to understand the existing fixture script pattern
2. Write `examples/generate_consistency_violation_fixture.py` following the same pattern
3. Scenario: contract for `char-elena` requires `["red_scarf", "silver_locket"]`; gen-001 has both (pass); gen-002 has only `silver_locket` (violation)
4. Script writes 3 JSONL entries to `output/consistency_violation/consistency_violation_audit.jsonl`
5. Run the script via `python examples/generate_consistency_violation_fixture.py` and verify output

**Relevant Context:**
- Playbook T5 (lines 136–147)
- `examples/generate_audit_fixture.py` — reference implementation to mirror
- `src/validation/gates.py:ConsistencyContractGate` (T4 must be done first)

**Status:** [ ] pending

---

### T6 · Add fixture regenerability test

**Intent:** Add `tests/test_consistency_violation_fixture.py` that runs the T5 script via
subprocess and asserts the JSONL output is correct. 3 assertions.

**Expected Outcomes:**
- `tests/test_consistency_violation_fixture.py` exists with 3 assertions
- Full suite ≥71 passed

**Todo List:**
1. Create `tests/test_consistency_violation_fixture.py`
2. Test: run `examples/generate_consistency_violation_fixture.py` via subprocess
3. Assert: JSONL file exists and has ≥3 lines
4. Assert: second entry has `decision_status: "contract_violated"`
5. Assert: reason string contains `red_scarf`
6. Run `pytest tests/test_consistency_violation_fixture.py -q` to confirm pass

**Relevant Context:**
- Playbook T6 (lines 149–157)
- `tests/conftest.py` — check for any relevant fixtures (e.g., tmp_path)
- Script output target: `output/consistency_violation/consistency_violation_audit.jsonl`

**Status:** [ ] pending

---

### T7 · Write `docs/schema/consistency-contract-examples.md`

**Intent:** Create the reference document with 5 worked examples of ConsistencyContract
enforcement. Each example includes YAML contract, YAML result, bold verdict, and 2-3 sentence
explanation. Concludes with a Gate Return Value Reference table.

**Expected Outcomes:**
- `docs/schema/consistency-contract-examples.md` exists and is ≥4 KB
- Contains 5 examples (2 PASS, 3 FAIL) covering all gate branch paths
- Final table maps scenario → exact `(ok: bool, reason: str)` tuple

**Todo List:**
1. Create `docs/schema/consistency-contract-examples.md`
2. Example 1: PASS — char "Nadia", all required present, nothing prohibited
3. Example 2: FAIL — char "Nadia", missing `short_hair`
4. Example 3: FAIL — char (not environment!), `headlamp` prohibited, mine helmet context
5. Example 4: FAIL — `variance_tolerance: 0.05`, partial match `hair_cropped` rejected (tight tolerance)
6. Example 5: PASS — empty contract, only `subject_id`
7. Add Gate Return Value Reference table at end

**Relevant Context:**
- Playbook T7 (lines 159–172)
- `src/validation/gates.py:ConsistencyContractGate.check()` — must cite exact return strings
- All IDs must follow schema patterns: `gen-NNN`, `char-NNN`, `env-NNN`

**Status:** [ ] pending

---

### T8 · Update `docs/judge-pack/differentiators.md`

**Intent:** Patch the differentiators doc to cite the live Phase 1/3 code files. Update
sections 01 and 05 file:line references. Add note about Agent Console being parked.

**Expected Outcomes:**
- Section 01 cites `src/service/production_service.py` and `src/schema/production_document.py`
- Section 05 cites `src/validation/gates.py:ConsistencyContractGate.check()`
- Note added: Agent Console UI parked per submission scope
- 4/5 differentiators cite live code

**Todo List:**
1. Read `docs/judge-pack/differentiators.md` in full
2. Find section 01 — update file:line reference to add `src/service/production_service.py`
3. Find section 05 — update reference from `src/videos/quality_evaluation.py` to `src/validation/gates.py:ConsistencyContractGate`
4. Add short note about Agent Console being parked
5. Verify no other sections need updates

**Relevant Context:**
- Playbook T8 (lines 174–183)
- `docs/judge-pack/differentiators.md` — current content (44 lines)
- T4 must be done first (ConsistencyContractGate must exist before citing it)

**Status:** [ ] pending

---

### T9 · Render wireframe SVGs to PNG

**Intent:** Render all 6 SVG wireframes to PNG using a Python script (cairosvg or svg2png).
Output goes to `docs/wireframes/*.png` alongside the SVGs.

**Expected Outcomes:**
- 6 PNG files exist in `docs/wireframes/`: `01-directors-canvas.png`, `02-guided-flow.png`, `03-timeline-editor.png`, `04-agent-console.png`, `05-node-graph.png`, `all-views-composite.png`

**Todo List:**
1. Check if `cairosvg` is installed (`pip show cairosvg`); if not, try `pip install cairosvg` or alternative
2. Write a small render script (inline or standalone) using cairosvg to convert each SVG
3. Run it and verify 6 PNG files are created
4. If cairosvg unavailable, use Inkscape CLI: `inkscape --export-type=png <file>.svg`

**Relevant Context:**
- Playbook T9 (lines 185–196)
- SVG files: `docs/wireframes/01-directors-canvas.svg`, `02-guided-flow.svg`, `03-timeline-editor.svg`, `04-agent-console.svg`, `05-node-graph.svg`, `all-views-composite.svg`

**Status:** [ ] pending

---

### T10 · Write self-review transcript

**Intent:** Create `bob-sessions/08-self-review/transcript.md` as a close analog to a
formal code-review session, documenting what was reviewed, what was found, and what T2/T3/T8
resolved.

**Expected Outcomes:**
- `bob-sessions/08-self-review/transcript.md` exists and is ≥1 KB
- Documents the 4 findings Bob would have surfaced in a real session 8
- Links to T2, T3, T8 as resolutions

**Todo List:**
1. Create `bob-sessions/08-self-review/` directory
2. Write `transcript.md` following the format in the playbook T10 section (lines 203-224)
3. Include: 4 findings (EvidenceGate mutation, FIXTURE hardcoding, AuditRecorder truncation, ord() angle selection), §26 differentiator gaps, resolution links to T2/T3/T8

**Relevant Context:**
- Playbook T10 (lines 198–224) — has the exact template
- References T2, T3, T8 resolutions
- See `bob-sessions/07-video-vertical/transcript.md` for session format reference

**Status:** [ ] pending

---

### T11 · Final test run + commit + submit prep

**Intent:** Verify ≥71 tests pass, commit all changes, push to remote.

**Expected Outcomes:**
- `pytest tests/ -q --basetemp=C:\Temp\pytest-openprod -p no:asyncio` reports ≥71 passed
- All files committed with message: `feat(ibm-challenge): ProductionService, ConsistencyContract gate, fixture, differentiators updated`
- Repo pushed to origin

**Todo List:**
1. Run full test suite with the exact command from the playbook
2. If <71 tests, identify the gap and fix it
3. `git add -A`
4. `git commit -m "feat(ibm-challenge): ProductionService, ConsistencyContract gate, fixture, differentiators updated"`
5. `git push`

**Relevant Context:**
- Playbook T11 (lines 226–239)
- Test floor: 63 minimum at all times; target ≥71 after all tasks
- Rollback strategy: each task is a small commit; revert is safe

**Status:** [ ] pending

---

## Dependency Order

```
T1 (archive) ─────────────────────────────────────────────────────────┐
T2 (mutation fix) → T3 (parameterize) ────────────────────────────────┤
T4 (CCGate) → T5 (fixture script) → T6 (fixture test) ────────────────┤
T4 (CCGate) → T8 (differentiators) ───────────────────────────────────┤
T7 (contract examples doc) ────────────────────────────────────────────┤
T9 (PNG renders) ──────────────────────────────────────────────────────┤
T10 (self-review transcript) ──────────────────────────────────────────┤
                                                                        ↓
                                                                       T11
```

Execution order: T2 → T3 → T4 → T5 → T6 → T7 → T8 → T1 → T10 → T9 → T11
