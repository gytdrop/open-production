"""Tests for creative_reframing.CreativeReframing.

Five tests covering all required paths per the Session 2 spec:
  1. Happy path — valid LLM response is parsed and returned unchanged.
  2. Malformed JSON retry path — first call returns garbage, second returns valid JSON.
  3. Missing-context safety — run() succeeds when context is absent or empty.
  4. Fallback — LLM fails twice, deterministic angles are returned.
  5. Distinctness — all three angles have non-overlapping questions_to_address.
"""
from __future__ import annotations

import json
import pytest

from agents.creative_reframing import ANGLE_IDS, CreativeReframing


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_llm_response(overrides: dict | None = None) -> str:
    """Build a well-formed LLM response JSON string."""
    angles = [
        {
            "id": "skeptic",
            "name": "The skeptic's view",
            "summary": "CRISPR for sickle cell faces serious equity barriers.",
            "questions_to_address": ["Who can afford it?", "What are long-term risks?", "Is it reversible?"],
            "risk_focus": "May overstate barriers and ignore genuine breakthroughs.",
        },
        {
            "id": "advocate",
            "name": "The advocate's case",
            "summary": "CRISPR offers the first functional cure for sickle cell disease.",
            "questions_to_address": ["What trial data exists?", "Who has been cured?", "What is the approval timeline?"],
            "risk_focus": "May underplay cost and access inequity.",
        },
        {
            "id": "contrarian",
            "name": "The non-obvious take",
            "summary": "Hydroxyurea, not CRISPR, may be the better short-term answer for most patients.",
            "questions_to_address": ["Why is hydroxyurea underused?", "What do patient advocates actually want?", "How do systemic issues dwarf the gene-editing question?"],
            "risk_focus": "May be seen as dismissing a genuine breakthrough in favour of the status quo.",
        },
    ]
    if overrides:
        angles = [{**a, **overrides.get(a["id"], {})} for a in angles]
    return json.dumps({"angles": angles})


class _SequenceLLM:
    """Returns responses from a queue, one per call to complete()."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self._index = 0

    def complete(self, prompt: str, system: str = "") -> str:
        resp = self._responses[self._index % len(self._responses)]
        self._index += 1
        return resp


# ---------------------------------------------------------------------------
# Test 1: Happy path
# ---------------------------------------------------------------------------

def test_happy_path_returns_three_angles():
    """Valid LLM response → all three angles returned with correct ids."""
    llm = _SequenceLLM([_valid_llm_response()])
    agent = CreativeReframing(llm=llm)

    result = agent.run({"topic": "CRISPR for sickle cell disease", "audience": "educated_lay", "tone": "neutral"})

    assert "angles" in result
    assert len(result["angles"]) == 3
    ids = {a["id"] for a in result["angles"]}
    assert ids == set(ANGLE_IDS)

    for angle in result["angles"]:
        assert "name" in angle
        assert "summary" in angle
        assert isinstance(angle["questions_to_address"], list)
        assert len(angle["questions_to_address"]) > 0
        assert "risk_focus" in angle


# ---------------------------------------------------------------------------
# Test 2: Malformed JSON retry path
# ---------------------------------------------------------------------------

def test_malformed_json_retries_and_succeeds():
    """First call returns garbage; second call returns valid JSON → success."""
    llm = _SequenceLLM(["NOT VALID JSON !!!", _valid_llm_response()])
    agent = CreativeReframing(llm=llm)

    result = agent.run({"topic": "CRISPR for sickle cell disease"})

    assert len(result["angles"]) == 3
    assert {a["id"] for a in result["angles"]} == set(ANGLE_IDS)


# ---------------------------------------------------------------------------
# Test 3: Missing-context safety
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ctx", [None, "", "   "])
def test_missing_context_does_not_raise(ctx):
    """run() must not raise when context is absent, empty, or whitespace-only."""
    llm = _SequenceLLM([_valid_llm_response()])
    agent = CreativeReframing(llm=llm)

    result = agent.run({"topic": "climate change", "context": ctx})

    assert "angles" in result
    assert len(result["angles"]) == 3


# ---------------------------------------------------------------------------
# Test 4: Fallback when LLM fails twice
# ---------------------------------------------------------------------------

def test_fallback_on_double_failure():
    """LLM returns invalid JSON twice → deterministic fallback, no exception raised."""
    llm = _SequenceLLM(["GARBAGE", "ALSO GARBAGE"])
    agent = CreativeReframing(llm=llm)

    result = agent.run({"topic": "universal basic income"})

    assert "angles" in result
    angles = result["angles"]
    assert len(angles) == 3
    ids = {a["id"] for a in angles}
    assert ids == set(ANGLE_IDS)
    for angle in angles:
        assert "universal basic income" in angle["summary"].lower() or any(
            "universal basic income" in q.lower() for q in angle["questions_to_address"]
        ), f"Fallback angle for {angle['id']!r} doesn't reference the topic"


# ---------------------------------------------------------------------------
# Test 5: Distinct questions_to_address across all three angles
# ---------------------------------------------------------------------------

def test_angles_have_distinct_questions():
    """No question appears in more than one angle's questions_to_address."""
    llm = _SequenceLLM([_valid_llm_response()])
    agent = CreativeReframing(llm=llm)

    result = agent.run({"topic": "CRISPR for sickle cell disease"})

    all_questions: list[str] = []
    for angle in result["angles"]:
        all_questions.extend(angle["questions_to_address"])

    # Every question must be unique across all angles
    assert len(all_questions) == len(set(all_questions)), (
        "Duplicate questions found across angles: "
        + str([q for q in all_questions if all_questions.count(q) > 1])
    )


# ---------------------------------------------------------------------------
# Test 6: Partial LLM response (missing one angle) triggers retry
# ---------------------------------------------------------------------------

def test_partial_response_triggers_retry():
    """LLM returns only 2 of 3 required angles → retry → valid response returned."""
    partial = json.dumps({
        "angles": [
            {
                "id": "skeptic",
                "name": "Skeptic",
                "summary": "Sentence.",
                "questions_to_address": ["Q1"],
                "risk_focus": "R1",
            },
            # 'advocate' present, 'contrarian' intentionally absent
            {
                "id": "advocate",
                "name": "Advocate",
                "summary": "Sentence.",
                "questions_to_address": ["Q2"],
                "risk_focus": "R2",
            },
        ]
    })
    llm = _SequenceLLM([partial, _valid_llm_response()])
    agent = CreativeReframing(llm=llm)

    result = agent.run({"topic": "mRNA vaccines"})

    assert len(result["angles"]) == 3
    assert {a["id"] for a in result["angles"]} == set(ANGLE_IDS)


# ---------------------------------------------------------------------------
# Test 7: Missing required key in one angle triggers fallback
# ---------------------------------------------------------------------------

def test_angle_missing_required_key_uses_fallback():
    """Angle without 'risk_focus' key → both retries fail → deterministic fallback."""
    broken = json.dumps({
        "angles": [
            {"id": "skeptic",    "name": "S", "summary": "s.", "questions_to_address": ["q"]},  # missing risk_focus
            {"id": "advocate",   "name": "A", "summary": "a.", "questions_to_address": ["q2"], "risk_focus": "r"},
            {"id": "contrarian", "name": "C", "summary": "c.", "questions_to_address": ["q3"], "risk_focus": "r"},
        ]
    })
    llm = _SequenceLLM([broken, broken])  # both attempts broken
    agent = CreativeReframing(llm=llm)

    result = agent.run({"topic": "nuclear fusion"})

    assert len(result["angles"]) == 3
    # All fallback angles must contain the topic
    for angle in result["angles"]:
        combined = angle["summary"] + " ".join(angle["questions_to_address"])
        assert "nuclear fusion" in combined.lower()
