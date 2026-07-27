# Bob Session 1 — Codebase Exploration

**Goal:** Bob reads the existing Open Production scheduler code and identifies branch coverage gaps in the dispatcher loop. This is the *exploration* session in the "explore → build → validate" Bob usage arc.

**Output:** A refactor proposal document. No code changes applied during this session.

---

## Setup

1. Open **IBM Bob IDE** (or Bob Shell if you prefer CLI).
2. Point Bob at the PDT source directory: `D:\openclaw\pdt\`
3. Tell Bob this session is **read-only** — analysis only, no file edits.

---

## Prompt to give Bob

> I need you to analyze the file `D:\openclaw\pdt\src\coordinator\scheduler.py` (about 33KB) and produce a refactor proposal.
>
> **Context:** This is a multi-agent scheduler that dispatches research-writing tasks. It has a 6-phase loop (Acquire → Detect → Plan → Dispatch → Commit → Release). I'm concerned about branch coverage gaps in the dispatcher loop and want to harden the failure paths.
>
> **What I want from you:**
> 1. Read the file end-to-end.
> 2. Identify every `if`/`elif`/`else` branch in the dispatcher.
> 3. For each branch, classify:
>    - **Tested** — clear unit test exists (check `tests/`)
>    - **Partially tested** — branch hit but error path not
>    - **Untested** — branch never hit by a test
>    - **Inherently untestable** — depends on wall-clock time, network, etc.
> 4. Rank the gaps by severity (production impact if branch fails).
> 5. Propose a refactor: small, focused, doesn't change semantics. The refactor should make the remaining gaps easier to test (e.g., extract a function, inject a dependency).
>
> **Output format:** A markdown refactor proposal with:
> - Phase table (each branch with classification)
> - Top 3 gaps by severity
> - Proposed refactor (file, function signatures, what changes)
> - New tests that would close the top 3 gaps
>
> **Constraints:**
> - Do not modify the file. Read-only.
> - Do not propose a rewrite. The scheduler is working; we just want to harden it.
> - Be concrete. Cite line numbers and function names.

---

## Save the transcript

Copy the entire Bob session (your prompts + Bob's responses) into:

`D:\IBM Project\Open_Production\bob-sessions\01-codebase-exploration\transcript.md`

Add this header at the top of the file:

```markdown
# Bob Session 1 — Codebase Exploration

**Date:** 2026-07-27
**Bob session ID:** (paste from Bob's session info if available)
**Goal:** Identify branch coverage gaps in `scheduler.py` and propose a hardening refactor.
**Outcome:** (paste the refactor proposal inline below, or link to the proposal file)

---

## Transcript

(paste session here)
```

---

## Done when

- [ ] Bob has read the full file (it should cite specific line numbers and function names)
- [ ] The proposal has a phase table + top 3 gaps + refactor + new tests
- [ ] The transcript is saved to `bob-sessions/01-codebase-exploration/transcript.md`
- [ ] The proposal is concise (≤ 1 page)

---

## What Boris does with the output

I review the proposal for soundness, then we either:
- **(a)** Apply the refactor in Bob session 2's continuation, OR
- **(b)** Set it aside as a documented improvement for after submission.

The transcript itself is the audit trail — keep it raw even if you don't apply the refactor.
