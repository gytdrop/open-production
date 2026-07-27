# Bob Session 2 — Build the Creative-Reframing Feature

**Date:** 2026-07-27  
**Goal:** Implement `src/agents/creative_reframing.py` per Boris's spec.  
**Outcome:** See 5-line summary below.

---

## 5-line summary

Built `CreativeReframing`, a `BaseAgent` subclass that proposes three creative angles (skeptic / advocate / contrarian) on any topic before writing begins. The agent calls the injected `LLMClient`, validates that all three required angle IDs are present in the JSON response, retries once on malformed output, and falls back to a deterministic set derived from the topic string if both attempts fail. System prompt is tightly constrained: JSON-only output, no markdown fences, one-sentence summaries, distinct questions across angles. All five required tests pass (7 pytest items, 0 failures), including the parametrised missing-context safety check.

---

## Transcript

**User:** Build `creative_reframing.py` per the session 2 spec — `CreativeReframing(BaseAgent)`, three angles (skeptic/advocate/contrarian), retry once on bad JSON, deterministic fallback, five tests.

**Bob:** *(read `src/agents/base.py`, `src/tools/llm_client.py`, `tests/conftest.py`, `pyproject.toml`)*

### Design decisions

1. **LLM injection over import-time default** — the `llm` parameter to `__init__` defaults to `MockLLMClient()` (safe offline). Tests pass a `_SequenceLLM` that returns pre-programmed responses in order, so no monkey-patching is needed and each test is hermetically isolated.

2. **System prompt discipline** — the system prompt explicitly forbids markdown fences, requires all three angle IDs, mandates one-sentence summaries, and demands non-overlapping `questions_to_address`. This is the most common LLM failure mode (spec identified it as "the most likely weakness").

3. **`_parse_angles` is a static method returning `None` on any failure** — no exceptions escape into `run()`. The retry and fallback logic is a clean 4-line sequence in `run()`.

4. **Deterministic fallback** — derived from the `topic` string so the returned content is always meaningfully scoped to the user's actual request, not generic placeholder text.

5. **Line count** — implementation: 147 lines. Tests: 145 lines. Both well under 300.

### Files produced

- `src/agents/creative_reframing.py` (147 lines)
- `tests/test_creative_reframing.py` (145 lines)

### Test run output

```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\IBM Project\Open_Production
configfile: pyproject.toml
collected 7 items

tests/test_creative_reframing.py::test_happy_path_returns_three_angles PASSED
tests/test_creative_reframing.py::test_malformed_json_retries_and_succeeds PASSED
tests/test_creative_reframing.py::test_missing_context_does_not_raise[None] PASSED
tests/test_creative_reframing.py::test_missing_context_does_not_raise[] PASSED
tests/test_creative_reframing.py::test_missing_context_does_not_raise[   ] PASSED
tests/test_creative_reframing.py::test_fallback_on_double_failure PASSED
tests/test_creative_reframing.py::test_angles_have_distinct_questions PASSED

============================== 7 passed in 0.16s ==============================
```

---

## Files produced

- `src/agents/creative_reframing.py`
- `tests/test_creative_reframing.py`

---

## Done checklist

- [x] `src/agents/creative_reframing.py` exists, 147 lines (≤ 300)
- [x] `tests/test_creative_reframing.py` exists, 5 tests (7 items after parametrize), all pass
- [x] No new dependencies added to `pyproject.toml`
- [x] Transcript saved to this file
- [ ] Boris reviews the implementation
