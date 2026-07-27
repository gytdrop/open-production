"""LLM client interface + a tiny mock for tests."""
from __future__ import annotations

import json
from typing import Optional, Protocol


class LLMClient(Protocol):
    """Minimal LLM client contract."""

    def complete(self, prompt: str, system: str = "") -> str:
        """Return the model''s completion for ``prompt`` (with optional ``system`` preamble)."""
        ...


def _default_three_angle_json() -> str:
    """Deterministic three-angle JSON used when MockLLMClient has no explicit response."""
    angles = [
        {
            "id": "skeptic",
            "name": "Skeptic",
            "summary": "What are the strongest objections to the mainstream framing?",
            "questions_to_address": [
                "What evidence is missing from the dominant narrative?",
                "Which stakeholders benefit from the current framing?",
                "What has been overstated or under-scrutinised?",
            ],
            "risk_focus": "May overemphasise doubt and underplay genuine progress.",
        },
        {
            "id": "advocate",
            "name": "Advocate",
            "summary": "Why does the topic matter and who stands to benefit most?",
            "questions_to_address": [
                "What is the strongest evidence in favour of the topic?",
                "Who are the primary beneficiaries and what do they report?",
                "What milestones mark genuine forward progress?",
            ],
            "risk_focus": "May underweight risks, costs, or equity concerns.",
        },
        {
            "id": "contrarian",
            "name": "Contrarian",
            "summary": "What is the defensible but underexplored position on the topic?",
            "questions_to_address": [
                "What does the consensus get backwards?",
                "Which second-order effects are being ignored?",
                "What would a contrarian-but-rigorous analyst argue?",
            ],
            "risk_focus": "May prioritise novelty over accuracy.",
        },
    ]
    return json.dumps({"angles": angles})


class MockLLMClient:
    """Returns a fixed JSON string. Used by tests + the demo stub.

    Behaviour:
    * If ``set_response(s)`` was called (or the constructor received a
      non-None ``response=``), ``complete()`` returns that string verbatim.
    * Otherwise ``complete()`` returns a default three-angle JSON payload
      that ``agents.creative_reframing.CreativeReframing`` can parse as-is.
    """

    def __init__(self, response: Optional[str] = None) -> None:
        self.response: Optional[str] = response

    def set_response(self, s: str) -> None:
        """Pin ``complete()`` to return ``s`` until cleared."""
        self.response = s

    def complete(self, prompt: str, system: str = "") -> str:
        if self.response is not None:
            return self.response
        return _default_three_angle_json()


class ResearchMockLLMClient:
    """Returns a deterministic three-angle JSON response for demo/research prompts.

    Extracts the topic from the prompt (first line after "Topic: ") and
    builds a valid ``{"angles": [...]}`` payload so the demo runs with no
    real API keys.
    """

    def complete(self, prompt: str, system: str = "") -> str:  # noqa: ARG002
        topic = "the topic"
        for line in prompt.splitlines():
            if line.startswith("Topic:"):
                topic = line.split(":", 1)[1].strip()
                break
        angles = [
            {
                "id": "skeptic",
                "name": "The skeptic''s view",
                "summary": f"What are the strongest objections to current claims about {topic}?",
                "questions_to_address": [
                    f"What evidence is missing from the mainstream narrative on {topic}?",
                    "Which stakeholders benefit from the dominant framing?",
                    "What has been overstated or under-scrutinised?",
                ],
                "risk_focus": "May overemphasise doubt and underplay genuine progress.",
            },
            {
                "id": "advocate",
                "name": "The advocate''s case",
                "summary": f"Why does {topic} matter and who stands to benefit most?",
                "questions_to_address": [
                    f"What is the strongest evidence in favour of {topic}?",
                    "Who are the primary beneficiaries and what do they report?",
                    "What milestones mark genuine forward progress?",
                ],
                "risk_focus": "May underweight risks, costs, or equity concerns.",
            },
            {
                "id": "contrarian",
                "name": "The non-obvious take",
                "summary": f"What is the defensible but underexplored position on {topic}?",
                "questions_to_address": [
                    f"What does the consensus on {topic} get backwards?",
                    "Which second-order effects are being ignored?",
                    "What would a contrarian-but-rigorous analyst argue?",
                ],
                "risk_focus": "May prioritise novelty over accuracy.",
            },
        ]
        return json.dumps({"angles": angles})