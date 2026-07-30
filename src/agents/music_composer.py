"""MusicComposerAgent — creates music cue briefs for each scene.

Scope contract (Appendix K.7 of open-production-plan.md):
  Can write:  Scene.music_cue, Timeline.music_cues (after human approval)
  Cannot write: Shot.audio.sfx, Shot.audio.voice_direction, any visual spec

Does NOT compose music — writes implementation-ready briefs for a music
generation system (Suno, Udio, etc.) or a human composer.

Failure mode: if scene_duration_sec is not set (0 or None), proposes a
"flexible duration" cue with open in/out markers rather than blocking.
"""
from __future__ import annotations

from agents.base import BaseAgent

# ---------------------------------------------------------------------------
# Narrative function → music brief templates
# ---------------------------------------------------------------------------

_BRIEFS = {
    "escalation": {
        "tempo_range": "90–120 BPM, gradually accelerating",
        "instrumentation": "low strings, sparse percussion building to full ensemble",
        "dynamic_arc": "Begins nearly inaudible; swells through the scene; peaks on the climactic cut.",
        "avoid": ["major key resolutions", "acoustic guitar", "light percussion"],
        "reference_tracks": [
            "Jonny Greenwood — 'There Will Be Blood' suite (sounds like that but less dissonant)",
            "Ennio Morricone — escalation motifs without the period feel",
        ],
        "cue_in": "First frame of scene",
        "cue_out": "Hard cut on scene end",
    },
    "resolution": {
        "tempo_range": "60–75 BPM, rubato",
        "instrumentation": "solo piano with sparse cello undertone; no rhythm section",
        "dynamic_arc": "Enters softly mid-scene; holds steady; fades on final dialogue line.",
        "avoid": ["drums", "electric instruments", "abrupt endings"],
        "reference_tracks": [
            "Nils Frahm — 'Says' (sounds like that but shorter and more contained)",
            "Max Richter — piano solo texture without the looping structure",
        ],
        "cue_in": "After first dialogue exchange",
        "cue_out": "Fade over final 8 seconds of scene",
    },
    "transition": {
        "tempo_range": "80–100 BPM, steady",
        "instrumentation": "single texture instrument (synth pad or sustained strings), no melody",
        "dynamic_arc": "Brief — enters at scene end, carries through the cut, resolves in new scene.",
        "avoid": ["strong melody", "lyrics", "prominent rhythm"],
        "reference_tracks": [
            "Brian Eno — ambient texture (sounds like that but with more forward motion)",
        ],
        "cue_in": "Final 4 seconds of outgoing scene",
        "cue_out": "First 4 seconds of incoming scene",
    },
    "tension": {
        "tempo_range": "No fixed tempo — pulse-based or rubato",
        "instrumentation": "low strings col legno, extended techniques, prepared piano taps",
        "dynamic_arc": "Constant low-level unease; micro-swells on specific beats; never resolves.",
        "avoid": ["major chords", "recognisable melody", "regular meter"],
        "reference_tracks": [
            "Jóhann Jóhannsson — 'Arrival' score texture without the choir",
            "Disasterpeace — 'It Follows' pulsing dread without the 80s synth surface",
        ],
        "cue_in": "Scene start — already present when picture cuts in",
        "cue_out": "Abrupt silence on reveal moment",
    },
    "default": {
        "tempo_range": "70–90 BPM, neutral",
        "instrumentation": "light orchestral texture; piano lead; ambient strings",
        "dynamic_arc": "Neutral presence throughout scene; does not compete with dialogue.",
        "avoid": ["loud passages during dialogue", "abrupt tempo changes"],
        "reference_tracks": [
            "Thomas Newman — understated scene underscore (quiet, motivic)",
        ],
        "cue_in": "Scene start",
        "cue_out": "Scene end",
    },
}


def _function_key(narrative_function: str) -> str:
    nf = narrative_function.lower()
    for key in ("escalation", "resolution", "transition", "tension"):
        if key in nf:
            return key
    return "default"


class MusicComposerAgent(BaseAgent):
    """Generates a music cue brief for a scene.

    Input dict:
        scene_id (str)              — identifier
        scene_mood (dict)           — MoodSpec-like dict (optional, used for colour)
        scene_duration_sec (float)  — total scene duration; 0 / None → flexible
        narrative_function (str)    — "escalation" | "resolution" | "transition" | "tension"
        production_brief (dict)     — optional additional context

    Output dict:
        scene_id (str)
        music_brief (dict)          — tempo_range, instrumentation, dynamic_arc,
                                      avoid, reference_tracks, cue_in, cue_out,
                                      rationale, flexible_duration (bool)
    """

    WRITABLE_FIELDS: frozenset[str] = frozenset({"Scene.music_cue", "Timeline.music_cues"})
    DIAGNOSTIC_KEYS: frozenset[str] = frozenset({
        "music_brief",
        "scene_id",
    })

    def __init__(self) -> None:
        super().__init__(name="music_composer_agent")

    def run(self, input: dict) -> dict:  # noqa: A002
        scene_id = str(input.get("scene_id") or "unknown")
        narrative_function = str(input.get("narrative_function") or "")
        scene_duration_sec = input.get("scene_duration_sec")
        scene_mood = input.get("scene_mood") or {}
        emotional_promise = str(scene_mood.get("emotional_promise") or "")

        key = _function_key(narrative_function or emotional_promise)
        template = _BRIEFS[key]

        # Failure mode: no duration → flexible brief
        flexible = not scene_duration_sec  # None or 0 → True

        brief = {
            **template,
            "rationale": (
                f"Brief derived from narrative_function='{narrative_function or 'unspecified'}' "
                f"({'flexible duration' if flexible else f'{scene_duration_sec}s scene'})."
            ),
            "flexible_duration": flexible,
        }

        if flexible:
            brief["cue_in"] = "Flexible — enter when picture suggests"
            brief["cue_out"] = "Flexible — hold until natural resolution"

        return {
            "scene_id": scene_id,
            "music_brief": brief,
        }
