# ConsistencyContract — Worked Examples

> Reference document for the `ConsistencyContractGate.check()` implementation
> (`src/validation/gates.py`). Each example pairs a YAML contract with a YAML
> GenerationResult and shows the exact `(ok: bool, reason: str)` tuple the gate returns.
>
> All subject IDs follow schema naming conventions: `char-NNN`, `env-NNN`, `gen-NNN`.

---

## Example 1 — PASS (all required attributes present, nothing prohibited)

**Scenario:** Character "Nadia" requires a white beret and silver earrings.
The generation includes both. No prohibited attributes are declared.

```yaml
# ConsistencyContract
subject_id: char-nadia
required_attributes:
  - white_beret
  - silver_earrings
prohibited_attributes: []
variance_tolerance: 0.15
```

```yaml
# GenerationResult
id: gen-001
subject_id: char-nadia
attributes:
  - white_beret
  - silver_earrings
  - grey_coat
```

**Verdict: ✅ PASS**

The gate iterates `required_attributes` in order. `white_beret` is in the result's attribute
set; `silver_earrings` is also present. The prohibited list is empty, so no further checks
are needed. The gate returns immediately after finding no violations.

---

## Example 2 — FAIL (missing required attribute)

**Scenario:** Same character "Nadia". The generation omits the white beret — a signature
visual anchor — while retaining the silver earrings.

```yaml
# ConsistencyContract
subject_id: char-nadia
required_attributes:
  - white_beret
  - silver_earrings
prohibited_attributes: []
variance_tolerance: 0.15
```

```yaml
# GenerationResult
id: gen-002
subject_id: char-nadia
attributes:
  - silver_earrings
  - dark_coat
```

**Verdict: ❌ FAIL**

`white_beret` is the first required attribute in the list. It is absent from the result.
Because `variance_tolerance` is 0.15 (above the 0.10 tight-tolerance threshold), the gate
uses the standard missing-attribute message rather than the partial-match message.
The gate stops immediately after the first missing attribute — it does not check
`silver_earrings` or the prohibited list.

---

## Example 3 — FAIL (prohibited attribute present on a character)

**Scenario:** Character "Riku" is a mine worker. His ConsistencyContract explicitly
prohibits `headlamp` on his character (the headlamp belongs to a separate equipment prop,
not to Riku's personal visual signature). A generation adds a headlamp directly to his
character attributes.

```yaml
# ConsistencyContract  (character, not environment)
subject_id: char-riku
required_attributes:
  - work_gloves
  - safety_vest
prohibited_attributes:
  - headlamp
variance_tolerance: 0.15
```

```yaml
# GenerationResult
id: gen-003
subject_id: char-riku
attributes:
  - work_gloves
  - safety_vest
  - headlamp
```

**Verdict: ❌ FAIL**

All required attributes (`work_gloves`, `safety_vest`) are present, so the required-attribute
loop completes without stopping. The gate then checks the prohibited list. `headlamp` is in
the result's attribute set, so the gate halts and returns a prohibited-attribute violation.
This is a character-level contract — the prohibition is about Riku's visual identity, not
about whether a headlamp exists somewhere in the environment.

---

## Example 4 — FAIL (tight tolerance rejects partial / synonym match)

**Scenario:** Character "Nadia" requires `short_hair`. The generation provides `hair_cropped`
— a semantically close synonym — but the contract's `variance_tolerance` is set to `0.05`,
meaning partial or synonym matches are treated as misses.

```yaml
# ConsistencyContract
subject_id: char-nadia
required_attributes:
  - short_hair
prohibited_attributes: []
variance_tolerance: 0.05
```

```yaml
# GenerationResult
id: gen-004
subject_id: char-nadia
attributes:
  - hair_cropped
  - silver_earrings
```

**Verdict: ❌ FAIL**

The gate performs exact string matching against the attribute set. `short_hair` is not in
`{"hair_cropped", "silver_earrings"}` — the synonym `hair_cropped` does not satisfy it.
Because `variance_tolerance` is 0.05 (≤ 0.10), the gate includes a tight-tolerance
diagnostic in the reason string, explicitly naming the attribute and the tolerance so the
caller understands why a near-match was rejected rather than silently missing context.

---

## Example 5 — PASS (empty contract, only subject_id)

**Scenario:** An environment "Empty Stage" has a contract with no required or prohibited
attributes — only a `subject_id`. Any generation passes.

```yaml
# ConsistencyContract
subject_id: env-empty-stage
required_attributes: []
prohibited_attributes: []
variance_tolerance: 0.15
```

```yaml
# GenerationResult
id: gen-005
subject_id: env-empty-stage
attributes:
  - neutral_backdrop
  - soft_lighting
```

**Verdict: ✅ PASS**

The `required_attributes` list is empty — the required-attribute loop never executes. The
`prohibited_attributes` list is also empty — the prohibited loop never executes. The gate
falls through to the final `return (True, "ok")`. An empty contract is valid and useful for
subjects whose visual identity has not yet been specified.

---

## Gate Return Value Reference

| Scenario | `ok` | `reason` |
|---|---|---|
| All required present, nothing prohibited | `True` | `"ok"` |
| Missing required attribute (standard tolerance) | `False` | `"missing required_attribute: <attr>"` |
| Missing required attribute (tight tolerance ≤ 0.10) | `False` | `"missing required_attribute: <attr> (variance_tolerance=<tol>; partial match '<attr>' rejected)"` |
| Prohibited attribute present | `False` | `"prohibited_attribute present: <attr>"` |
| Empty contract | `True` | `"ok"` |

> **Stop-fast guarantee:** the gate returns on the *first* violation found.
> It does not accumulate multiple failures into a list. If both a required attribute is
> missing and a prohibited attribute is present, only the missing-required reason is returned
> (required attributes are checked first).

---

*Document generated 2026-07-27 · cites `src/validation/gates.py:ConsistencyContractGate.check()`*
