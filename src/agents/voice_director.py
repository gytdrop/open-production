"""VoiceDirectorAgent — specifies voice performance for each character's lines.

Scope contract (Appendix K.5 of open-production-plan.md):
  Can write:  Shot.audio.voice_direction (after human approval)
  Cannot write: Production.characters, camera specs, any visual spec

Does NOT generate voice — specifies what the voice should do (emotion,
pace, emphasis, subtext) so a voice-generation backend or a human actor
can execute it faithfully.

Failure mode: if character has no voice spec, proposes a base voice
profile from the character_brief before attempting per-line direction.
"""
from __future__ import annotations

from agents.base import BaseAgent

# ---------------------------------------------------------------------------
# Emotion / pace lookup tables keyed on scene_mood or character_brief signal
# ---------------------------------------------------------------------------

_EMOTION_MAP = {
    "grief":       {"emotion": "restrained grief",      "pace": "slow, deliberate"},
    "fear":        {"emotion": "controlled fear",        "pace": "clipped, breathless"},
    "anger":       {"emotion": "suppressed anger",       "pace": "tight, measured"},
    "authority":   {"emotion": "cold authority",         "pace": "steady, unhurried"},
    "joy":         {"emotion": "open warmth",            "pace": "bright, lifted"},
    "tension":     {"emotion": "barely-contained dread", "pace": "staccato, halting"},
    "resolution":  {"emotion": "quiet relief",           "pace": "slow, releasing"},
    "default":     {"emotion": "neutral presence",       "pace": "conversational"},
}


def _mood_key(text: str) -> str:
    t = text.lower()
    for key in ("grief", "fear", "anger", "authority", "joy", "tension", "resolution"):
        if key in t:
            return key
    return "default"


def _first_words(line: str, n: int = 2) -> list[str]:
    """Return the first n content words as default emphasis candidates."""
    words = [w.strip(".,!?;:\"'") for w in line.split() if w.strip(".,!?;:\"'")]
    return words[:n]


def _build_direction(line: str, mood_key: str) -> dict:
    profile = _EMOTION_MAP[mood_key]
    return {
        "line": line,
        "emotion": profile["emotion"],
        "pace": profile["pace"],
        "emphasis": _first_words(line),
        "subtext": f"The character is communicating more than the words say — {profile['emotion']}.",
    }


class VoiceDirectorAgent(BaseAgent):
    """Specifies per-line voice performance for a character.

    Input dict:
        character_id (str)          — identifier of the character
        script_lines (list[str])    — lines to direct
        scene_mood (dict)           — MoodSpec-like dict with 'emotional_promise'
        character_brief (str)       — the character's emotional state in this scene

    Output dict:
        voice_direction (list[dict])  — one entry per line:
                                         line, emotion, pace, emphasis, subtext
        voice_profile (dict | None)   — set when no voice spec is available;
                                        proposes a base profile from character_brief
    """

    WRITABLE_FIELDS: frozenset[str] = frozenset({"Shot.audio.voice_direction"})
    DIAGNOSTIC_KEYS: frozenset[str] = frozenset({
        "character_id",
        "voice_direction",
        "voice_profile",
    })

    def __init__(self) -> None:
        super().__init__(name="voice_director_agent")

    def run(self, input: dict) -> dict:  # noqa: A002
        character_id = str(input.get("character_id") or "unknown")
        script_lines = list(input.get("script_lines") or [])
        scene_mood = input.get("scene_mood") or {}
        character_brief = str(input.get("character_brief") or "")

        # Derive mood key from scene_mood.emotional_promise or character_brief
        mood_text = str(scene_mood.get("emotional_promise") or character_brief)
        key = _mood_key(mood_text)

        voice_direction = [_build_direction(line, key) for line in script_lines]

        # If no lines provided, still return a valid empty direction
        result: dict = {
            "character_id": character_id,
            "voice_direction": voice_direction,
        }

        # Failure mode: no script lines supplied — propose a voice profile instead
        if not script_lines:
            result["voice_profile"] = self._propose_voice_profile(character_brief, key)
        else:
            result["voice_profile"] = None

        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _propose_voice_profile(character_brief: str, mood_key: str) -> dict:
        """Base voice profile when no script lines are available."""
        profile = _EMOTION_MAP[mood_key]
        return {
            "rationale": (
                f"No script lines provided. "
                f"Proposed base voice profile from character brief: '{character_brief[:80]}'."
            ),
            "default_emotion": profile["emotion"],
            "default_pace": profile["pace"],
            "note": "Lock a voice profile before running per-line direction.",
        }
