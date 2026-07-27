# Consistency Contract Examples — Plan

## Top-Level Overview

**Goal:** Write `docs/schema/consistency-contract-examples.md` — five worked
examples of ConsistencyContract enforcement, each showing a contract, a
GenerationResult, and a one-line gate verdict.

The document also serves as the **fixture spec** for
`src/validation/gates.py:ConsistencyContractGate.consistency_contract_check()`,
so the contract fields, attribute names, and verdict strings in this document
must exactly match what the gate implementation will check.

**Sources of truth consulted:**
- [`docs/schema/production-document.schema.json`](docs/schema/production-document.schema.json)
  — canonical field names, types, and descriptions for `ConsistencyContract`
  and `GenerationResult`.
- [`docs/schema/production_document.py`](docs/schema/production_document.py)
  — Python mirror; confirms `variance_tolerance` default = `0.15`, all fields
  are optional except `subject_id`.

---

## Sub-Tasks

### Sub-Task 1 — Author `docs/schema/consistency-contract-examples.md`

**Intent:**
Produce a single Markdown file that a developer or reviewer can read cold and
immediately understand what the gate checks, why each example passes or fails,
and what string to expect in `reason`.

**Five examples and their design rationale:**

| # | Title | Key mechanic exercised | Expected verdict |
|---|---|---|---|
| 1 | All attributes present, nothing prohibited | Baseline pass | `PASS` |
| 2 | Missing `short_hair` in attributes | `required_attributes` miss | `FAIL` |
| 3 | `glasses` appears in output and is prohibited | `prohibited_attributes` hit | `FAIL` |
| 4 | Tight `variance_tolerance: 0.05` with partial attribute match | tolerance edge case | `FAIL — flagged` |
| 5 | Completely empty contract (only `subject_id`) | empty lists → nothing to check | `PASS` |

**Structure per example:**
1. **Heading** — `### Example N — <VERDICT>: <one-line description>`
2. **Contract block** — YAML (readable, compact)
3. **GenerationResult block** — YAML, includes `reviewer_verdict` stub showing
   what the gate would write back
4. **Gate verdict** — single bold sentence, written to match the exact `reason`
   string the gate implementation must return
5. **Why** — two-to-three sentence explanation of which contract field was
   triggered and why

**Key field mappings from schema:**
- `ConsistencyContract.required_attributes` — `list[str]`; gate checks each
  string is present in the generation's attribute set.
- `ConsistencyContract.prohibited_attributes` — `list[str]`; gate checks none
  are present.
- `ConsistencyContract.variance_tolerance` — `float 0.0–1.0`, default `0.15`;
  a value ≤ 0.05 means the gate flags any attribute not an exact string match
  (partial / synonym match is treated as a miss).
- `GenerationResult.reviewer_verdict` — free-form `dict`; the gate writes its
  decision here so the audit trail can reference it.
- `GenerationResult.id` — schema pattern `^gen_[A-Za-z0-9_-]{4,}$`

**Tolerance interpretation for Example 4:**
`variance_tolerance` is a float signal, not a fuzzy-match engine. The gate
implementation will use it as a *strictness mode*: when `variance_tolerance ≤
0.10`, any attribute value that is a partial/synonym of a required attribute
(e.g. `"hair_short"` vs `"short_hair"`) is treated as a miss. Example 4
demonstrates this by supplying `"hair_cropped"` where `"short_hair"` is
required under tolerance `0.05` — the gate must flag it.

**Expected Outcomes:**
- File exists at `docs/schema/consistency-contract-examples.md`.
- Five examples, each with contract YAML, GenerationResult YAML, and verdict.
- Verdict strings in the document match the exact format the gate returns:
  `"missing required_attribute: <name>"`,
  `"prohibited_attribute present: <name>"`,
  `"missing required_attribute: short_hair (variance_tolerance=0.05; partial match 'hair_cropped' rejected)"`,
  `"ok"`.
- The intro section names the file as the fixture spec for
  `ConsistencyContractGate.consistency_contract_check()`.

**Todo List:**
1. Write the file header (title, schema version ref, role as fixture spec).
2. Write Example 1 — PASS.
3. Write Example 2 — FAIL missing required_attribute.
4. Write Example 3 — FAIL prohibited_attribute present.
5. Write Example 4 — FAIL tight variance_tolerance, partial attribute rejected.
6. Write Example 5 — PASS empty contract.
7. Add a closing **Gate Return Value Reference** table mapping scenario → exact
   `(ok: bool, reason: str)` tuple the gate implementation must return.

**Relevant Context:**
- [`docs/schema/production-document.schema.json`](docs/schema/production-document.schema.json)
  lines 176–189 — `ConsistencyContract` definition.
- [`docs/schema/production-document.schema.json`](docs/schema/production-document.schema.json)
  lines 308–325 — `GenerationResult` definition.
- [`docs/schema/production_document.py`](docs/schema/production_document.py)
  lines 100–108 — Python `ConsistencyContract` dataclass (confirms defaults).
- [`src/validation/gates.py`](src/validation/gates.py) — existing gate module;
  new gate will follow same `(bool, str)` return convention as `PublicationGate`.

**Status:** `[ ] pending`

---

## Notes for Implementation

- Use YAML for contracts and results (more readable than JSON for the audience
  consuming this as a spec document).
- All `gen_` IDs must match the schema pattern `^gen_[A-Za-z0-9_-]{4,}$`.
- All `char_` / `env_` IDs must match their respective patterns.
- The `reviewer_verdict` in each `GenerationResult` should show what the gate
  writes back (even as a stub), so readers see the full feedback loop.
- Do NOT invent new fields beyond those in the schema.
