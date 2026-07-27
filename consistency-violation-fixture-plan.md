# Consistency Violation Fixture — Plan

## Top-Level Overview

**Goal:** Demonstrate the `consistency_contract` enforcement path in the Open
Production validation layer by producing:

1. **`examples/generate_consistency_violation_fixture.py`** — a runnable script
   that creates a `production.json` + `audit.jsonl` pair where a
   `GenerationResult` is blocked because it is missing a `required_attribute`
   mandated by a `ConsistencyContract`.

2. **`tests/test_consistency_violation_fixture.py`** — a pytest that imports
   and re-exercises the same fixture logic in-process (no file I/O required),
   asserting gate failure + expected reason string.

The new gate (`ConsistencyContractGate`) lives **inside**
`src/validation/gates.py` alongside the three existing gates so that the test
module's single import is consistent with the project's existing pattern.

**Scope boundary:** No production service is being built; `src/service/` does
not exist and will not be created. The task is about adding one new gate class
and two new files (the example script and the pytest).

---

## Sub-Tasks

---

### Sub-Task 1 — Add `ConsistencyContractGate` to `src/validation/gates.py`

**Intent:**
Introduce the gate that enforces a `ConsistencyContract` against a
`GenerationResult`. Keeping it in the existing `gates.py` file follows the
project convention and keeps test imports identical to the existing pattern
(`from validation.gates import ConsistencyContractGate`).

**Domain model (pure Python dicts — no ORM, no dataclasses):**

```
ConsistencyContract = {
    "subject_id": str,                  # e.g. "char-elena"
    "required_attributes": list[str],   # e.g. ["red_scarf", "silver_locket"]
}

GenerationResult = {
    "generation_id": str,
    "subject_id": str,
    "attributes": list[str],            # attributes present in the output
}
```

**Gate logic (`ConsistencyContractGate.check`):**
- Accepts a `contract: dict` and a `result: dict`.
- Returns `(bool, str)` — identical API shape to `PublicationGate.check`.
- Pass: every `required_attribute` in `contract["required_attributes"]` is
  present in `result["attributes"]`.  Returns `(True, "ok")`.
- Fail: first missing attribute found → returns
  `(False, "missing required_attribute: <name>")`.

**Expected Outcomes:**
- `src/validation/gates.py` has a fourth class `ConsistencyContractGate`.
- `from validation.gates import ConsistencyContractGate` works from tests.

**Todo List:**
1. Append `ConsistencyContractGate` class to `src/validation/gates.py`.
2. Verify the file is syntactically valid (no import changes needed — pure
   Python, stdlib only).

**Relevant Context:**
- [`src/validation/gates.py`](src/validation/gates.py) — existing gate module.
- Pattern: `PublicationGate.check` returns `(bool, str)` — reuse this shape.

**Status:** `[ ] pending`

---

### Sub-Task 2 — Write `examples/generate_consistency_violation_fixture.py`

**Intent:**
Produce a self-documenting script that writes two files and prints the JSONL
audit trail to stdout.  The failure mode must be obvious from the audit trail
alone — no comments or explanations should be needed.

**Output files written by the script:**
- `examples/output/production.json` — the production document containing the
  `ConsistencyContract` and the `GenerationResult`.
- `examples/output/consistency_violation_audit.jsonl` — the audit trail, one
  JSON line per decision.

**Audit trail structure — three entries (minimum):**

| # | `gate_name` | `claim_id` | `decision_status` | `reason` |
|---|---|---|---|---|
| 1 | `consistency_contract_gate` | `gen-001` | `contract_pass` | `ok` *(verify subject_id matches)* |
| 2 | `consistency_contract_gate` | `gen-002` | `contract_violated` | `missing required_attribute: red_scarf` |
| 3 | `consistency_contract_gate` | `gen-002` | `production_blocked` | human-readable summary |

Entry 2 is the key one — it names the missing attribute explicitly so the JSONL
is self-explanatory.

**Script structure:**
1. `ROOT / SRC` path injection (same pattern as
   [`examples/generate_audit_fixture.py`](examples/generate_audit_fixture.py)).
2. `PRODUCTION_DOC` dict — inline definition of one `ConsistencyContract` +
   two `GenerationResult` objects (one passing, one failing).
3. Run the gate against each result, record decisions with `AuditRecorder`.
4. Write `production.json` (pretty-printed).
5. Print all JSONL lines to stdout.
6. `if __name__ == "__main__": sys.exit(main())`.

**Expected Outcomes:**
- Script runs with `python examples/generate_consistency_violation_fixture.py`.
- `examples/output/production.json` exists with the contract + results.
- `examples/output/consistency_violation_audit.jsonl` exists.
- Stdout shows exactly the JSONL entries, one per line.
- A reader of the output immediately understands why `gen-002` was blocked.

**Relevant Context:**
- [`examples/generate_audit_fixture.py`](examples/generate_audit_fixture.py) —
  exact style to follow (path injection, `AuditRecorder`, `main()` pattern).
- [`src/audit/recorder.py`](src/audit/recorder.py) — `AuditRecorder` API.
- [`src/validation/gates.py`](src/validation/gates.py) — gate to import.

**Status:** `[ ] pending`

---

### Sub-Task 3 — Write `tests/test_consistency_violation_fixture.py`

**Intent:**
Provide a pytest that verifies the `ConsistencyContractGate` blocks a
`GenerationResult` missing a `required_attribute` and that the reason string
explicitly names the missing attribute. This keeps the contract machine-checked
and raises the test count from 51 to 52.

**Test cases (one test function each):**

1. `test_gate_passes_complete_result` — a `GenerationResult` containing all
   `required_attributes` → gate returns `(True, "ok")`.
2. `test_gate_blocks_missing_attribute` — a `GenerationResult` missing
   `"red_scarf"` → gate returns `(False, ...)` and reason contains
   `"red_scarf"`.
3. `test_gate_reason_names_missing_attribute` — same missing result; asserts
   the reason string starts with `"missing required_attribute:"`.

**Fixtures (module-level, using `@pytest.fixture`):**
- `contract` — the `ConsistencyContract` dict for `char-elena`, requiring
  `["red_scarf", "silver_locket"]`.
- `passing_result` — `GenerationResult` for `gen-001` that includes both
  required attributes.
- `failing_result` — `GenerationResult` for `gen-002` that omits `"red_scarf"`.

**Expected Outcomes:**
- `pytest tests/test_consistency_violation_fixture.py` passes (3/3).
- Total suite passes at 52/52 (or better).
- No existing tests are modified.

**Relevant Context:**
- [`tests/test_gates.py`](tests/test_gates.py) — fixture + test style to match.
- [`tests/conftest.py`](tests/conftest.py) — `src` already on `pythonpath`;
  no changes to conftest needed.

**Status:** `[ ] pending`

---

## Notes for Implementation

- `src/service/production_service.py` does **not** exist; the task description
  refers to the *concept* of a production service, not an existing file. The
  gate lives in `gates.py` and the "service" is demonstrated by the example
  script.
- The `consistency_contract` domain model (from `open-production-plan.md`
  §12) uses `required_attributes` (list). Our gate implementation aligns with
  that schema.
- All three files are stdlib-only (no new dependencies).
