"""Creative-reframing agent: proposes three angles on a topic before writing begins.

Before writing starts, Open Production surfaces three distinct angles on the topic
(skeptic, advocate, contrarian) and lets the user pick one. The chosen angle becomes
the document's creative frame — the differentiator that moves Open Production from
"AI that writes" to "AI as creative partner".
"""
from __future__ import annotations

import json

from agents.base import BaseAgent
from tools.llm_client import LLMClient, MockLLMClient


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ANGLE_IDS = ("skeptic", "advocate", "contrarian")

_SYSTEM_PROMPT = """\
You are a creative editorial strategist. Your job is to propose three distinct
angles for researching and writing about a topic.

Return ONLY a JSON object — no markdown fences, no prose before or after. The
object must have exactly this shape:

{
  "angles": [
    {
      "id": "skeptic",
      "name": "<short label>",
      "summary": "<exactly one sentence>",
      "questions_to_address": ["<question 1>", "<question 2>", "<question 3>"],
      "risk_focus": "<one sentence describing what this angle risks getting wrong>"
    },
    {
      "id": "advocate",
      "name": "<short label>",
      "summary": "<exactly one sentence>",
      "questions_to_address": ["<question 1>", "<question 2>", "<question 3>"],
      "risk_focus": "<one sentence>"
    },
    {
      "id": "contrarian",
      "name": "<short label>",
      "summary": "<exactly one sentence>",
      "questions_to_address": ["<question 1>", "<question 2>", "<question 3>"],
      "risk_focus": "<one sentence>"
    }
  ]
}

Rules:
- All three angle ids (skeptic, advocate, contrarian) MUST be present.
- Each angle's questions_to_address must be distinct from the other angles' questions.
- Summaries are exactly one sentence — no semicolons hiding a second sentence.
- Return valid JSON only. No explanation, no commentary."""


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class CreativeReframing(BaseAgent):
    """Proposes three reframed angles on a topic.

    Injects an ``LLMClient`` so tests can swap in a mock without monkey-patching.
    If no client is provided, a ``MockLLMClient`` is used (safe offline default).
    """

    def __init__(self, llm: LLMClient | None = None) -> None:
        super().__init__("creative_reframing")
        self._llm: LLMClient = llm if llm is not None else MockLLMClient()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, input: dict) -> dict:
        """Return three creative angles for *input["topic"]*.

        Never raises. Falls back to a deterministic set if the LLM fails twice.
        """
        topic = input.get("topic", "")
        audience = input.get("audience", "educated_lay")
        tone = input.get("tone", "neutral")
        context = input.get("context") or ""

        prompt = self._build_prompt(topic, audience, tone, context)

        # Attempt 1
        raw = self._llm.complete(prompt, system=_SYSTEM_PROMPT)
        angles = self._parse_angles(raw)

        # Attempt 2 on failure
        if angles is None:
            raw = self._llm.complete(prompt, system=_SYSTEM_PROMPT)
            angles = self._parse_angles(raw)

        # Deterministic fallback
        if angles is None:
            angles = self._fallback_angles(topic)

        return {"angles": angles}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_prompt(topic: str, audience: str, tone: str, context: str) -> str:
        parts = [
            f"Topic: {topic}",
            f"Target audience: {audience}",
            f"Tone guidance: {tone}",
        ]
        if context.strip():
            parts.append(f"Additional context: {context.strip()}")
        return "\n".join(parts)

    @staticmethod
    def _parse_angles(raw: str) -> list[dict] | None:
        """Parse LLM output → validated angles list, or None if invalid."""
        try:
            data = json.loads(raw.strip())
        except (json.JSONDecodeError, AttributeError):
            return None

        angles = data.get("angles")
        if not isinstance(angles, list):
            return None

        # Index by id for easy lookup
        by_id = {a.get("id"): a for a in angles if isinstance(a, dict)}

        result = []
        for aid in ANGLE_IDS:
            angle = by_id.get(aid)
            if not angle:
                return None  # all three must be present
            # Ensure required keys exist
            for key in ("name", "summary", "questions_to_address", "risk_focus"):
                if key not in angle:
                    return None
            result.append(angle)

        return result

    @staticmethod
    def _fallback_angles(topic: str) -> list[dict]:
        """Deterministic fallback derived from the topic string."""
        return [
            {
                "id": "skeptic",
                "name": "The skeptic's view",
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
                "name": "The advocate's case",
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
