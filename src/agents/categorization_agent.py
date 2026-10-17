"""CategorizationStoryAgent — Agent 1 of the 4-agent manifest pipeline.

Replaces: Intent + Story + Script agents.

Takes the user's raw narrative text and asks IBM Bob (any LLMClient) to:
  1. classify the media type (documentary / educational / cinematic_narrative /
     promotional / social_short), and
  2. chunk the narrative into chronological scenes, each with a title,
     summary, and the source text span it covers.

The agent is transport-agnostic: it accepts anything satisfying the
``tools.llm_client.LLMClient`` protocol (``complete(prompt, system) -> str``),
so the same code runs against IBM Bob in production and ``BobMockClient``
offline.  ``BobMockClient`` below demonstrates the exact JSON contract Bob is
prompted to return.

Run the built-in demo (no API key needed):
    python -m agents.categorization_agent
"""
from __future__ import annotations

import json
import re

from agents.base import BaseAgent

SYSTEM_PROMPT = (
    "You are IBM Bob, a story-structure analyst for a media production pipeline. "
    "You always answer with a single valid JSON object and nothing else — "
    "no prose, no markdown fences."
)

PROMPT_TEMPLATE = """Analyze the narrative below and return JSON with exactly this shape:

{{
  "media_category": one of ["documentary", "educational", "cinematic_narrative", "promotional", "social_short"],
  "category_rationale": "<one sentence>",
  "scenes": [
    {{
      "scene_id": "scene_01",
      "title": "<3-6 word title>",
      "summary": "<1-2 sentence summary of what happens>",
      "narrative_text": "<the verbatim span of the source text this scene covers>",
      "chronological_order": 1
    }}
  ]
}}

Rules:
- Scenes must be in chronological story order and cover the whole narrative with no gaps.
- Prefer 3-8 scenes; split on changes of time, place, or emotional beat.
- scene_id is zero-padded and sequential.

NARRATIVE:
{narrative}
"""


class CategorizationStoryAgent(BaseAgent):
    """Classifies raw narrative text and segments it into chronological scenes."""

    WRITABLE_FIELDS = frozenset({"media_category", "scenes"})
    DIAGNOSTIC_KEYS = frozenset({"category_rationale"})

    def __init__(self, llm_client) -> None:
        super().__init__(name="categorization_story")
        self.llm = llm_client

    def run(self, input: dict) -> dict:  # noqa: A002
        narrative = (input.get("narrative") or "").strip()
        if not narrative:
            return self._enforce_scope({"media_category": "unknown", "scenes": []})

        raw = self.llm.complete(PROMPT_TEMPLATE.format(narrative=narrative), system=SYSTEM_PROMPT)
        parsed = _parse_json_response(raw)

        scenes = parsed.get("scenes") or []
        for i, scene in enumerate(scenes, start=1):
            scene.setdefault("scene_id", f"scene_{i:02d}")
            scene.setdefault("chronological_order", i)

        return self._enforce_scope(
            {
                "media_category": parsed.get("media_category", "unknown"),
                "category_rationale": parsed.get("category_rationale", ""),
                "scenes": scenes,
            }
        )


def _parse_json_response(raw: str) -> dict:
    """Parse an LLM reply into a dict, tolerating markdown fences / preamble."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass
    brace = re.search(r"\{.*\}", raw, re.DOTALL)
    if brace:
        try:
            return json.loads(brace.group(0))
        except json.JSONDecodeError:
            pass
    raise ValueError(f"IBM Bob returned unparseable JSON (first 200 chars): {raw[:200]!r}")


class BobMockClient:
    """Offline stand-in for IBM Bob.

    Satisfies the LLMClient protocol and returns the exact JSON contract the
    real Bob is prompted to produce, deterministically derived from the
    narrative: sentences are grouped into up to four chronological scenes.
    Used by tests and the ``python -m agents.categorization_agent`` demo.
    """

    def complete(self, prompt: str, system: str = "") -> str:  # noqa: ARG002
        narrative = prompt.split("NARRATIVE:", 1)[-1].strip()
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", narrative) if s.strip()]
        n_scenes = min(4, max(1, len(sentences)))
        per_scene = max(1, len(sentences) // n_scenes)

        scenes = []
        for i in range(n_scenes):
            start = i * per_scene
            end = None if i == n_scenes - 1 else (i + 1) * per_scene
            chunk = " ".join(sentences[start:end])
            first_words = " ".join(chunk.split()[:5])
            scenes.append(
                {
                    "scene_id": f"scene_{i + 1:02d}",
                    "title": first_words or f"Scene {i + 1}",
                    "summary": chunk[:160],
                    "narrative_text": chunk,
                    "chronological_order": i + 1,
                }
            )
        return json.dumps(
            {
                "media_category": "cinematic_narrative",
                "category_rationale": "A personal story arc with emotional beats suits a cinematic treatment.",
                "scenes": scenes,
            }
        )


if __name__ == "__main__":
    SAMPLE_STORY = (
        "Arjun grew up in a cramped lane of Mumbai, playing cricket with a taped tennis "
        "ball and a bat his father repaired with wire. Every morning before school he "
        "practised against the compound wall while his mother sold flowers at the market. "
        "At fourteen, a local coach spotted him at a gully tournament and offered him a "
        "place at the academy, though the family could barely afford the bus fare. Years "
        "of discipline followed — dawn training sessions, rejections at state trials, and "
        "a shoulder injury that nearly ended it all. Then one monsoon season, he was "
        "called up for the state under-19 side and scored a century on debut. The lane he "
        "grew up in gathered around a single television, and his father wept holding the "
        "old repaired bat."
    )
    agent = CategorizationStoryAgent(llm_client=BobMockClient())
    result = agent.run({"narrative": SAMPLE_STORY})
    print(json.dumps(result, indent=2))
