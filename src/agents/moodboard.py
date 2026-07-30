"""MoodboardAgent — assembles a moodboard from approved references and locks the tone.

Scope contract (Pipeline Stage 4 of open-production-plan.md):
  Can write:  Scene.mood (MoodSpec) — after human approval
  Cannot write: Shot.camera, Production.characters, Production.environments,
                any generation parameter

Plan gate: "Tone is locked" — the MoodSpec.locked flag must be True before
the production can advance to Stage 5 (Creative Direction).

Two operations:
  "assemble"  — produces 3 moodboard interpretations from approved cluster tokens,
                each yielding a fully-populated MoodSpec proposal.
  "lock"      — marks the chosen MoodSpec as locked and returns the final spec.

Failure mode: if no style_tokens are supplied, the agent sets needs_style_tokens=True
and returns placeholder moodboard proposals rather than blocking entirely.
"""
from __future__ import annotations

from agents.base import BaseAgent

# ---------------------------------------------------------------------------
# Tonal palette templates keyed on dominant visual register
# ---------------------------------------------------------------------------

_MOODBOARD_TEMPLATES = {
    "dark": [
        {
            "emotional_promise": "Oppressive dread building to revelation",
            "tonal_palette": ["deep shadow", "desaturated cool", "intermittent harsh light"],
            "visual_motifs": ["shadow play", "confinement framing", "single key source"],
            "texture_notes": "Rough, industrial, unforgiving surfaces.",
            "pacing_register": "slow, deliberate, tightly controlled",
            "references": [],
            "rationale": (
                "Dark cluster tokens converge on psychological unease. "
                "The moodboard isolates light as a scarce resource, "
                "making its appearance emotionally significant."
            ),
        },
        {
            "emotional_promise": "Night world — familiar spaces made threatening",
            "tonal_palette": ["sodium orange", "deep black", "isolated practicals"],
            "visual_motifs": ["empty streets", "overhead surveillance angle", "wet surfaces"],
            "texture_notes": "Reflective urban surfaces amplify isolation.",
            "pacing_register": "mid-tempo, uneasy, watchful",
            "references": [],
            "rationale": (
                "Sodium practicals and wet reflective surfaces create an urban nocturnal register. "
                "Overhead angles reinforce powerlessness."
            ),
        },
        {
            "emotional_promise": "Grief rendered as visual silence",
            "tonal_palette": ["flat grey", "overcast diffusion", "empty frames"],
            "visual_motifs": ["negative space", "still frames", "absence"],
            "texture_notes": "Soft, featureless surfaces; no hard shadows.",
            "pacing_register": "very slow, meditative",
            "references": [],
            "rationale": (
                "Featureless overcast light and empty frames express emotional numbness. "
                "Absence itself becomes the visual language."
            ),
        },
    ],
    "bright": [
        {
            "emotional_promise": "Vitality and forward movement",
            "tonal_palette": ["warm amber", "golden daylight", "open sky"],
            "visual_motifs": ["expansive horizontals", "upward angles", "warm backlighting"],
            "texture_notes": "Natural, organic textures — wood, foliage, skin.",
            "pacing_register": "energetic, confident, purposeful",
            "references": [],
            "rationale": (
                "Warm amber tones and expansive horizontals signal optimism and forward momentum. "
                "Upward angles reinforce aspiration."
            ),
        },
        {
            "emotional_promise": "Joy as communal experience",
            "tonal_palette": ["high saturation", "midday sun", "bright mixed practicals"],
            "visual_motifs": ["crowd geometry", "shared gaze", "dynamic movement"],
            "texture_notes": "Bold colours; high saturation; no muted tones.",
            "pacing_register": "fast, celebratory, inclusive",
            "references": [],
            "rationale": (
                "High saturation and dynamic movement in crowds signal collective joy. "
                "Shared gaze motifs bind the viewer to the group."
            ),
        },
        {
            "emotional_promise": "Quiet hope in an ordinary moment",
            "tonal_palette": ["soft morning light", "warm neutral", "gentle diffusion"],
            "visual_motifs": ["everyday objects", "close framings", "gentle movement"],
            "texture_notes": "Soft textiles, worn surfaces, lived-in domesticity.",
            "pacing_register": "slow, intimate, observational",
            "references": [],
            "rationale": (
                "Soft morning light and close framings find beauty in the ordinary. "
                "Worn textures ground hope in the tangible."
            ),
        },
    ],
    "neutral": [
        {
            "emotional_promise": "Investigative clarity — let facts speak",
            "tonal_palette": ["clean daylight", "neutral grey", "slight desaturation"],
            "visual_motifs": ["frontal compositions", "unobtrusive camera", "clean backgrounds"],
            "texture_notes": "Plain, non-distracting surfaces. No decorative texture.",
            "pacing_register": "measured, factual, authoritative",
            "references": [],
            "rationale": (
                "Neutral greys and clean daylight signal objectivity. "
                "Frontal composition removes subjectivity from the visual field."
            ),
        },
        {
            "emotional_promise": "Uncertainty held in careful balance",
            "tonal_palette": ["flat diffused light", "mid-grey", "no strong saturation"],
            "visual_motifs": ["balanced symmetry", "ambiguous depth", "central subject"],
            "texture_notes": "Smooth, non-committal surfaces. Ambiguity is the texture.",
            "pacing_register": "even, watchful, suspended",
            "references": [],
            "rationale": (
                "Flat light and balanced symmetry suspend emotional resolution. "
                "The viewer is held in a state of watchful uncertainty."
            ),
        },
        {
            "emotional_promise": "Everyday realism — nothing heightened",
            "tonal_palette": ["natural overcast", "rec709 neutral", "moderate saturation"],
            "visual_motifs": ["natural eye-level", "organic framing", "real environments"],
            "texture_notes": "Whatever is naturally present — no stylisation.",
            "pacing_register": "natural, unmannered, present-tense",
            "references": [],
            "rationale": (
                "Rec709 neutral and natural eye-level framing make no visual argument. "
                "The production world simply exists."
            ),
        },
    ],
}


def _tone_key(style_tokens: list[str], emotional_promise: str) -> str:
    """Derive moodboard family from tokens and emotional promise."""
    combined = " ".join(style_tokens + [emotional_promise]).lower()
    dark_signals = ("dark", "shadow", "night", "oppressive", "grief", "cold",
                    "teal", "desaturated", "alienat")
    bright_signals = ("warm", "golden", "bright", "joy", "hope", "vitality",
                      "sunny", "amber", "energy")
    if any(w in combined for w in dark_signals):
        return "dark"
    if any(w in combined for w in bright_signals):
        return "bright"
    return "neutral"


class MoodboardAgent(BaseAgent):
    """Assembles moodboard proposals from reference clusters and locks the tone.

    Input dict (operation='assemble'):
        operation (str)                — "assemble" (default)
        scene_id (str)                 — target scene identifier
        style_tokens (list[str])       — tokens from ReferenceClusteringAgent proposals
        emotional_promise (str)        — optional seed from intent document
        approved_references (list[str])— URIs of approved reference images
        production_brief (dict)        — optional topic/tone context

    Input dict (operation='lock'):
        operation (str)                — "lock"
        scene_id (str)
        chosen_proposal (dict)         — the proposal the user approved

    Output (assemble):
        proposals (list[dict])         — 3 moodboard interpretations, each with:
                                           emotional_promise, tonal_palette,
                                           visual_motifs, texture_notes,
                                           pacing_register, references, rationale
        scene_id (str)
        needs_style_tokens (bool)      — True when no style_tokens supplied

    Output (lock):
        scene_id (str)
        mood_spec (dict)               — MoodSpec-compatible dict with locked=True
        locked (bool)                  — always True
    """

    WRITABLE_FIELDS: frozenset[str] = frozenset({"Scene.mood"})
    DIAGNOSTIC_KEYS: frozenset[str] = frozenset({
        "proposals",
        "needs_style_tokens",
        "scene_id",
    })

    def __init__(self) -> None:
        super().__init__(name="moodboard_agent")

    def run(self, input: dict) -> dict:  # noqa: A002
        operation = str(input.get("operation") or "assemble")
        if operation == "lock":
            return self._lock(input)
        return self._assemble(input)

    def _assemble(self, input: dict) -> dict:
        scene_id = str(input.get("scene_id") or "unknown")
        style_tokens = list(input.get("style_tokens") or [])
        emotional_promise = str(input.get("emotional_promise") or "")
        approved_references = list(input.get("approved_references") or [])

        needs_style_tokens = not style_tokens

        key = _tone_key(style_tokens, emotional_promise) if style_tokens or emotional_promise else "neutral"
        proposals = [dict(p) for p in _MOODBOARD_TEMPLATES[key]]  # shallow copy each

        # Attach supplied approved references to every proposal
        for p in proposals:
            p["references"] = list(approved_references)
            p["scene_id"] = scene_id

        return {
            "proposals": proposals,
            "scene_id": scene_id,
            "needs_style_tokens": needs_style_tokens,
        }

    def _lock(self, input: dict) -> dict:
        scene_id = str(input.get("scene_id") or "unknown")
        chosen = dict(input.get("chosen_proposal") or {})
        mood_spec = {
            "emotional_promise": chosen.get("emotional_promise", ""),
            "tonal_palette": chosen.get("tonal_palette", []),
            "references": chosen.get("references", []),
            "locked": True,
        }
        return {
            "scene_id": scene_id,
            "mood_spec": mood_spec,
            "locked": True,
        }
