# Bob Session 4 — Demo Entry Point + Audit Trail Recorder

**Goal:** Wire `creative_reframing` + the three fail-closed gates into a runnable end-to-end demo. Every gate decision gets recorded to `audit_trail.jsonl`. This is the *integration* session — it makes the existing pieces demoable.

**Output:**
- `src/audit/recorder.py` — small audit recorder
- `src/audit/__init__.py` — empty package init
- `scripts/run_demo.py` — replaces the stub; actually runs end-to-end
- `tests/test_audit_recorder.py` — 3–5 tests for the recorder

---

## Context for Bob

You're picking up where Bob sessions 2 and 3 left off. The artifacts:

- `D:\IBM Project\Open_Production\src\agents\creative_reframing.py` (189 lines) — takes a topic + audience + tone, returns 3 angles.
- `D:\IBM Project\Open_Production\src\validation\gates.py` — three classes:
  - `EvidenceGate.process(claim: dict) -> dict` — claim must have `source_ids: list[str]`. Returns claim with `status` + `reason`.
  - `ConsistencyGate.find_contradictions(claims: list[dict]) -> list[dict]` — claims with same `fact_id` + different `conclusion` are contradictions.
  - `PublicationGate.check(metadata: dict) -> tuple[bool, str]`.
- `D:\IBM Project\Open_Production\scripts\run_demo.py` — currently a stub. You replace it.
- 21/21 tests currently pass.

---

## Spec — paste this prompt into Bob IDE verbatim

> I need you to build TWO small modules that wire the existing `creative_reframing` agent and the three fail-closed gates into a runnable end-to-end demo. Every gate decision must be recorded to `audit_trail.jsonl`.
>
> ## Module 1 — `src/audit/recorder.py`
>
> ```python
> # API
> class AuditRecorder:
>     def __init__(self, path: str = "audit_trail.jsonl"):
>         self.path = path
>         # ensure file exists (truncate or fresh each run)
>
>     def record_gate_decision(
>         self,
>         gate_name: str,        # "evidence_gate" | "consistency_gate" | "publication_gate"
>         claim_id: str,
>         decision_status: str,  # "accepted" | "rejected" | "contradiction_detected" | "publish_ok" | "publish_rejected"
>         reason: str = "",
>         evidence: dict | None = None,
>     ) -> None:
>         """Append one JSON line to self.path."""
>
>     def entries(self) -> list[dict]:
>         """Read all entries from the file. Return as list of dicts."""
> ```
>
> Each JSON line in `audit_trail.jsonl`:
>
> ```json
> {"ts": "2026-07-27T21:11:00Z", "gate_name": "evidence_gate", "claim_id": "c1", "decision_status": "accepted", "reason": "", "evidence": {"source_ids": ["s1"]}}
> ```
>
> Use `datetime.now(timezone.utc).isoformat()` for `ts`.
>
> Thread-safe via `threading.Lock`. 30–50 lines including imports and docstring.
>
> ## Module 2 — `scripts/run_demo.py`
>
> Replace the existing stub. New behavior:
>
> 1. Argparse: `--topic` (required), `--audience` (default "educated_lay"), `--tone` (default "neutral"), `--out` (default "audit_trail.jsonl").
> 2. Use `MockLLMClient` from `src/tools/llm_client.py` so the demo runs with no real API keys. The `MockLLMClient` should be augmented to return a deterministic JSON string with three valid angles (skeptic / advocate / contrarian) when prompted with a research-style topic. You can either extend `MockLLMClient` (preferred) or inject a fake response in `run_demo.py`.
> 3. Call `CreativeReframing(llm_client).run({"topic": ..., "audience": ..., "tone": ...})` and print the 3 angles as a numbered list.
> 4. Use a hardcoded fixture set of 3 claims (one accepted by evidence, one rejected by evidence, two with same `fact_id` but different conclusions).
> 5. Run the 3 claims through `EvidenceGate.process()`, recording each decision to the recorder.
> 6. Run the result through `ConsistencyGate.find_contradictions()`, recording each contradiction detected.
> 7. Simulate a metadata dict and run it through `PublicationGate.check()`, recording the decision.
> 8. Print a summary line:
>    `3 angles · X claims accepted · Y claims rejected · Z contradictions detected · audit trail: audit_trail.jsonl`
> 9. Exit 0. (Demo, not a validator.)
>
> Total: 60–80 lines including imports.
>
> ## Tests — `tests/test_audit_recorder.py`
>
> 3–5 tests:
> 1. Recorder writes valid JSONL; entries are parseable as JSON.
> 2. Multiple `record_gate_decision` calls produce the right number of entries.
> 3. Each entry has the required fields: `ts`, `gate_name`, `claim_id`, `decision_status`.
> 4. Empty file → `entries()` returns `[]`.
> 5. The recorder truncates/creates fresh on instantiation (no leftover entries from prior runs).
>
> Use `tmp_path` fixture. No mocking required.
>
> ## Constraints
>
> - No new dependencies. Pure stdlib (`json`, `datetime`, `threading`, `pathlib`).
> - Keep total new code under 200 lines across both modules + tests.
> - Run `pytest -v` after each file is written. All tests must still pass, plus the new recorder tests. Target: 24–26 total passing.
> - Do NOT modify `creative_reframing.py` or `gates.py`. You may extend `MockLLMClient` if needed.
> - The script must be runnable as `python scripts/run_demo.py --topic "..."`.
> - The audit trail file must be the one specified by `--out`.
>
> ## Output
>
> 1. The two new modules.
> 2. The new test file.
> 3. The full pytest run output (showing 24+ tests passing).
> 4. A 5-line summary at the top of the transcript describing what you built and how the demo runs.

---

## Save the transcript

Save the entire Bob session to:

`D:\IBM Project\Open_Production\bob-sessions\04-demo-and-audit\transcript.md`

If the directory `D:\IBM Project\Open_Production\bob-sessions\04-demo-and-audit\` doesn't exist, create it before saving.

Use this header at the top of the file:

```markdown
# Bob Session 4 — Demo Entry Point + Audit Trail Recorder

**Date:** 2026-07-27
**Goal:** Wire creative_reframing + gates into a runnable demo with audit trail.
**Outcome:** (paste 5-line summary inline)

---

## Files produced

- `src/audit/__init__.py`
- `src/audit/recorder.py`
- `scripts/run_demo.py` (replaces stub)
- `tests/test_audit_recorder.py`

---

## Transcript

(paste session here)
```

---

## Done when

- [ ] `src/audit/recorder.py` exists, 30–50 lines, thread-safe.
- [ ] `src/audit/__init__.py` exists.
- [ ] `scripts/run_demo.py` runs end-to-end without error.
- [ ] `tests/test_audit_recorder.py` has 3–5 tests, all pass.
- [ ] `pytest -v` reports 24–26 tests passing (existing 21 + new 3–5).
- [ ] `audit_trail.jsonl` is produced when `run_demo.py` runs.
- [ ] Transcript saved to `bob-sessions/04-demo-and-audit/transcript.md`.

---

## Why this session matters

Right now the demo can't run. After this session, you can run:

```
python scripts/run_demo.py --topic "CRISPR for sickle cell disease"
```

And it prints the 3 angles, runs the claims through 3 fail-closed gates, and writes `audit_trail.jsonl`. That's the live demo for the video. That's what wins "Technical Execution" and "Feasibility" on the rubric.

Begin.