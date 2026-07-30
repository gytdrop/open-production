"""ShotDesignerAgent — translates shot intent into camera and lighting specs.

Scope contract (Appendix K.1 of open-production-plan.md):
  Can write:  Shot.camera, Shot.lighting (after human approval)
  Cannot write: Shot.characters, Shot.intent, Production.characters, Scene.*

Always returns exactly 3 proposals. Uses MockLLMClient pattern (structured
mock responses — same approach as CreativeReframing). A real LLM integration
would replace the _generate_proposals method.
"""
from __future__ import annotations

from agents.base import BaseAgent

# ---------------------------------------------------------------------------
# Mock proposal templates — one per intent mood category
# ---------------------------------------------------------------------------

_PROPOSAL_TEMPLATES = {
    "tense": [
        {
            "label": "High-angle surveillance",
            "rationale": "A high angle puts the protagonist at a disadvantage, reinforcing tension.",
            "camera": {"framing": "medium_wide", "angle": "high", "movement": "static",
                       "lens_mm": 35, "preset_id": None},
            "lighting": {"color_temp_k": 4200, "mood": "cold", "shadows": "hard",
                         "preset_id": "cold_interrogation"},
            "risk": "High angle can feel detached — ensure character expression is still readable.",
        },
        {
            "label": "Dutch tilt close-up",
            "rationale": "Canted framing signals psychological imbalance and imminent threat.",
            "camera": {"framing": "close", "angle": "dutch_tilt", "movement": "slow_push",
                       "lens_mm": 50, "preset_id": None},
            "lighting": {"color_temp_k": 3800, "mood": "dramatic", "shadows": "hard",
                         "preset_id": "dramatic_side_light"},
            "risk": "Dutch tilt can feel clichéd — use sparingly and purposefully.",
        },
        {
            "label": "Low-angle wide establishing",
            "rationale": "Low angle magnifies the threat; wide shot shows the protagonist is cornered.",
            "camera": {"framing": "wide", "angle": "low", "movement": "static",
                       "lens_mm": 24, "preset_id": None},
            "lighting": {"color_temp_k": 4500, "mood": "ominous", "shadows": "deep",
                         "preset_id": None},
            "risk": "Wide shot may lose intimacy — balance with a cut to close-up.",
        },
    ],
    "warm": [
        {
            "label": "Golden-hour medium shot",
            "rationale": "Warm natural light creates an inviting, optimistic atmosphere.",
            "camera": {"framing": "medium", "angle": "eye_level", "movement": "static",
                       "lens_mm": 50, "preset_id": None},
            "lighting": {"color_temp_k": 3200, "mood": "warm", "shadows": "soft",
                         "preset_id": "golden_hour"},
            "risk": "Warm tones can reduce urgency — ensure narrative stakes remain clear.",
        },
        {
            "label": "Soft close-up portrait",
            "rationale": "Close framing with soft light draws focus to emotional expression.",
            "camera": {"framing": "close", "angle": "eye_level", "movement": "slight_push",
                       "lens_mm": 85, "preset_id": None},
            "lighting": {"color_temp_k": 3400, "mood": "intimate", "shadows": "minimal",
                         "preset_id": "soft_beauty"},
            "risk": "Soft light may feel too flattering for dramatic scenes.",
        },
        {
            "label": "Wide establishing with warm fill",
            "rationale": "Shows the environment positively while grounding the emotional context.",
            "camera": {"framing": "wide", "angle": "eye_level", "movement": "slow_pan",
                       "lens_mm": 28, "preset_id": None},
            "lighting": {"color_temp_k": 3600, "mood": "welcoming", "shadows": "soft",
                         "preset_id": None},
            "risk": "Wide shots with slow movement can feel slow — match edit pace carefully.",
        },
    ],
    "default": [
        {
            "label": "Neutral medium shot",
            "rationale": "Clean, unobtrusive framing that lets the scene content lead.",
            "camera": {"framing": "medium", "angle": "eye_level", "movement": "static",
                       "lens_mm": 50, "preset_id": "standard_medium"},
            "lighting": {"color_temp_k": 5600, "mood": "neutral", "shadows": "balanced",
                         "preset_id": "daylight_neutral"},
            "risk": "Neutral framing is safe but may lack visual interest.",
        },
        {
            "label": "Over-the-shoulder coverage",
            "rationale": "Establishes spatial relationship between characters and aids continuity.",
            "camera": {"framing": "medium_close", "angle": "eye_level", "movement": "static",
                       "lens_mm": 50, "preset_id": None},
            "lighting": {"color_temp_k": 5400, "mood": "naturalistic", "shadows": "soft",
                         "preset_id": None},
            "risk": "Over-shoulder requires a matching reverse — ensure coverage is complete.",
        },
        {
            "label": "Insert / detail shot",
            "rationale": "Directs viewer attention to a specific narrative detail.",
            "camera": {"framing": "extreme_close", "angle": "eye_level", "movement": "static",
                       "lens_mm": 100, "preset_id": None},
            "lighting": {"color_temp_k": 5600, "mood": "focused", "shadows": "minimal",
                         "preset_id": None},
            "risk": "Insert shots need clear motivation — make the detail narratively significant.",
        },
    ],
}


def _mood_key(shot_intent: str) -> str:
    intent_lower = shot_intent.lower()
    if any(w in intent_lower for w in ("tense", "confrontation", "cornered", "threat", "danger", "fear")):
        return "tense"
    if any(w in intent_lower for w in ("warm", "love", "joy", "celebrate", "reunion", "hope")):
        return "warm"
    return "default"


class ShotDesignerAgent(BaseAgent):
    """Translates shot intent into 3 concrete camera + lighting proposals.

    Input dict:
        shot_id (str)              — identifier for the shot
        shot_intent (str)          — one-sentence description of the shot
        scene_mood (dict)          — MoodSpec-like dict (optional)
        character_refs (list)      — list of character reference dicts (optional)
        production_brief (dict)    — tone, style_tokens, creative_direction (optional)
        preset_library (dict)      — available presets (optional; unused in mock)

    Output dict:
        proposals (list[dict])     — exactly 3 proposals, each with:
                                     label, rationale, camera, lighting, risk
    """

    WRITABLE_FIELDS: frozenset[str] = frozenset({"Shot.camera", "Shot.lighting"})
    DIAGNOSTIC_KEYS: frozenset[str] = frozenset({
        "proposals",
    })

    def __init__(self) -> None:
        super().__init__(name="shot_designer_agent")

    def run(self, input: dict) -> dict:  # noqa: A002
        shot_intent = str(input.get("shot_intent") or "")
        key = _mood_key(shot_intent)
        proposals = _PROPOSAL_TEMPLATES[key]
        # Inject shot_id into each proposal for traceability
        shot_id = input.get("shot_id", "")
        tagged = [{**p, "shot_id": shot_id} for p in proposals]
        return {"proposals": tagged}
