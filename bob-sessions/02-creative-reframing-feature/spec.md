# Bob Session 2 — Build the Creative-Reframing Feature

**Goal:** Bob designs and implements a new agent that takes a topic and returns three creative angles on it. This is the *implementation* session in the "explore → build → validate" Bob usage arc.

**Output:** A working `creative_reframing.py` module, integrated into the pipeline, plus a saved transcript of the build session.

---

## Why this module

The IBM challenge rubric asks: *"How can AI act as a creative partner rather than simply a content generator?"* Open Production's answer is **creative reframing**: before writing, the system proposes three angles on the topic and lets the user pick one. This is the differentiator that takes Open Production from "AI that writes" to "AI as creative partner."

---

## Setup

1. Open **IBM Bob IDE**.
2. Point Bob at the working directory: `D:\IBM Project\Open_Production\`
3. Bob will create the file `src/agents/creative_reframing.py`.

---

## What you're telling Bob (paste this prompt)

> I need you to build a small module called `creative_reframing.py` for a Python research-writing system called Open Production. The module is part of an `agents/` package; other agents in that package use a base class defined at `src/agents/base.py`.
>
> ## Specification
>
> **Purpose.** Before writing begins, Open Production proposes three creative angles on the topic. The user picks one. The chosen angle becomes the document's frame.
>
> **Input:**
> ```python
> {
>   "topic": "CRISPR for sickle cell disease",
>   "audience": "educated_lay",  # one of: researchers, educated_lay, students
>   "tone": "neutral",           # one of: neutral, skeptical, advocate, contrarian
>   "context": "Optional prior reframings or user notes (may be empty)."
> }
> ```
>
> **Output (must be JSON, exactly this shape):**
> ```python
> {
>   "angles": [
>     {
>       "id": "skeptic",
>       "name": "The skeptic's view",
>       "summary": "One-sentence frame.",
>       "questions_to_address": ["question 1", "question 2"],
>       "risk_focus": "What this angle risks getting wrong"
>     },
>     {
>       "id": "advocate",
>       ...
>     },
>     {
>       "id": "contrarian",
>       ...
>     }
>   ]
> }
> ```
>
> **Three angles must always be present:**
> 1. `skeptic` — what could go wrong, what's overstated, what's missing
> 2. `advocate` — why this matters, what's the strongest case, who benefits
> 3. `contrarian` — the non-obvious take, the contrarian-but-defensible position
>
> **Class shape.** Implement a `CreativeReframing` class that inherits from `src/agents/base.py`'s `BaseAgent`. It should expose:
> - `run(input: dict) -> dict`
> - The returned dict must validate against the JSON shape above
> - `run()` must NOT raise on missing/empty `context`
> - `run()` must return all three angles, even if the LLM call returns fewer
>
> **Model.** Use the existing `src/tools/llm_client.py` wrapper. The wrapper exposes `complete(prompt: str, system: str) -> str`. Do not call any LLM directly.
>
> **Prompt design.** The system prompt must instruct the model to:
> - Always return all three angles
> - Match the JSON shape exactly (no markdown fences, no prose)
> - Keep each summary to one sentence
> - Keep each angle distinct (no overlap of `questions_to_address`)
>
> **Validation.** If the LLM returns malformed JSON or fewer than three angles, retry once. On second failure, return a deterministic fallback set of angles derived from the input.
>
> **Tests.** Include a `tests/test_creative_reframing.py` file with:
> - One test for happy path (mock the LLM to return a known good JSON)
> - One test for malformed JSON retry path
> - One test for missing-context safety
> - One test for the fallback (LLM fails twice)
> - One test asserting all three angles have distinct `questions_to_address`
>
> **Constraints.**
> - Single file for the agent: `src/agents/creative_reframing.py`
> - Single file for the tests: `tests/test_creative_reframing.py`
> - Use the project's existing LLM client (do not import openai, anthropic, etc. directly)
> - No new dependencies in `pyproject.toml`
> - Keep the file under 300 lines including tests
>
> **Deliver.**
> 1. The implementation file
> 2. The test file
> 3. A 5-line summary at the top of the transcript describing what you built and why

---

## Save the transcript

Copy the entire Bob session into:

`D:\IBM Project\Open_Production\bob-sessions\02-creative-reframing-feature\transcript.md`

Add this header:

```markdown
# Bob Session 2 — Build the Creative-Reframing Feature

**Date:** 2026-07-27
**Goal:** Implement `src/agents/creative_reframing.py` per Boris's spec.
**Outcome:** (paste the 5-line summary inline)

---

## Transcript

(paste session here)

---

## Files produced

- `src/agents/creative_reframing.py`
- `tests/test_creative_reframing.py`
```

---

## Done when

- [ ] `src/agents/creative_reframing.py` exists, ≤ 300 lines
- [ ] `tests/test_creative_reframing.py` exists, 5 tests, all pass
- [ ] No new dependencies added
- [ ] The transcript is saved
- [ ] Boris reviews the implementation

---

## What Boris does with the output

I review the implementation for:
- Correctness of the validation/retry/fallback logic
- Whether the JSON shape is exactly as specified
- Test coverage quality
- Whether the system prompt is well-designed (this is the most likely weakness — Bob may write a generic prompt)

If anything is wrong, I flag it. If it's good, we move to Session 3.