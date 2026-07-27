# Bob Session 5 — Interactive Confirm Gate

**Goal:** Build a real interactive `confirm` gate inside `scripts/run_demo.py` that follows the hyperframes-motion-director pattern: propose → wait for confirmation → produce. Without this, the demo is "system proposes and runs" — with it, the demo is "system proposes, user picks, system runs." The user picking is the AI-as-creative-partner moment judges score on.

**Output:** Updated `scripts/run_demo.py` + new `src/agents/confirm_gate.py` + tests.

---

## Context

The repo is `D:\IBM Project\Open_Production\`. Existing files:

- `src/agents/creative_reframing.py` — Bob-built, 189 lines. Takes a topic, returns 3 angles.
- `scripts/run_demo.py` — Bob-built, current behavior: prints 3 angles, runs gates, writes audit trail.
- `tests/test_creative_reframing.py` — 9 tests.
- 26/26 tests currently pass.

Currently the demo runs the angles through the gates *without* user input. The user has no role after declaring the topic. That's the gap. Now add the confirm gate.

---

## Spec — paste this into Bob IDE verbatim

> I need to add a real interactive confirm gate to the Open Production demo. The pattern comes from hyperframes-motion-director: propose something → wait for human confirmation → produce. Currently my demo runs end-to-end with no user interaction after the topic is declared. I want the user to pick which angle to use *before* the gates fire.
>
> ## What to build
>
> ### Module 1 — `src/agents/confirm_gate.py`
>
> A new module that implements a human-in-the-loop confirm gate. Three classes:
>
> ```python
> from dataclasses import dataclass
> from typing import Protocol, Callable
>
> @dataclass
> class ConfirmRequest:
>     summary: str         # "Which angle should guide the write?"
>     options: list[str]   # ["skeptic", "advocate", "contrarian"]
>     default: str | None  # suggested default
>
> @dataclass
> class ConfirmResponse:
>     choice: str          # the chosen option
>     declined: bool       # True if user said "no" / cancelled
>
> class ConfirmSink(Protocol):
>     """Anything that can present a confirm request and get a response."""
>     def ask(self, request: ConfirmRequest) -> ConfirmResponse: ...
>
> class TtyConfirmSink:
>     """Interactive terminal sink. Prints options, reads stdin, returns choice."""
>     def ask(self, request: ConfirmRequest) -> ConfirmResponse:
>         # Print:
>         #   summary
>         #   1. option[0]
>         #   2. option[1]
>         #   3. option[2]
>         #   Default: <default>
>         #   Choose [1/2/3/d/default]:
>         # Read input. If empty, use default. Map "1" -> options[0], etc.
>         # If input is "n" or "no", return ConfirmResponse(choice="", declined=True).
>         # If EOF / non-interactive, return ConfirmResponse(choice=default or options[0], declined=False).
>
> class AutoConfirmSink:
>     """Deterministic sink for tests. Always picks the default or specified choice."""
>     def __init__(self, choice: str | None = None):
>         self.choice = choice
>     def ask(self, request: ConfirmRequest) -> ConfirmResponse:
>         chosen = self.choice or request.default or (request.options[0] if request.options else "")
>         return ConfirmResponse(choice=chosen, declined=False)
> ```
>
> Keep total under 80 lines including imports and docstrings.
>
> ### Module 2 — Update `scripts/run_demo.py`
>
> After `creative_reframing.run()` returns the 3 angles, do:
>
> 1. Build a `ConfirmRequest(summary="Which angle should guide the write?", options=["skeptic", "advocate", "contrarian"], default=...)`. The default should be the angle whose `id` matches the topic's first character (just for determinism — `chr(ord(topic[0].lower()) % 3)` → 0/1/2 → ids).
> 2. Call `sink.ask(request)` to get the user's choice.
> 3. If `declined`, print "User cancelled. Exiting." and exit 0.
> 4. Filter the angles dict to just the chosen one. Use it as the framing for the gates.
> 5. Print the chosen angle prominently.
> 6. Add a CLI flag `--no-confirm` that uses `AutoConfirmSink` instead of `TtyConfirmSink`. This is what `make demo` uses by default (so the demo runs in CI / non-interactive contexts).
> 7. After confirmation, the demo continues exactly as before: evidence_gate, consistency_gate, publication_gate, audit trail.
> 8. **Add a new audit entry** to `audit_trail.jsonl` for the confirm gate. Format:
>    ```json
>    {"ts": "2026-07-27T...", "gate_name": "confirm_gate", "claim_id": "angle-selection", "decision_status": "accepted", "reason": "user picked <chosen_angle>", "evidence": {"options": ["skeptic", "advocate", "contrarian"], "chosen": "<chosen_angle>"}}
>    ```
> 9. Update the summary line at the end:
>    `3 angles proposed · user picked <chosen_angle> · X claims accepted · Y claims rejected · Z contradictions detected · audit trail: audit_trail.jsonl`
>
> ### Tests — `tests/test_confirm_gate.py`
>
> 5 tests:
> 1. `TtyConfirmSink` with stdin-mocked input "1" returns choice=options[0], declined=False.
> 2. `TtyConfirmSink` with empty stdin returns the default.
> 3. `TtyConfirmSink` with "n" returns declined=True.
> 4. `AutoConfirmSink(c="advocate")` always returns choice="advocate".
> 5. `AutoConfirmSink` with no choice arg falls back to `request.default` then `request.options[0]`.
>
> Use `monkeypatch` for stdin mocking. No external deps.
>
> ## Constraints
>
> - Pure stdlib. No new dependencies.
> - Do not modify `src/agents/creative_reframing.py` or `src/validation/gates.py` or `src/audit/recorder.py`.
> - All 26 existing tests must still pass. Plus 5 new = 31/31.
> - Run `pytest -v` after each file. Report the full output.
> - The confirm gate MUST run in the demo by default. `--no-confirm` is the escape hatch for CI.
> - Audit trail entry for the confirm gate must be exactly the format above.
>
> ## Output
>
> 1. The new module `src/agents/confirm_gate.py`.
> 2. Updated `scripts/run_demo.py`.
> 3. New test file `tests/test_confirm_gate.py`.
> 4. Full pytest run output (showing 31/31 passing).
> 5. Transcript of running the demo with `--no-confirm` (proves the end-to-end flow still works).
> 6. Transcript of running the demo with the interactive prompt (proves the confirm gate works).
> 7. 5-line summary at the top of the transcript.

---

## Save the transcript

Save the entire Bob session to:

`D:\IBM Project\Open_Production\bob-sessions\05-confirm-gate\transcript.md`

Use this header:

```markdown
# Bob Session 5 — Interactive Confirm Gate

**Date:** 2026-07-27
**Goal:** Add interactive confirm gate to demo (hyperframes-motion-director pattern).
**Outcome:** (paste 5-line summary)

---

## Files produced

- `src/agents/confirm_gate.py`
- `scripts/run_demo.py` (updated)
- `tests/test_confirm_gate.py`

---

## Transcript

(paste session here)

---

## Demo evidence

### Run with --no-confirm
(paste output)

### Run with interactive prompt
(paste output)
```

---

## Done when

- [ ] `src/agents/confirm_gate.py` exists, ≤ 80 lines, 3 classes.
- [ ] `tests/test_confirm_gate.py` exists, 5 tests, all pass.
- [ ] `scripts/run_demo.py` updated with confirm gate + `--no-confirm` flag.
- [ ] All 31 tests pass (26 existing + 5 new).
- [ ] Demo evidence captured for both interactive and `--no-confirm` modes.
- [ ] Transcript saved.

---

## Why this session matters

The rubric asks: *"How can AI act as a creative partner rather than simply a content generator?"* The answer is the user picking. Without this session, our demo runs end-to-end without user input — that's an AI generator, not a creative partner. With this session, the demo *requires* user input between Stage 2 and Stage 3. That's the AI-as-creative-partner moment judges score on Innovation + Challenge Fit.

This is the single highest-impact session left. After this, the demo video at 1:05–1:45 shows the user *picking* an angle. That's the rubric's exact framing in action.

Begin.