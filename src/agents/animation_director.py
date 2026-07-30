"""AnimationDirectorAgent — specifies per-shot motion and scene transition specs.

Scope contract (Stage 18 of open-production-plan.md):
  Can write:  Shot.motion_spec (new field), Timeline.transitions
  Cannot write: Shot.camera, Shot.generation, any audio spec

Always returns exactly 3 motion proposals.

Gate: once the user approves a proposal and calls run() with op='lock',
the agent returns motion_locked=True and writes the approved spec to the
output 'motion_spec' key.

Failure mode: if the edit assembly has not been locked (no shot_sequence
supplied), returns needs_edit_lock=True and proposals are placeholder drafts
rather than committed motion specs.
"""
from __future__ import annotations

from agents.base import BaseAgent

# ---------------------------------------------------------------------------
# Scene-type → motion primitive templates
# ---------------------------------------------------------------------------

_MOTION_TEMPLATES = {
    "action": [
        {
            "label": "Kinetic Whip-Pan Sequence",
            "motion_primitives": [
                {"shot_position": "all", "movement": "whip_pan", "duration_frames": 4,
                 "easing": "ease-in-out", "hold_frames": 0},
            ],
            "transition_specs": [
                {"type": "smash_cut", "duration_frames": 0, "rationale": "Zero-frame hard cut maximises impact."},
                {"type": "match_cut", "duration_frames": 2, "rationale": "Match-cut on matching motion vectors."},
            ],
            "motion_intensity": "high",
            "rationale": (
                "Whip-pan movements with smash cuts eliminate dead air and sustain "
                "kinetic energy throughout the action sequence."
            ),
        },
        {
            "label": "Push-In Escalation",
            "motion_primitives": [
                {"shot_position": "all", "movement": "push_in", "duration_frames": 24,
                 "easing": "ease-in", "hold_frames": 6},
            ],
            "transition_specs": [
                {"type": "cut", "duration_frames": 0, "rationale": "Hard cut on push-in apex creates urgency."},
                {"type": "cut", "duration_frames": 0, "rationale": "Second hard cut sustains the escalation."},
            ],
            "motion_intensity": "high",
            "rationale": (
                "Progressive push-in moves accelerate audience engagement; "
                "cutting at the movement apex prevents the shot from relaxing."
            ),
        },
        {
            "label": "Handheld Chase",
            "motion_primitives": [
                {"shot_position": "all", "movement": "handheld", "duration_frames": 48,
                 "easing": "none", "hold_frames": 0},
            ],
            "transition_specs": [
                {"type": "cut", "duration_frames": 0, "rationale": "Raw hard cuts match handheld instability."},
                {"type": "cut", "duration_frames": 0, "rationale": "Consistent hard cuts keep viewer in pursuit mode."},
            ],
            "motion_intensity": "high",
            "rationale": (
                "Handheld instability places the viewer inside the action; "
                "hard cuts prevent the camera from settling."
            ),
        },
    ],
    "dialogue": [
        {
            "label": "Static Anchor with Slow Push",
            "motion_primitives": [
                {"shot_position": "all", "movement": "slow_push_in", "duration_frames": 96,
                 "easing": "ease-in-out", "hold_frames": 24},
            ],
            "transition_specs": [
                {"type": "cut", "duration_frames": 0, "rationale": "Clean cut between dialogue blocks."},
                {"type": "cut", "duration_frames": 0, "rationale": "Clean cut to reaction shot."},
            ],
            "motion_intensity": "low",
            "rationale": (
                "A barely perceptible push-in over a long dialogue beat creates "
                "growing intimacy without distracting from the performance."
            ),
        },
        {
            "label": "Locked-Off Coverage",
            "motion_primitives": [
                {"shot_position": "all", "movement": "static", "duration_frames": 0,
                 "easing": "none", "hold_frames": 0},
            ],
            "transition_specs": [
                {"type": "cut", "duration_frames": 0, "rationale": "Invisible cut on new speaker."},
                {"type": "cut", "duration_frames": 0, "rationale": "Invisible cut to reaction."},
            ],
            "motion_intensity": "none",
            "rationale": (
                "Locked-off camera removes all visual noise and makes "
                "performance the sole focus."
            ),
        },
        {
            "label": "Subtle Arc with Dissolve",
            "motion_primitives": [
                {"shot_position": "all", "movement": "arc", "duration_frames": 72,
                 "easing": "ease-in-out", "hold_frames": 12},
            ],
            "transition_specs": [
                {"type": "dissolve", "duration_frames": 18, "rationale": "Soft dissolve eases between emotional beats."},
                {"type": "cut", "duration_frames": 0, "rationale": "Hard cut to reaction maintains continuity."},
            ],
            "motion_intensity": "low",
            "rationale": (
                "A slow circular arc shifts the power dynamic between speakers "
                "while dissolves soften time pressure."
            ),
        },
    ],
    "montage": [
        {
            "label": "Rhythmic Match-Cut Montage",
            "motion_primitives": [
                {"shot_position": "all", "movement": "static", "duration_frames": 12,
                 "easing": "none", "hold_frames": 0},
            ],
            "transition_specs": [
                {"type": "match_cut", "duration_frames": 2, "rationale": "Match-cuts create graphic rhymes across shots."},
                {"type": "cut", "duration_frames": 0, "rationale": "Hard cut to contrasting element."},
                {"type": "match_cut", "duration_frames": 2, "rationale": "Second match-cut closes the graphic loop."},
            ],
            "motion_intensity": "medium",
            "rationale": (
                "Match-cuts between visually rhyming frames create subconscious "
                "narrative connections across the montage."
            ),
        },
        {
            "label": "Slow-Motion Drift",
            "motion_primitives": [
                {"shot_position": "all", "movement": "dolly", "duration_frames": 60,
                 "easing": "ease-in-out", "hold_frames": 18},
            ],
            "transition_specs": [
                {"type": "cross_fade", "duration_frames": 24, "rationale": "Long cross-fade layers emotional states."},
                {"type": "cross_fade", "duration_frames": 24, "rationale": "Continued cross-fade maintains reverie."},
            ],
            "motion_intensity": "low",
            "rationale": (
                "Slow dollies with long cross-fades create a dreamlike passage of time "
                "suited to memory or nostalgia montages."
            ),
        },
        {
            "label": "Split-Rhythm Jump Cuts",
            "motion_primitives": [
                {"shot_position": "all", "movement": "static", "duration_frames": 8,
                 "easing": "none", "hold_frames": 0},
            ],
            "transition_specs": [
                {"type": "jump_cut", "duration_frames": 0, "rationale": "Jump cuts create fragmented temporal energy."},
                {"type": "jump_cut", "duration_frames": 0, "rationale": "Second jump cut compounds disorientation."},
                {"type": "cut", "duration_frames": 0, "rationale": "Final hard cut as resolution anchor."},
            ],
            "motion_intensity": "medium",
            "rationale": (
                "Jump cuts in a montage deliberately break continuity; "
                "useful when urgency or anxiety is the montage's emotional register."
            ),
        },
    ],
    "default": [
        {
            "label": "Standard Coverage",
            "motion_primitives": [
                {"shot_position": "all", "movement": "static", "duration_frames": 0,
                 "easing": "none", "hold_frames": 0},
            ],
            "transition_specs": [
                {"type": "cut", "duration_frames": 0, "rationale": "Clean invisible cuts for readable coverage."},
                {"type": "cut", "duration_frames": 0, "rationale": "Consistent cuts maintain scene clarity."},
            ],
            "motion_intensity": "none",
            "rationale": "Clean static coverage — motion does not compete with content.",
        },
        {
            "label": "Gentle Drift",
            "motion_primitives": [
                {"shot_position": "all", "movement": "dolly", "duration_frames": 72,
                 "easing": "ease-in-out", "hold_frames": 12},
            ],
            "transition_specs": [
                {"type": "cut", "duration_frames": 0, "rationale": "Hard cut prevents drift from becoming distraction."},
                {"type": "dissolve", "duration_frames": 12, "rationale": "Short dissolve softens the end of scene."},
            ],
            "motion_intensity": "low",
            "rationale": "A slow dolly adds cinematic movement without overpowering the content.",
        },
        {
            "label": "Pull-Out Reveal",
            "motion_primitives": [
                {"shot_position": "first", "movement": "pull_out", "duration_frames": 48,
                 "easing": "ease-out", "hold_frames": 24},
                {"shot_position": "rest", "movement": "static", "duration_frames": 0,
                 "easing": "none", "hold_frames": 0},
            ],
            "transition_specs": [
                {"type": "cut", "duration_frames": 0, "rationale": "Hard cut from reveal to remaining coverage."},
                {"type": "cut", "duration_frames": 0, "rationale": "Hard cut maintains reveal momentum."},
            ],
            "motion_intensity": "medium",
            "rationale": (
                "An opening pull-out contextualises the scene spatially; "
                "subsequent static coverage keeps focus on content."
            ),
        },
    ],
}


def _scene_type_key(scene_type: str) -> str:
    t = scene_type.lower()
    if any(w in t for w in ("action", "chase", "fight", "battle", "run", "urgent")):
        return "action"
    if any(w in t for w in ("dialogue", "conversation", "interview", "talk", "debate")):
        return "dialogue"
    if any(w in t for w in ("montage", "sequence", "collage", "memory", "nostalgic")):
        return "montage"
    return "default"


class AnimationDirectorAgent(BaseAgent):
    """Specifies motion primitives and transition specs for each shot in a scene.

    Input dict (propose op):
        op (str)                    — 'propose' (default) or 'lock'
        scene_id (str)              — identifier
        scene_type (str)            — 'action' / 'dialogue' / 'montage' / or free text
        shot_sequence (list[dict])  — shots in edit order (each needs an 'id' key)
        edit_locked (bool)          — True when EditorAgent has locked the assembly
        production_brief (dict)     — optional tone/style context

    Input dict (lock op — call after user selects a proposal):
        op (str)                    — 'lock'
        scene_id (str)
        approved_proposal (dict)    — the proposal dict the user approved

    Output dict:
        scene_id (str)
        proposals (list[dict])      — exactly 3 proposals (propose op), each with:
                                       label, motion_primitives, transition_specs,
                                       motion_intensity, rationale
        motion_locked (bool)        — True only after 'lock' op
        motion_spec (dict | None)   — populated after 'lock' op with the approved spec
        needs_edit_lock (bool)      — True when shot_sequence is empty (edit not locked)
    """

    WRITABLE_FIELDS: frozenset[str] = frozenset({"Shot.motion_spec", "Timeline.transitions"})
    DIAGNOSTIC_KEYS: frozenset[str] = frozenset({
        "scene_id",
        "proposals",
        "motion_locked",
        "motion_spec",
        "needs_edit_lock",
    })

    def __init__(self) -> None:
        super().__init__(name="animation_director_agent")

    def run(self, input: dict) -> dict:  # noqa: A002
        op = str(input.get("op") or "propose")
        scene_id = str(input.get("scene_id") or "unknown")
        shot_sequence = list(input.get("shot_sequence") or [])
        edit_locked = bool(input.get("edit_locked", False))

        needs_edit_lock = not shot_sequence and not edit_locked

        if op == "lock":
            approved = input.get("approved_proposal") or {}
            motion_spec = {
                "scene_id": scene_id,
                **approved,
                "locked": True,
            }
            return self._enforce_scope({
                "scene_id": scene_id,
                "proposals": [],
                "motion_locked": True,
                "motion_spec": motion_spec,
                "needs_edit_lock": False,
            })

        # propose op
        scene_type = str(input.get("scene_type") or "")
        key = _scene_type_key(scene_type)
        # Annotate each proposal with scene context (shallow-copy to avoid mutating templates)
        proposals = [
            {**p, "scene_id": scene_id, "shot_count": len(shot_sequence)}
            for p in _MOTION_TEMPLATES[key]
        ]

        return self._enforce_scope({
            "scene_id": scene_id,
            "proposals": proposals,
            "motion_locked": False,
            "motion_spec": None,
            "needs_edit_lock": needs_edit_lock,
        })
