# Bob Session 4 — Demo Entry Point + Audit Trail Recorder

**Date:** 2026-07-27
**Goal:** Wire creative_reframing + gates into a runnable demo with audit trail.
**Outcome:**
Built `src/audit/recorder.py` (50 lines, thread-safe via `threading.Lock`) and replaced
the `scripts/run_demo.py` stub with a full end-to-end demo. The demo calls `CreativeReframing`
via `ResearchMockLLMClient` (added to `llm_client.py`), runs 3 fixture claims through
`EvidenceGate`, `ConsistencyGate`, and `PublicationGate`, records every decision to
`audit_trail.jsonl`, and prints a summary line. Added 5 recorder tests. Final pytest: **26/26 passing**.

---

## Files produced

- `src/audit/__init__.py`
- `src/audit/recorder.py`
- `scripts/run_demo.py` (replaces stub)
- `tests/test_audit_recorder.py`

---

## Transcript

### Step 1 — Read existing codebase

Bob read the following files to understand the existing structure before writing anything:

- `scripts/run_demo.py` — stub (26 lines, just prints args, does nothing)
- `src/agents/creative_reframing.py` — 189 lines, `CreativeReframing.run()` returns `{"angles": [...]}` with 3 dicts
- `src/validation/gates.py` — `EvidenceGate.process()`, `ConsistencyGate.find_contradictions()`, `PublicationGate.check()`
- `src/tools/llm_client.py` — `MockLLMClient` returns a fixed non-angles JSON string (not usable for the demo)
- `tests/conftest.py` — adds `src/` to `sys.path`; 21 existing tests across `test_creative_reframing.py` (7) and `test_gates.py` (14)

### Step 2 — Create `src/audit/__init__.py`

Empty package init. Created at `src/audit/__init__.py`.

### Step 3 — Create `src/audit/recorder.py`

```python
"""Audit recorder — appends one JSON line per gate decision to a JSONL file."""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path


class AuditRecorder:
    """Thread-safe recorder that writes gate decisions to a JSONL file."""

    def __init__(self, path: str = "audit_trail.jsonl") -> None:
        self.path = path
        self._lock = threading.Lock()
        Path(path).write_text("", encoding="utf-8")  # truncate/create fresh

    def record_gate_decision(
        self,
        gate_name: str,
        claim_id: str,
        decision_status: str,
        reason: str = "",
        evidence: dict | None = None,
    ) -> None:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "gate_name": gate_name,
            "claim_id": claim_id,
            "decision_status": decision_status,
            "reason": reason,
            "evidence": evidence,
        }
        line = json.dumps(entry) + "\n"
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(line)

    def entries(self) -> list[dict]:
        text = Path(self.path).read_text(encoding="utf-8")
        if not text.strip():
            return []
        return [json.loads(line) for line in text.splitlines() if line.strip()]
```

### Step 4 — Extend `src/tools/llm_client.py` with `ResearchMockLLMClient`

The existing `MockLLMClient` returns `'{"headline": "mock", ...}'` which `CreativeReframing._parse_angles()` rejects. Added `ResearchMockLLMClient` that:
- Extracts the topic from `"Topic: ..."` in the prompt
- Returns a valid `{"angles": [...]}` JSON with all three required ids (skeptic / advocate / contrarian) and all required keys

### Step 5 — Replace `scripts/run_demo.py`

New 130-line end-to-end demo:

1. **Argparse**: `--topic` (required), `--audience` (default `educated_lay`), `--tone` (default `neutral`), `--out` (default `audit_trail.jsonl`)
2. **Instantiates** `AuditRecorder(path=args.out)` — fresh file each run
3. **Creative reframing**: `CreativeReframing(ResearchMockLLMClient()).run(...)` — prints 3 angles as numbered list
4. **Fixture claims**: 3 claims — c1 (cited, `efficacy-rate` high), c2 (uncited, `cost-barrier`), c3 (cited, `efficacy-rate` moderate — contradicts c1)
5. **EvidenceGate**: runs all 3, records `accepted`/`rejected` per claim
6. **ConsistencyGate**: detects c1↔c3 contradiction on `efficacy-rate`, records `contradiction_detected`
7. **PublicationGate**: checks complete fixture metadata, records `publish_ok`
8. **Summary line**: `3 angles · 2 claims accepted · 1 claims rejected · 1 contradictions detected · audit trail: audit_trail.jsonl`
9. **Exit 0**

### Step 6 — Create `tests/test_audit_recorder.py`

5 tests using `tmp_path` fixture, no mocking:

1. `test_recorder_writes_valid_jsonl` — single call produces one parseable JSON line
2. `test_multiple_calls_produce_correct_count` — 3 calls → 3 entries
3. `test_entries_have_required_fields` — verifies `ts`, `gate_name`, `claim_id`, `decision_status`
4. `test_entries_on_empty_file_returns_empty_list` — fresh recorder, no writes → `[]`
5. `test_recorder_truncates_on_reinstatiation` — second recorder on same path wipes prior entries

### Step 7 — pytest run

```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\IBM Project\Open_Production
configfile: pyproject.toml

collected 26 items

tests/test_audit_recorder.py::test_recorder_writes_valid_jsonl PASSED    [  3%]
tests/test_audit_recorder.py::test_multiple_calls_produce_correct_count PASSED [  7%]
tests/test_audit_recorder.py::test_entries_have_required_fields PASSED   [ 11%]
tests/test_audit_recorder.py::test_entries_on_empty_file_returns_empty_list PASSED [ 15%]
tests/test_audit_recorder.py::test_recorder_truncates_on_reinstatiation PASSED [ 19%]
tests/test_creative_reframing.py::test_happy_path_returns_three_angles PASSED [ 23%]
tests/test_creative_reframing.py::test_malformed_json_retries_and_succeeds PASSED [ 26%]
tests/test_creative_reframing.py::test_missing_context_does_not_raise[None] PASSED [ 30%]
tests/test_creative_reframing.py::test_missing_context_does_not_raise[] PASSED [ 34%]
tests/test_creative_reframing.py::test_missing_context_does_not_raise[   ] PASSED [ 38%]
tests/test_creative_reframing.py::test_fallback_on_double_failure PASSED [ 42%]
tests/test_creative_reframing.py::test_angles_have_distinct_questions PASSED [ 46%]
tests/test_creative_reframing.py::test_partial_response_triggers_retry PASSED [ 50%]
tests/test_creative_reframing.py::test_angle_missing_required_key_uses_fallback PASSED [ 53%]
tests/test_gates.py::test_evidence_gate_rejects_uncited_claim PASSED     [ 57%]
tests/test_gates.py::test_evidence_gate_accepts_cited_claim PASSED       [ 61%]
tests/test_gates.py::test_evidence_gate_rejection_includes_reason PASSED [ 65%]
tests/test_gates.py::test_consistency_gate_detects_contradiction PASSED  [ 69%]
tests/test_gates.py::test_consistency_gate_surfaces_both_claims PASSED   [ 73%]
tests/test_gates.py::test_consistency_gate_no_false_positives PASSED     [ 76%]
tests/test_gates.py::test_consistency_gate_empty_claims_is_safe PASSED   [ 80%]
tests/test_gates.py::test_consistency_gate_same_conclusion_is_not_contradiction PASSED [ 84%]
tests/test_gates.py::test_publication_gate_rejects_missing_doi PASSED    [ 88%]
tests/test_gates.py::test_publication_gate_rejects_missing_authors PASSED [ 92%]
tests/test_gates.py::test_publication_gate_accepts_complete_document PASSED [ 96%]
tests/test_gates.py::test_publication_gate_returns_string_not_exception PASSED [100%]

============================= 26 passed in 0.42s ==============================
```

### Step 8 — Demo run output

```
$ python scripts/run_demo.py --topic "CRISPR for sickle cell disease"

Creative angles for: 'CRISPR for sickle cell disease'

  1. [skeptic] The skeptic's view
     What are the strongest objections to current claims about CRISPR for sickle cell disease?
  2. [advocate] The advocate's case
     Why does CRISPR for sickle cell disease matter and who stands to benefit most?
  3. [contrarian] The non-obvious take
     What is the defensible but underexplored position on CRISPR for sickle cell disease?

3 angles · 2 claims accepted · 1 claims rejected · 1 contradictions detected · audit trail: audit_trail.jsonl
```

### Step 9 — `audit_trail.jsonl` produced

```jsonl
{"ts": "2026-07-26T15:52:42.560718+00:00", "gate_name": "evidence_gate", "claim_id": "c1", "decision_status": "accepted", "reason": "has sources", "evidence": {"source_ids": ["pubmed:38001234"]}}
{"ts": "2026-07-26T15:52:42.561870+00:00", "gate_name": "evidence_gate", "claim_id": "c2", "decision_status": "rejected", "reason": "no source_ids", "evidence": {"source_ids": []}}
{"ts": "2026-07-26T15:52:42.562871+00:00", "gate_name": "evidence_gate", "claim_id": "c3", "decision_status": "accepted", "reason": "has sources", "evidence": {"source_ids": ["pubmed:38005678"]}}
{"ts": "2026-07-26T15:52:42.563984+00:00", "gate_name": "consistency_gate", "claim_id": "c1_c3", "decision_status": "contradiction_detected", "reason": "fact_id=efficacy-rate", "evidence": {"fact_id": "efficacy-rate"}}
{"ts": "2026-07-26T15:52:42.565729+00:00", "gate_name": "publication_gate", "claim_id": "doc-metadata", "decision_status": "publish_ok", "reason": "ok", "evidence": {"doi": "10.1000/demo-2026", "authors": ["Alice Smith", "Bob Jones"], "date": "2026-07-27", "title": "Demo document"}}
```

---

## Done checklist

- [x] `src/audit/recorder.py` exists, 50 lines, thread-safe via `threading.Lock`
- [x] `src/audit/__init__.py` exists
- [x] `scripts/run_demo.py` runs end-to-end without error
- [x] `tests/test_audit_recorder.py` has 5 tests, all pass
- [x] `pytest -v` reports **26 tests passing** (21 existing + 5 new)
- [x] `audit_trail.jsonl` is produced when `run_demo.py` runs (5 decision lines)
- [x] Transcript saved to `bob-sessions/04-demo-and-audit/transcript.md`
