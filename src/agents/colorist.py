"""ColoristAgent — proposes color grades for scenes.

Scope contract (Appendix K.9 of open-production-plan.md):
  Can write:  Shot.color_spec (new field), Scene.color_look (new field)
  Cannot write: any generation parameter, camera spec, character spec

Always returns exactly 3 proposals (1 primary + 2 alternatives).

Failure mode: if the scene has no MoodSpec.emotional_promise, the agent
sets needs_emotional_promise=True and returns placeholder proposals
rather than blocking entirely.
"""
from __future__ import annotations

from agents.base import BaseAgent

# ---------------------------------------------------------------------------
# Emotional intent → colour grade template map
# ---------------------------------------------------------------------------

_GRADE_TEMPLATES = {
    "cold": [
        {
            "look_name": "Institutional Cold",
            "reference_frame": "fluorescent-lit corridor, desaturated blues",
            "primary": {
                "lift": "dark shadows, crushed blacks",
                "gamma": "blue-grey midtones",
                "gain": "cool whites, near-clipped highlights",
                "saturation": 0.65,
            },
            "creative": {
                "shadow_tint": "blue-green",
                "highlight_tint": "pale cyan",
                "skin_tone_preservation": True,
                "lut": "teal-orange_invert",
            },
            "rationale": (
                "Desaturated blues and crushed blacks create psychological distance "
                "and institutional oppression. Skin tones are preserved but pushed cool."
            ),
        },
        {
            "look_name": "Moonlight Bleach",
            "reference_frame": "moonlit exterior, silver-grey tones",
            "primary": {
                "lift": "mid-level blacks, no crush",
                "gamma": "neutral grey midtones",
                "gain": "near-white, slight blue cast",
                "saturation": 0.55,
            },
            "creative": {
                "shadow_tint": "indigo",
                "highlight_tint": "cold white",
                "skin_tone_preservation": False,
                "lut": "bleach_bypass_cool",
            },
            "rationale": (
                "Bleach-bypass emulation removes warmth entirely. "
                "Works when alienation is the primary emotional register."
            ),
        },
        {
            "look_name": "Clinical Teal",
            "reference_frame": "operating-theatre lighting, sharp teal cast",
            "primary": {
                "lift": "black with teal push",
                "gamma": "midtone teal",
                "gain": "white with slight cyan",
                "saturation": 0.70,
            },
            "creative": {
                "shadow_tint": "teal",
                "highlight_tint": "near-white",
                "skin_tone_preservation": True,
                "lut": "teal_clinical",
            },
            "rationale": (
                "Clinical teal signals precision and menace without the full "
                "desaturation of bleach-bypass. Retains skin tones for character legibility."
            ),
        },
    ],
    "warm": [
        {
            "look_name": "Golden Hour Memory",
            "reference_frame": "warm afternoon interior, amber window light",
            "primary": {
                "lift": "warm shadows, amber undertone",
                "gamma": "lifted midtones, golden cast",
                "gain": "warm white, slightly clipped",
                "saturation": 1.05,
            },
            "creative": {
                "shadow_tint": "amber-brown",
                "highlight_tint": "warm gold",
                "skin_tone_preservation": True,
                "lut": "golden_hour_warm",
            },
            "rationale": (
                "Lifted warm midtones and golden highlights evoke nostalgia and safety. "
                "Saturation slightly boosted to reinforce emotional fullness."
            ),
        },
        {
            "look_name": "Soft Candle",
            "reference_frame": "candlelit room, intimate and low-key",
            "primary": {
                "lift": "warm dark blacks",
                "gamma": "orange-amber midtones",
                "gain": "warm cream whites",
                "saturation": 0.95,
            },
            "creative": {
                "shadow_tint": "deep amber",
                "highlight_tint": "cream",
                "skin_tone_preservation": True,
                "lut": "candle_low_key",
            },
            "rationale": (
                "Low-key amber palette creates intimacy and vulnerability. "
                "Works best for dialogue-heavy scenes between two characters."
            ),
        },
        {
            "look_name": "Warm Contrast",
            "reference_frame": "strong sunlight, rich contrast, saturated warm",
            "primary": {
                "lift": "dark blacks",
                "gamma": "warm golden midtones",
                "gain": "bright warm whites",
                "saturation": 1.10,
            },
            "creative": {
                "shadow_tint": "orange-brown",
                "highlight_tint": "bright gold",
                "skin_tone_preservation": True,
                "lut": "warm_high_contrast",
            },
            "rationale": (
                "High contrast and saturation signal vitality and emotional peaks. "
                "Use for scenes of triumph, reunion, or revelation."
            ),
        },
    ],
    "neutral": [
        {
            "look_name": "Balanced Naturalistic",
            "reference_frame": "overcast daylight, even exposure",
            "primary": {
                "lift": "neutral blacks",
                "gamma": "neutral midtones",
                "gain": "clean whites",
                "saturation": 0.90,
            },
            "creative": {
                "shadow_tint": "none",
                "highlight_tint": "none",
                "skin_tone_preservation": True,
                "lut": "rec709_natural",
            },
            "rationale": (
                "Unobtrusive naturalistic grade lets performance and production "
                "design carry the scene. Slight saturation reduction avoids video look."
            ),
        },
        {
            "look_name": "Desaturated Documentary",
            "reference_frame": "natural documentary style, no stylisation",
            "primary": {
                "lift": "lifted blacks",
                "gamma": "neutral-grey midtones",
                "gain": "clean diffuse whites",
                "saturation": 0.80,
            },
            "creative": {
                "shadow_tint": "faint cool",
                "highlight_tint": "none",
                "skin_tone_preservation": True,
                "lut": "documentary_flat",
            },
            "rationale": (
                "Lifted blacks reduce contrast for an observational quality. "
                "Used when the content should feel credible and unmanipulated."
            ),
        },
        {
            "look_name": "Print Film Emulation",
            "reference_frame": "Kodak Vision3 emulation, slight grain",
            "primary": {
                "lift": "warm dark blacks",
                "gamma": "neutral warm midtones",
                "gain": "creamy whites",
                "saturation": 0.92,
            },
            "creative": {
                "shadow_tint": "faint green",
                "highlight_tint": "faint warm",
                "skin_tone_preservation": True,
                "lut": "kodak_vision3",
            },
            "rationale": (
                "Film emulation adds organic warmth and mild desaturation. "
                "Slightly greened shadows evoke photochemical colour science."
            ),
        },
    ],
}


def _grade_key(emotional_intent: str) -> str:
    intent = emotional_intent.lower()
    if any(w in intent for w in ("cold", "clinical", "oppressive", "alienat", "institutional")):
        return "cold"
    if any(w in intent for w in ("warm", "intimate", "nostalgic", "joy", "hope", "love")):
        return "warm"
    return "neutral"


class ColoristAgent(BaseAgent):
    """Proposes 3 color grades for a scene (1 primary + 2 alternatives).

    Input dict:
        scene_id (str)              — identifier
        emotional_intent (str)      — "oppressive institutional cold" / "intimate warmth"
        reference_frames (list[str])— URIs of reference images (stored in proposals)
        shots (list[dict])          — approved shots (used for shot count context)
        production_brief (dict)     — optional tone/style context

    Output dict:
        scene_id (str)
        proposals (list[dict])      — exactly 3 proposals, each with:
                                       look_name, reference_frame, primary,
                                       creative, rationale
        needs_emotional_promise (bool)  — True when emotional_intent was empty;
                                          proposals are placeholder-grade only
    """

    WRITABLE_FIELDS: frozenset[str] = frozenset({"Shot.color_spec", "Scene.color_look"})
    DIAGNOSTIC_KEYS: frozenset[str] = frozenset({
        "needs_emotional_promise",
        "proposals",
        "scene_id",
    })

    def __init__(self) -> None:
        super().__init__(name="colorist_agent")

    def run(self, input: dict) -> dict:  # noqa: A002
        scene_id = str(input.get("scene_id") or "unknown")
        emotional_intent = str(input.get("emotional_intent") or "")
        reference_frames = list(input.get("reference_frames") or [])
        shots = list(input.get("shots") or [])

        needs_emotional_promise = not emotional_intent.strip()
        key = _grade_key(emotional_intent) if emotional_intent.strip() else "neutral"

        proposals = list(_GRADE_TEMPLATES[key])  # copy — always 3

        # Attach user-supplied reference frames to first proposal if provided
        if reference_frames:
            proposals[0] = {**proposals[0], "reference_frame": reference_frames[0]}

        # Annotate with scene context
        for p in proposals:
            p["scene_id"] = scene_id
            p["shot_count"] = len(shots)

        return {
            "scene_id": scene_id,
            "proposals": proposals,
            "needs_emotional_promise": needs_emotional_promise,
        }
