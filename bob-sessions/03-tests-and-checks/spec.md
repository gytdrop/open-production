# Bob Session 3 — Tests and Gate-Validation Checks

**Goal:** Bob authors and runs the test suite for the creative_reframing agent and the gate-validation suite for the Open Production pipeline. This is the *validation* session in the "explore → build → validate" Bob usage arc.

**Output:** A test file, a check log, and a saved transcript.

---

## Why this matters

A submission with code but no tests signals "we wrote code, hope it works." A submission with code + a tested-by-Bob audit trail signals "we used Bob end-to-end, the way professional teams do." This session is the difference.

---

## Setup

1. Open **IBM Bob IDE**.
2. Point Bob at the working directory: `D:\IBM Project\Open_Production\`.
3. Two deliverables:
   - `tests/test_creative_reframing.py` — already drafted in Session 2; Bob should now **review and harden** it.
   - `tests/test_gates.py` — **new** — gate-validation suite for the publication pipeline.
   - `bob-sessions/03-tests-and-checks/check-log.md` — the run output.

---

## Part A — Harden the creative_reframing tests (paste this prompt)

> Open Production's `tests/test_creative_reframing.py` was written in Bob session 2. Please:
>
> 1. Read the file.
> 2. Verify it covers:
>    - Happy path (mocked LLM returns valid JSON)
>    - Malformed JSON retry path
>    - Missing-context safety
>    - Fallback when LLM fails twice
>    - All three angles have distinct `questions_to_address`
> 3. If any are missing or weak, **add tests** (don't rewrite — only add).
> 4. Run the test suite. Capture the full pytest output (including pass/fail counts).
> 5. If any test fails, fix the production code (in `src/agents/creative_reframing.py`), not the test.
> 6. Re-run until all tests pass.
>
> **Output:** Updated test file, full pytest log, and a 3-line summary describing what you added and why.

---

## Part B — Write the gate-validation suite (paste this prompt)

> Open Production runs three validation gates on every research output:
>
> - **evidence_gate** (`src/validation/evidence_gate.py`) — every claim must cite a source.
> - **consistency_gate** (`src/validation/consistency_gate.py`) — surfaces contradictions; doesn't silently overwrite.
> - **publication_gate** (in `src/publication/`) — refuses to publish with incomplete metadata.
>
> Please write `tests/test_gates.py` that tests:
>
> 1. **Evidence gate:**
>    - Rejects a claim with no citation
>    - Accepts a claim with at least one source ID
>    - Logs rejections in a way the audit trail can consume
> 2. **Consistency gate:**
>    - Detects two claims about the same fact with conflicting conclusions
>    - Surfaces both (does not pick a winner)
>    - Empty claim set is not an error
> 3. **Publication gate:**
>    - Refuses a document missing DOI
>    - Refuses a document missing author attribution
>    - Accepts a complete document
>    - Returns a clear error message (not an exception) when refusing
>
> **Constraints:**
> - Use pytest fixtures to share fixture claim sets across tests.
> - Mock external APIs (PubMed, OpenAlex, etc.) — do not hit live services in tests.
> - Do not modify the production code. If a test reveals a bug, log it as a "Bob flagged:" comment in the test file; we will fix it after submission.
>
> **Output:** The new test file, the full pytest run output (passes/fails), and a 3-line summary describing what you wrote.

---

## Save the transcript and check log

Save the session into:

`D:\IBM Project\Open_Production\bob-sessions\03-tests-and-checks\transcript.md`

Save the pytest output into:

`D:\IBM Project\Open_Production\bob-sessions\03-tests-and-checks\check-log.md`

Both files need a header. For the transcript:

```markdown
# Bob Session 3 — Tests and Gate-Validation Checks

**Date:** 2026-07-28
**Goal:** Harden creative_reframing tests; write gate-validation suite.
**Outcome:** (paste 3-line summary inline)

---

## Transcript

(paste session here)
```

For the check-log:

```markdown
# Check Log — Open Production Test Run

**Date:** 2026-07-28
**Run by:** IBM Bob
**Suite:** tests/test_creative_reframing.py + tests/test_gates.py

---

## Part A — creative_reframing tests

(paste pytest output)

## Part B — gate-validation suite

(paste pytest output)

---

## Summary

- Tests added: (N)
- Tests passed: (N)
- Tests failed: (N)
- Bugs flagged: (list)
```

---

## Done when

- [ ] `tests/test_creative_reframing.py` hardened (no broken tests)
- [ ] `tests/test_gates.py` written and runs
- [ ] All tests pass (or flagged bugs are documented)
- [ ] Transcript saved
- [ ] Check log saved
- [ ] Boris reviews

---

## What Boris does with the output

I review for:
- Test quality (do they actually test the right thing, or are they tautological?)
- Bug flags (Bob may have flagged real bugs we missed in PDT)
- Whether the test structure (fixtures, mocks) is sane

If anything is wrong, I flag it. If it's good, we have a complete test suite that proves Open Production works. This becomes the "Technical Execution" evidence in the submission.

---

## Bob coin budget

This session will burn more Bobcoins than the previous two because it generates code. Estimate: ~10–15 Bobcoins. After session 3 you should still have 5–10 coins for any quick fixes during video recording / submission.