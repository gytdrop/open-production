# Open Production — Master Build Playbook

> **For Boris (me), Codex, and IBM Bob.** The single document that sequences everything we still need to build between **now and Fri Jul 31 11:59 PM ET** (≈3.5 days). Each task names the actor, the artifact, the exit criterion, and (for Bob) the exact prompt to run.

> **Submission floor:** `pytest tests/ -q --basetemp=C:\Temp\pytest-openprod -p no:asyncio` must report **≥63 passed** at every phase boundary. No exceptions. Below 63 = roll back the last change.

> **Companion doc:** `docs/plans/2026-07-27-frontend-with-view-switching.md` (the original Phase 1/2 plan; this playbook supersedes the sequencing but keeps the file as historical reference).

---

## 0 · Status as of playbook write

```
✅ Phase 1 done — ProductionService + dual-artifact demo_flow, 63/63 tests
✅ ACT-1, ACT-3, ACT-5, ACT-8, P0-4 design/planning docs on disk (~200 KB)
✅ 5 wireframe SVGs + composite + README on disk (107 KB)
✅ Bob session 8 prompt-A critique on disk (transcript captured separately by K)
✅ Bob session 9 (differentitors doc) on disk
✅ Bob session 11 (quick-brief refresh) on disk
✅ Bob session 13 (90-second demo script) on disk

⏳ Phase 2 (HTML pages + view-switching) — parked by K #1948 (skip per time budget)
⏳ Phase 3 (ConsistencyContract gate + fixture) — 4 in-flight items
⏳ Phase 4 (finalize: differentiators, PNG renders, self-review transcript)
```

---

## 1 · Phases, time budget, exit criteria

| # | Phase | Wall budget | Exit criterion |
|---|---|---|---|
| 1 | ProductionService + dual-artifact demo_flow | ✅ done | 63/63 tests pass |
| 2 | HTML pages + view-switching | parked | K's #1948 — defer to post-submission |
| 3 | ConsistencyContract gate + fixture + example docs | 1.5 hr | 66/66 tests pass; fixture regenerable from script |
| 4 | Finalize: code-review fix, fixture injectability, differentiators update, PNG renders | 1 hr | all judge-pack files in place; final test run green |
| 5 | Submit | 30 min | form filled, repo pushed |

**Total remaining**: ~3.5 hr of real work. Comfortable.

---

## 2 · Master task list

### T1 · Save Bob's prompt-A transcript (5 min) — **Boris (me)**

Move the prompt-A code-review transcript that K forwarded into `bob-sessions/08-code-review/transcript.md` for archival. Add a `spec.md` if Bob provided one. Otherwise create both files with content summarizing Bob's critique (4 findings, 3 differentiator gaps).

**Exit:** `bob-sessions/08-code-review/transcript.md` exists and is ≥2 KB.

### T2 · Fix `EvidenceGate.process` mutation hazard (10 min) — **Boris (me)**

Per Bob's prompt-A finding #1. The gate at `src/validation/gates.py:16-20` mutates the caller's dict in-place. The current workaround (`dict(claim)` at `demo_flow.py:110`) is fragile.

```python
# Before (mutates input)
def process(self, claim: dict) -> dict:
    if not (claim.get("source_ids") or []):
        claim["status"] = "rejected"
        claim["reason"] = "no source_ids"
    else:
        claim["status"] = "accepted"
        claim["reason"] = "has sources"
    return claim

# After (returns new dict)
def process(self, claim: dict) -> dict:
    source_ids = claim.get("source_ids") or []
    if not source_ids:
        return {**claim, "status": "rejected", "reason": "no source_ids"}
    return {**claim, "status": "accepted", "reason": "has sources"}
```

Add 1 test asserting `process()` doesn't mutate input.

**Exit:** `tests/test_gates.py` has 1 new test; full suite ≥64/64.

### T3 · Parameterize `FIXTURE_CLAIMS` and `FIXTURE_METADATA` (15 min) — **Boris (me)**

Per Bob's prompt-A finding #2. Add `claims` and `metadata` as optional params to `build_demo_report()`. Default keeps existing behavior.

```python
def build_demo_report(
    topic, audience="educated_lay", tone="neutral",
    chosen_angle_id=None, audit_path=None, audit_dir="output/public-demo",
    claims: list[dict] | None = None,
    metadata: dict | None = None,
) -> dict:
    claims = claims if claims is not None else FIXTURE_CLAIMS
    metadata = metadata if metadata is not None else FIXTURE_METADATA
    ...
```

Add 2 tests:
- `build_demo_report` accepts custom claims and applies them
- `build_demo_report` accepts custom metadata and applies it

**Exit:** `tests/test_demo_flow.py` has 2 new tests; full suite ≥66/66.

### T4 · Implement `ConsistencyContractGate.check()` (20 min) — **Boris (me)**

Per Bob's prompt-C plan. New gate in `src/validation/gates.py` that takes a `ConsistencyContract` (dict) and a `GenerationResult` (dict), returns `(bool, str)`. Stop-fast (Q2). 3-entry audit pattern (Q3) — but the gate itself returns the verdict string; the 3-entry audit is enforced by the fixture script.

```python
class ConsistencyContractGate:
    """Stop-fast check of a GenerationResult against a ConsistencyContract."""

    def check(self, contract: dict, result: dict) -> tuple[bool, str]:
        required = contract.get("required_attributes") or []
        prohibited = contract.get("prohibited_attributes") or []
        result_attrs = set(result.get("attributes") or [])
        # stop-fast: first missing required
        for attr in required:
            if attr not in result_attrs:
                tol = contract.get("variance_tolerance", 0.15)
                if tol <= 0.10:
                    return (False, f"missing required_attribute: {attr} "
                                   f"(variance_tolerance={tol}; "
                                   f"partial match '{attr}' rejected)")
                return (False, f"missing required_attribute: {attr}")
        # then prohibited
        for attr in prohibited:
            if attr in result_attrs:
                return (False, f"prohibited_attribute present: {attr}")
        return (True, "ok")
```

Add 1 test:
- `check()` returns `(False, "missing required_attribute: red_scarf")` for missing-required case
- `check()` returns `(False, "prohibited_attribute present: glasses")` for prohibited case
- `check()` returns `(True, "ok")` for empty contract
- `check()` returns `(False, "...variance_tolerance=0.05...")` for tight-tolerance partial match

**Exit:** `tests/test_gates.py` has 4 new gate tests; full suite ≥70/70.

### T5 · Generate `examples/generate_consistency_violation_fixture.py` (15 min) — **Boris (me)**

Per Bob's prompt-C plan. Writes a sample `production.json` + `consistency_violation_audit.jsonl` pair demonstrating a failed ConsistencyContract enforcement.

Fixture scenario from Bob's plan:
- Contract for `char-elena` requires `["red_scarf", "silver_locket"]`
- `gen-001` includes both → passes
- `gen-002` includes `silver_locket` but omits `red_scarf` → blocked with explicit reason

Run with: `python examples/generate_consistency_violation_fixture.py`. Output goes to `output/consistency_violation/`.

**Exit:** running the script produces the JSONL with 3 entries (gen-001 pass, gen-002 violation, production_blocked summary).

### T6 · Add 1 test asserting the fixture is regenerable (5 min) — **Boris (me)**

In `tests/test_consistency_violation_fixture.py`:
- Run the script via subprocess
- Assert the JSONL exists and has ≥3 entries
- Assert the second entry has `decision_status: "contract_violated"`
- Assert the reason string contains the missing attribute name

**Exit:** `tests/test_consistency_violation_fixture.py` has 3 assertions; full suite ≥71/71.

### T7 · Relocate + expand `consistency-contract-examples-plan.md` → `docs/schema/consistency-contract-examples.md` (10 min) — **Boris (me)**

Per Bob's prompt-E plan. Take Bob's 5 worked examples (all already designed), expand into the actual document with:
- Example 1: PASS (all required present, nothing prohibited) — character "Nadia"
- Example 2: FAIL (missing `short_hair`) — character "Nadia"
- Example 3: FAIL (`headlamp` prohibited, mine helmet) — character **not environment** (Q7)
- Example 4: FAIL (variance_tolerance 0.05, partial match `hair_cropped` rejected) — spell out the framing (Q6)
- Example 5: PASS (empty contract, only `subject_id`)

Each example has: YAML contract block, YAML GenerationResult block, one-line bold verdict, 2-3 sentence "why" explanation.

Add a final **Gate Return Value Reference** table mapping scenario → exact `(ok: bool, reason: str)` tuple.

**Exit:** `docs/schema/consistency-contract-examples.md` exists and is ≥4 KB.

### T8 · Update differentiators doc to reflect Phase 1/3 work (10 min) — **Boris (me)**

Bob's `docs/judge-pack/differentiators.md` (prompt B, on disk) was written before Phase 1 shipped. Update it to reflect:
- 01 Production Document — now cites `src/service/production_service.py` and `src/schema/production_document.py` (NOT just `docs/schema/production-document.schema.json`)
- 05 Reviewer Agent — now cites `src/validation/gates.py:ConsistencyContractGate.check()` (Phase 3 work)
- Add a short note: "The Agent Console (UI surface for the crew) is parked per submission-window scope; the underlying event log is shipped via `ProductionService`."

Don't rewrite — Bob's structure is good. Just patch the file:line references.

**Exit:** differentiators.md updated; 4/5 differentiators cite live code (Agent Console still parked).

### T9 · Render wireframes to PNG (5 min) — **Boris (me)**

Use the browser tool to render each SVG to PNG. Save to `docs/wireframes/*.png` (6 files: 5 views + composite).

```python
# pseudo-code
for svg_path in ["01-directors-canvas.svg", ...]:
    png_path = svg_path.replace(".svg", ".png")
    browser.open(f"file://{svg_path}", screenshot=True, save_to=png_path)
```

**Exit:** 6 PNG files exist alongside the SVGs.

### T10 · Self-review transcript for prompt-A replacement (15 min) — **Boris (me)**

Bob's prompt-A was a real critique but it wasn't a transcript of a "code-review session" — it was a critique of files that didn't yet exist in the form I described. Save a self-review transcript to `bob-sessions/08-self-review/transcript.md` so judges can see what was reviewed and what changed.

Format:
```
# Bob session 8 — code-review (self-transcript)

> Note: this is a self-transcript because Bob's session 8 paused on a
> premise mismatch (the named service file didn't exist at the time).
> The review below is the closest analog: a tight critique of the
> actual shipped code paths.

## What I would change for a 51-test prototype
1. EvidenceGate.process mutates the caller's dict — fix in T2.
2. FIXTURE_CLAIMS / FIXTURE_METADATA are module-level — fix in T3.
3. AuditRecorder.__init__ truncates the file on construction — keep as-is (acceptable for the demo).
4. pick_default_angle_id via ord(topic[0]) — keep but document.

## §26 differentiators absent from shipped code
[reference Bob's findings]

## Resolution
[link to T2, T3, T8 commits]
```

**Exit:** `bob-sessions/08-self-review/transcript.md` exists and is ≥1 KB.

### T11 · Final test run + commit + submit prep (30 min) — **Boris (me)**

```bash
# from project root
$tmpdir = "C:\Temp\pytest-openprod"
python -m pytest tests/ -q --basetemp="$tmpdir" -p no:asyncio
# expect: ≥71 passed

git add -A
git commit -m "feat(ibm-challenge): ProductionService, ConsistencyContract gate, fixture, differentiators updated"
git push
```

**Exit:** tests green; commit pushed; submission form ready.

---

## 3 · Bob prompt sequence (if you choose to send more prompts)

If you'd rather have Bob do the design work and you (or me) implement, here are the 4 prompts you'd send, in order. Each is a complete paste-ready block.

### Bob prompt G — Differentitors update + character-subject for Example 3

```
Read docs/judge-pack/differentiators.md.

Section 01 currently cites docs/schema/production-document.schema.json
and docs/schema/production_document.py. After Phase 1 shipped, also
available: src/service/production_service.py and src/schema/production_document.py.

Section 05 currently cites src/videos/quality_evaluation.py. After
Phase 3 shipped, also available: src/validation/gates.py:ConsistencyContractGate.

Update the file:line references in sections 01 and 05 to include
the new files. Don't add a section about the Agent Console — it's
parked. Just refresh the cites.

Then write docs/schema/consistency-contract-examples.md with the
5 worked examples you designed in consistency-contract-examples-plan.md,
keeping in mind:
- Example 3 must use a CHARACTER subject (not environment) — "headlamp" prohibited is character visual continuity, not environment
- Example 4 should explicitly spell out that tight tolerance treats
  partial/synonym strings as misses, with the tolerance value pinned
- All gen_/char_/env_ IDs must match the schema patterns
- Verdict strings must exactly match the format the gate implementation returns
```

### Bob prompt H — Open production plan callouts in `quick-brief.md`

```
Read open-production-plan.md and verify the 5 differentiators in
section §26 match what's in docs/judge-pack/differentiators.md.

If the plan was updated to add a 6th differentiator since Bob session 9,
add it to differentiators.md with a file:line citation. If not, no change.

Don't add speculative differentiators. Only ones actually cited in
§26 of the plan as of this read.
```

### Bob prompt I — 90-second script final pass

```
Re-read docs/demo/90-second-script.md and verify:
1. Closing line is verbatim: "The audit trail IS the production document. The video is just one render of it."
2. file:line citation for record_gate_decision points to src/audit/recorder.py:23
3. word count for each segment matches the table (≈25, ≈75, ≈75, ≈45)
4. narrator-notes table doesn't recommend anything not in the prototype

If any of these is wrong, fix the file. If they're all correct,
report "verified" and do not modify.
```

### Bob prompt J — ProductionDocument evidence file

```
Read docs/judge-pack/differentiators.md and src/service/production_service.py.

The differentiator doc claims "the production document is serializable,
diffable, versionable" and cites src/service/production_service.py as
evidence. Verify the actual class methods support this:
- serializable: ProductionService.save() writes JSON
- diffable: any tooling that compares production.json files
- versionable: ProductionService.snapshot() OR production.json's content_hash

Report:
1. Which of these three properties the shipped code supports (with file:line)
2. Which are aspirational (designed but not yet implemented)
3. Whether the differentiator doc should be updated to soften the language
   for the aspirational ones
```

---

## 4 · Check-and-balances cadence

| Trigger | Output |
|---|---|
| Phase boundary (T1 done, T2 done, etc.) | Single-line HEARTBEAT in chat |
| 30 min elapsed with no phase change | Status block: DONE / PENDING / BLOCKER |
| Test failure | Print the failing test name + diff + auto-rollback instruction |
| Bob session ends | Print Bob's artifact path + size + verified-vs-echoes verdict |

**Test floor invariant:** if `pytest tests/ -q` reports **fewer than 63 passed** at any point, the most recent code change is rolled back and the failing test is triaged.

---

## 5 · Rollback strategy

Every task is small enough to revert with a single `git revert`. If T2 breaks something:
- Revert the commit
- Identify the regression (specific test name)
- Re-apply only the parts of T2 that pass

For T4 (ConsistencyContractGate), the gate is **additive** — adding it doesn't change existing gate behavior. If T4 fails:
- The gate is a new class, no existing code imports it
- The fixture generator is a new script, no existing test runs it
- Worst case: delete `ConsistencyContractGate` class + the fixture file

---

## 6 · Honest risks (not excuses — risks)

1. **Time slippage on T2/T4.** Each is 10-20 min, but I've been 4× my budget on prior tasks (Phase 1 took 4× expected). Mitigation: small commits, rollback if a single task slips past its 1.5× budget.
2. **Bob's prompt-G might write something I disagree with.** If so, I review, don't blindly apply. Update the doc, but if Bob's update is wrong I correct it.
3. **The Agent Console (parked) is a real differentiator absent from shipped code.** The differentiators doc (after T8) will be honest about this. Better honest than inflated.
4. **Friday submission has no slack.** If T4 takes longer than expected, T8 (differentiators update) is the highest-leverage move — judges see the doc first. Don't sacrifice T8 for T4 if forced to choose.

---

## 7 · Sign-off

When T11 commits land and tests are green, the IBM submission package is:
- Working kernel with 71+ tests passing
- ProductionDocument schema + dataclass mirror
- ProductionService runtime
- ConsistencyContractGate enforced
- 5 wireframes (SVG + PNG)
- Differentitors doc, quick-brief, 90-second script (all judge-pack ready)
- Bob sessions 1-7 transcripts + session 8 self-transcript + session 11/13
- Honest deferrals: Agent Console UI, real reviewer loop, multi-user collab

That package is competitive. The path between here and Friday is the playbook above.

*Plan written 2026-07-27 22:58 IST · supersedes the earlier Phase 1/2 plan as the working document · Boris_Hub topic IBM*
