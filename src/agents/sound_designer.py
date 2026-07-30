"""SoundDesignerAgent — specifies the sound palette for each scene.

Scope contract (Appendix K.6 of open-production-plan.md):
  Can write:  Shot.audio.sfx (per-shot), Scene.sound_palette (new field)
  Cannot write: Shot.audio.music_cue, Shot.audio.voice_direction, any visual spec

Does NOT mix audio — specifies what sounds should be present and why.

Failure mode: if scene mood is not locked (MoodSpec.locked == False),
returns a needs_mood_lock flag and does not propose a palette.
"""
from __future__ import annotations

from agents.base import BaseAgent

# ---------------------------------------------------------------------------
# Location-type → ambient sound map
# ---------------------------------------------------------------------------

_AMBIENT_MAP = {
    "interior": {
        "warm":       "soft domestic ambience — ticking clock, distant birdsong through glass",
        "cold":       "low fluorescent hum, faint HVAC drone",
        "dramatic":   "deep building resonance, occasional creak of structure",
        "default":    "low room tone, minimal acoustic presence",
    },
    "exterior": {
        "urban":      "distant traffic wash, occasional horn, crowd murmur at threshold",
        "nature":     "wind through leaves, ambient wildlife, no mechanical sound",
        "industrial": "metal resonance, distant machinery, gravel underfoot",
        "default":    "open air ambience, light wind",
    },
    "abstract": {
        "default":    "designed silence — absence of ambient as a stylistic choice",
    },
}

_SFX_SUGGESTIONS = {
    "interior": ["door latch", "footsteps on hard floor", "chair movement", "paper handling"],
    "exterior": ["footsteps on gravel/pavement", "car pass-by", "wind gust", "distant bell"],
    "abstract": ["processed sound design element", "tonal drone", "reverb tail"],
}

_AVOID_MAP = {
    "warm":       ["harsh electronic tones", "dissonant sfx", "busy crowd noise"],
    "cold":       ["warm natural sounds", "birdsong", "organic textures"],
    "dramatic":   ["upbeat incidental music", "casual ambient sounds"],
    "default":    [],
}

_SILENCE_NOTES = {
    "dramatic":   "A beat of complete silence before a key revelation amplifies its weight.",
    "tension":    "Silence between lines of dialogue makes every word cost more.",
    "resolution": "Let the last line breathe in silence before the next scene begins.",
    "default":    "No specific silence beat specified — use room tone throughout.",
}


def _loc_key(location: str) -> str:
    loc = location.lower()
    if any(w in loc for w in ("interior", "indoor", "room", "office", "home", "studio")):
        return "interior"
    if any(w in loc for w in ("exterior", "outdoor", "street", "park", "field", "nature")):
        return "exterior"
    if any(w in loc for w in ("abstract", "void", "stylised", "stylized")):
        return "abstract"
    return "interior"


def _mood_key(text: str) -> str:
    t = text.lower()
    for k in ("warm", "cold", "dramatic", "tension", "resolution", "urban", "nature", "industrial"):
        if k in t:
            return k
    return "default"


class SoundDesignerAgent(BaseAgent):
    """Specifies the sound palette for a scene.

    Input dict:
        scene_id (str)              — identifier
        scene_mood (dict)           — MoodSpec-like dict; needs 'locked': True
                                      and 'emotional_promise' for a full palette
        location (str)              — location name or type
        shot_sequence (list[dict])  — approved shots in the scene (used for sfx count)
        production_brief (dict)     — optional additional context

    Output dict:
        scene_id (str)
        sound_palette (dict)        — ambient, sfx, silence_intent, avoid
        needs_mood_lock (bool)      — True when mood is not locked; palette is
                                      a best-effort draft, not a committed spec
    """

    WRITABLE_FIELDS: frozenset[str] = frozenset({"Shot.audio.sfx", "Scene.sound_palette"})
    DIAGNOSTIC_KEYS: frozenset[str] = frozenset({
        "needs_mood_lock",
        "scene_id",
        "sound_palette",
    })

    def __init__(self) -> None:
        super().__init__(name="sound_designer_agent")

    def run(self, input: dict) -> dict:  # noqa: A002
        scene_id = str(input.get("scene_id") or "unknown")
        scene_mood = input.get("scene_mood") or {}
        location = str(input.get("location") or "interior")
        shot_sequence = list(input.get("shot_sequence") or [])

        mood_locked = bool(scene_mood.get("locked", False))
        emotional_promise = str(scene_mood.get("emotional_promise") or "")
        needs_mood_lock = not mood_locked

        loc_key = _loc_key(location)
        mood_key = _mood_key(emotional_promise)

        # Ambient: pick by location_type → mood sub-key
        ambient_options = _AMBIENT_MAP.get(loc_key, _AMBIENT_MAP["interior"])
        ambient = ambient_options.get(mood_key, ambient_options["default"])

        # SFX: pull from location template, scale to shot count
        sfx_pool = _SFX_SUGGESTIONS.get(loc_key, _SFX_SUGGESTIONS["interior"])
        sfx_count = max(1, min(len(shot_sequence), len(sfx_pool)))
        sfx = sfx_pool[:sfx_count]

        # Silence intent
        silence = _SILENCE_NOTES.get(mood_key, _SILENCE_NOTES["default"])

        # Avoid list
        avoid = _AVOID_MAP.get(mood_key, _AVOID_MAP["default"])

        sound_palette = {
            "ambient": ambient,
            "sfx": sfx,
            "silence_intent": silence,
            "avoid": avoid,
            "rationale": (
                f"Palette derived from location='{location}' "
                f"and emotional_promise='{emotional_promise or 'unspecified'}'."
            ),
        }

        return {
            "scene_id": scene_id,
            "sound_palette": sound_palette,
            "needs_mood_lock": needs_mood_lock,
        }
