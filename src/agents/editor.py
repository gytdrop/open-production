"""EditorAgent — proposes cut assembly for an approved shot set.

Scope contract (Appendix K.8 of open-production-plan.md):
  Can write:  Timeline.scene_order, Shot.duration_sec (non-destructively)
  Cannot write: Shot.generation, Shot.camera, any generation parameter

Always returns exactly 3 cut proposals. Fewer than 3 approved shots returns
a single-shot proposal flagged with a coverage warning.
"""
from __future__ import annotations

from agents.base import BaseAgent

# ---------------------------------------------------------------------------
# Edit style templates keyed on narrative_intent mood
# ---------------------------------------------------------------------------

_EDIT_STYLES = {
    "fast": [
        {
            "label": "Fast cross-cut, escalating",
            "transitions_template": ["cut", "cut", "match_cut"],
            "duration_scale": 0.6,   # relative to target_duration
            "rationale": "Rapid cuts build urgency and mirror accelerating stakes.",
        },
        {
            "label": "Jump-cut montage",
            "transitions_template": ["jump_cut", "jump_cut", "cut"],
            "duration_scale": 0.5,
            "rationale": "Jump cuts create nervous energy and a fragmented sense of time.",
        },
        {
            "label": "Hard-cut action sequence",
            "transitions_template": ["cut", "cut", "cut"],
            "duration_scale": 0.7,
            "rationale": "Pure hard cuts maintain maximum kinetic energy through the sequence.",
        },
    ],
    "slow": [
        {
            "label": "Slow dissolve contemplative",
            "transitions_template": ["dissolve", "dissolve", "fade"],
            "duration_scale": 1.4,
            "rationale": "Dissolves soften temporal boundaries and create a meditative pace.",
        },
        {
            "label": "Sustained wide with single cut",
            "transitions_template": ["cut"],
            "duration_scale": 1.8,
            "rationale": "Long takes allow emotional weight to accumulate before cutting.",
        },
        {
            "label": "Gentle cross-fade sequence",
            "transitions_template": ["cross_fade", "cross_fade", "dissolve"],
            "duration_scale": 1.5,
            "rationale": "Cross-fades layer emotional states and ease transitions.",
        },
    ],
    "default": [
        {
            "label": "Balanced coverage edit",
            "transitions_template": ["cut", "cut", "cut"],
            "duration_scale": 1.0,
            "rationale": "Standard coverage edit — clear, readable, matches dialogue pacing.",
        },
        {
            "label": "Parallel cross-cut",
            "transitions_template": ["cut", "dissolve", "cut"],
            "duration_scale": 1.0,
            "rationale": "Alternating perspectives create implicit comparison or tension.",
        },
        {
            "label": "Shot-reverse-shot with insert",
            "transitions_template": ["cut", "cut", "match_cut"],
            "duration_scale": 0.9,
            "rationale": "Classic coverage pattern with a detail insert for emphasis.",
        },
    ],
}


def _intent_key(narrative_intent: str) -> str:
    intent_lower = narrative_intent.lower()
    if any(w in intent_lower for w in ("fast", "urgent", "action", "chase", "escalat")):
        return "fast"
    if any(w in intent_lower for w in ("slow", "contemplat", "grief", "melanchol", "quiet")):
        return "slow"
    return "default"


class EditorAgent(BaseAgent):
    """Proposes cut assembly for an approved shot set.

    Input dict:
        scene_id (str)              — identifier of the scene
        shots (list[dict])          — approved shots (each needs an 'id' key)
        narrative_intent (str)      — what the edit should feel like
        target_duration_sec (float) — target total scene duration
        music_cue (dict | None)     — optional music brief

    Output dict:
        proposals (list[dict])      — up to 3 cut proposals, each with:
                                      label, shot_sequence, durations,
                                      transitions, rationale, total_duration_sec
        coverage_warning (str | None) — set if shots < 3
    """

    WRITABLE_FIELDS: frozenset[str] = frozenset({"Timeline.scene_order", "Shot.duration_sec"})
    DIAGNOSTIC_KEYS: frozenset[str] = frozenset({
        "coverage_warning",
        "proposals",
    })

    def __init__(self) -> None:
        super().__init__(name="editor_agent")

    def run(self, input: dict) -> dict:  # noqa: A002
        shots = input.get("shots") or []
        narrative_intent = str(input.get("narrative_intent") or "")
        target_sec = float(input.get("target_duration_sec") or 30.0)
        scene_id = str(input.get("scene_id") or "")

        shot_ids = [s.get("id", f"shot-{i}") for i, s in enumerate(shots)]
        coverage_warning: str | None = None

        if len(shot_ids) < 3:
            coverage_warning = (
                f"Only {len(shot_ids)} approved shot(s) in scene '{scene_id}'. "
                "Coverage is thin — more shots recommended."
            )

        if not shot_ids:
            return {
                "proposals": [],
                "coverage_warning": coverage_warning or "No shots provided.",
            }

        key = _intent_key(narrative_intent)
        templates = _EDIT_STYLES[key]
        proposals = []
        for tmpl in templates:
            seq = shot_ids if len(shot_ids) >= 2 else shot_ids * 2
            scale = tmpl["duration_scale"]
            n = len(seq)
            per_shot = (target_sec * scale) / n if n else target_sec
            durations = [round(per_shot, 2)] * n
            # Build transitions list (n-1 transitions for n shots)
            trans_tmpl = tmpl["transitions_template"]
            transitions = [trans_tmpl[i % len(trans_tmpl)] for i in range(max(0, n - 1))]
            proposals.append({
                "label": tmpl["label"],
                "shot_sequence": seq,
                "durations": durations,
                "transitions": transitions,
                "rationale": tmpl["rationale"],
                "total_duration_sec": round(sum(durations), 2),
                "scene_id": scene_id,
            })
            if len(proposals) == 3:
                break

        return {"proposals": proposals, "coverage_warning": coverage_warning}
