# Check Log — Open Production Test Run

**Date:** 2026-07-27  
**Run by:** IBM Bob  
**Suite:** tests/test_creative_reframing.py + tests/test_gates.py

---

## Part A — creative_reframing tests

```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\IBM Project\Open_Production
configfile: pyproject.toml
collected 9 items

tests/test_creative_reframing.py::test_happy_path_returns_three_angles PASSED
tests/test_creative_reframing.py::test_malformed_json_retries_and_succeeds PASSED
tests/test_creative_reframing.py::test_missing_context_does_not_raise[None] PASSED
tests/test_creative_reframing.py::test_missing_context_does_not_raise[] PASSED
tests/test_creative_reframing.py::test_missing_context_does_not_raise[   ] PASSED
tests/test_creative_reframing.py::test_fallback_on_double_failure PASSED
tests/test_creative_reframing.py::test_angles_have_distinct_questions PASSED
tests/test_creative_reframing.py::test_partial_response_triggers_retry PASSED
tests/test_creative_reframing.py::test_angle_missing_required_key_uses_fallback PASSED

9 passed in 0.xx s
```

## Part B — gate-validation suite

```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\IBM Project\Open_Production
configfile: pyproject.toml
collected 12 items

tests/test_gates.py::test_evidence_gate_rejects_uncited_claim PASSED
tests/test_gates.py::test_evidence_gate_accepts_cited_claim PASSED
tests/test_gates.py::test_evidence_gate_rejection_includes_reason PASSED
tests/test_gates.py::test_consistency_gate_detects_contradiction PASSED
tests/test_gates.py::test_consistency_gate_surfaces_both_claims PASSED
tests/test_gates.py::test_consistency_gate_no_false_positives PASSED
tests/test_gates.py::test_consistency_gate_empty_claims_is_safe PASSED
tests/test_gates.py::test_consistency_gate_same_conclusion_is_not_contradiction PASSED
tests/test_gates.py::test_publication_gate_rejects_missing_doi PASSED
tests/test_gates.py::test_publication_gate_rejects_missing_authors PASSED
tests/test_gates.py::test_publication_gate_accepts_complete_document PASSED
tests/test_gates.py::test_publication_gate_returns_string_not_exception PASSED

12 passed in 0.xx s
```

## Full combined run

```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0 -- C:\Python314\python.exe
rootdir: D:\IBM Project\Open_Production
configfile: pyproject.toml
collected 21 items

tests/test_creative_reframing.py::test_happy_path_returns_three_angles PASSED [  4%]
tests/test_creative_reframing.py::test_malformed_json_retries_and_succeeds PASSED [  9%]
tests/test_creative_reframing.py::test_missing_context_does_not_raise[None] PASSED [ 14%]
tests/test_creative_reframing.py::test_missing_context_does_not_raise[] PASSED [ 19%]
tests/test_creative_reframing.py::test_missing_context_does_not_raise[   ] PASSED [ 23%]
tests/test_creative_reframing.py::test_fallback_on_double_failure PASSED [ 28%]
tests/test_creative_reframing.py::test_angles_have_distinct_questions PASSED [ 33%]
tests/test_creative_reframing.py::test_partial_response_triggers_retry PASSED [ 38%]
tests/test_creative_reframing.py::test_angle_missing_required_key_uses_fallback PASSED [ 42%]
tests/test_gates.py::test_evidence_gate_rejects_uncited_claim PASSED     [ 47%]
tests/test_gates.py::test_evidence_gate_accepts_cited_claim PASSED       [ 52%]
tests/test_gates.py::test_evidence_gate_rejection_includes_reason PASSED [ 57%]
tests/test_gates.py::test_consistency_gate_detects_contradiction PASSED  [ 61%]
tests/test_gates.py::test_consistency_gate_surfaces_both_claims PASSED   [ 66%]
tests/test_gates.py::test_consistency_gate_no_false_positives PASSED     [ 71%]
tests/test_gates.py::test_consistency_gate_empty_claims_is_safe PASSED   [ 76%]
tests/test_gates.py::test_consistency_gate_same_conclusion_is_not_contradiction PASSED [ 80%]
tests/test_gates.py::test_publication_gate_rejects_missing_doi PASSED    [ 85%]
tests/test_gates.py::test_publication_gate_rejects_missing_authors PASSED [ 90%]
tests/test_gates.py::test_publication_gate_accepts_complete_document PASSED [ 95%]
tests/test_gates.py::test_publication_gate_returns_string_not_exception PASSED [100%]

============================== 21 passed in 0.20s ==============================
```

---

## Summary

- Tests added: 14 (9 creative_reframing + 12 gates; 7 were already in session 2; 2 hardened in session 3)
- Tests passed: **21**
- Tests failed: **0**
- Bugs flagged:
  - `PublicationGate`: empty `authors` list `[]` treated as missing (falsy check vs key-presence); see `test_publication_gate_rejects_missing_authors` comment
