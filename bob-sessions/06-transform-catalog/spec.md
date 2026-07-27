# Bob Session 6 — Transform Catalog

**Goal:** Build a `transforms/` package that makes "Transform is one of the five primitives" real in code. Each Transform is named, typed, idempotent. Generalizes the "named motion primitive" pattern from video-shotcraft.

**Output:** New `src/transforms/` package + tests.

---

## Context

- Working directory: `D:\IBM Project\Open_Production\`
- Existing: `src/agents/base.py`, `src/agents/creative_reframing.py`, `src/agents/confirm_gate.py` (session 5), `src/validation/gates.py`, `src/audit/recorder.py`, `src/tools/llm_client.py`
- 26/26 tests (or 31/31 with session 5) currently pass

---

## Spec — paste into Bob IDE verbatim

> I need to build a small `transforms/` package that implements the "Transform" primitive from my architecture. A Transform is a named, typed, idempotent operation. Think of it as a catalog of reusable building blocks.
>
> ## Directory layout
>
> ```
> src/transforms/
> ├── __init__.py
> ├── base.py                  # Transform base class + TransformResult dataclass
> ├── registry.py              # Global catalog; register_transform(), get_transform(), list_transforms()
> ├── text/
> │   ├── __init__.py
> │   ├── upper.py             # Transform: upper(text: str) -> str
> │   ├── word_count.py        # Transform: word_count(text: str) -> int
> │   └── summary.py           # Transform: summary(text: str, max_words: int = 50) -> str
> ├── filter/
> │   ├── __init__.py
> │   ├── require_source.py    # Transform: require_source(claim: dict) -> dict
> │   └── dedupe.py            # Transform: dedupe(items: list) -> list
> └── compose/
>     ├── __init__.py
>     └── sequence.py          # Transform: sequence(*transforms: Transform) -> Transform
> ```
>
> ## `src/transforms/base.py`
>
> ```python
> from dataclasses import dataclass, field
> from typing import Any
>
> @dataclass
> class TransformResult:
>     value: Any
>     transform_name: str
>     metadata: dict = field(default_factory=dict)
>
> class Transform:
>     """Base class for a named, typed, idempotent transform."""
>     name: str = "unnamed"
>     input_schema: type | None = None
>     output_schema: type | None = None
>
>     def __init__(self, name: str = None):
>         if name:
>             self.name = name
>
>     def apply(self, input_value: Any) -> TransformResult:
>         raise NotImplementedError
>
>     def __call__(self, input_value: Any) -> TransformResult:
>         return self.apply(input_value)
>
>     def compose(self, other: "Transform") -> "Transform":
>         from src.transforms.compose.sequence import SequenceTransform
>         return SequenceTransform([self, other])
> ```
>
> ## `src/transforms/registry.py`
>
> ```python
> from typing import TYPE_CHECKING
> if TYPE_CHECKING:
>     from .base import Transform
>
> _registry: dict = {}
>
> def register_transform(t: "Transform") -> None:
>     _registry[t.name] = t
>
> def get_transform(name: str) -> "Transform":
>     return _registry[name]
>
> def list_transforms() -> list[str]:
>     return sorted(_registry.keys())
>
> def clear_registry() -> None:
>     _registry.clear()
> ```
>
> ## Each transform
>
> Follow this pattern (example):
>
> ```python
> # src/transforms/text/upper.py
> from src.transforms.base import Transform, TransformResult
> from src.transforms.registry import register_transform
>
> class UpperTransform(Transform):
>     name = "text.upper"
>     input_schema = str
>     output_schema = str
>
>     def apply(self, input_value: str) -> TransformResult:
>         return TransformResult(
>             value=input_value.upper(),
>             transform_name=self.name,
>         )
>
> register_transform(UpperTransform())
> ```
>
> Specific implementations:
>
> - `text/upper.py`: `UpperTransform` — `value = input_value.upper()`
> - `text/word_count.py`: `WordCountTransform` — `value = len(input_value.split())`, returns int
> - `text/summary.py`: `SummaryTransform` — `value = " ".join(input_value.split()[:max_words])`. Constructor takes `max_words: int = 50`.
> - `filter/require_source.py`: `RequireSourceTransform` — `value = {**input_value, "source_required": True}`
> - `filter/dedupe.py`: `DedupeTransform` — `value = sorted(set(input_value))`. Idempotent by definition.
> - `compose/sequence.py`: `SequenceTransform` — accepts a list of Transforms in constructor. `apply(input)` runs them in order, threading the output of each into the next. Final result is the last transform's output.
>
> Each file ≤ 30 lines.
>
> ## `__init__.py` files
>
> Each `__init__.py` imports all transforms from that package so they auto-register. Example:
>
> ```python
> # src/transforms/__init__.py
> from .base import Transform, TransformResult
> from .registry import register_transform, get_transform, list_transforms, clear_registry
> from . import text  # noqa
> from . import filter  # noqa
> from . import compose  # noqa
> ```
>
> ## Tests — `tests/test_transforms.py`
>
> 10 tests:
>
> 1. `text.upper` — input "hello" returns "HELLO"
> 2. `text.upper` — running twice on "hello" returns "HELLO" both times (idempotency)
> 3. `text.word_count` — input "hello world foo" returns 3
> 4. `text.summary` — input "a b c d e" with max_words=2 returns "a b"
> 5. `filter.require_source` — input `{"text": "x"}` returns `{"text": "x", "source_required": True}`
> 6. `filter.dedupe` — input `[1, 2, 2, 3, 1]` returns `[1, 2, 3]`
> 7. `compose.sequence` — sequence of upper → word_count on "hello world" returns 2
> 8. `registry` — after import, `list_transforms()` returns at least 6 names
> 9. `registry` — `get_transform("text.upper")` returns the UpperTransform instance
> 10. `Transform.compose(other)` — `UpperTransform().compose(WordCountTransform())` returns a SequenceTransform
>
> Use `clear_registry()` fixture to reset state between tests.
>
> ## Constraints
>
> - Pure stdlib. No new dependencies.
> - Do not modify any existing files.
> - All existing tests must still pass. Plus 10 new = 36+ total.
> - Run `pytest -v` after each transform file. Report full output.
> - Every transform MUST auto-register on import.
>
> ## Output
>
> 1. New files in `src/transforms/` and `tests/test_transforms.py`
> 2. Full pytest run output (showing 36+ passing)
> 3. 5-line summary at the top of the transcript
> 4. List of all registered transforms at the end

---

## Save the transcript

Save to `D:\IBM Project\Open_Production\bob-sessions\06-transform-catalog\transcript.md`. Use this header:

```markdown
# Bob Session 6 — Transform Catalog

**Date:** 2026-07-27
**Goal:** Build transforms/ package with named, typed, idempotent Transforms.
**Outcome:** (paste 5-line summary)

---

## Files produced

- src/transforms/ (8 files)
- tests/test_transforms.py

---

## Registered transforms

(paste list_transforms() output)

---

## Transcript

(paste session here)
```

---

## Done when

- [ ] All files in `src/transforms/` exist
- [ ] All transforms auto-register on import
- [ ] `tests/test_transforms.py` has 10 tests, all pass
- [ ] All existing tests still pass (36+ total)
- [ ] Transcript saved

---

## Why this session matters

The architecture doc claims "Transform is one of the five primitives." After this session, it's real code, not just a doc claim. v0.2 video vertical will register its own Transforms in this catalog. Judges evaluating Innovation see the medium-blind kernel has a working abstraction layer.

Begin.