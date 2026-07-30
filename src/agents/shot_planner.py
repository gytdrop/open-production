"""ShotPlanningAgent — decomposes a scene/script excerpt into a shot list.

Scope contract (Appendix K.1-ext of open-production-plan.md):
  Can write:  Scene.shots (new Shot records — after human approval)
  Cannot write: Shot.camera, Shot.lighting, Production.characters,
                Production.environments, Scene.mood

This agent sits UPSTREAM of ShotDesignerAgent in the pipeline:
    Script excerpt → ShotPlanningAgent → Shot list (intent only)
                                       ↓
                           ShotDesignerAgent → camera + lighting specs

Always returns exactly one list of Shot-shaped dicts per call. Uses mock
templates keyed on scene_type (action / dialogue / montage / default).
A real LLM integration would replace the _decompose() method.
"""
from __future__ import annotations

import uuid

from agents.base import BaseAgent

# ---------------------------------------------------------------------------
# Mock shot-list templates keyed on scene_type
# ---------------------------------------------------------------------------

_SCENE_TYPE_TEMPLATES: dict[str, list[dict]] = {
    "action": [
        {
            "shot_label": "Wide establishing",
            "intent": "Establish the geography of the action — show protagonist and threat in the same frame.",
            "duration_sec": 4.0,
        },
        {
            "shot_label": "Close-up reaction",
            "intent": "Capture the protagonist's split-second decision before the action erupts.",
            "duration_sec": 2.0,
        },
        {
            "shot_label": "OTS chase / pursuit",
            "intent": "Lock the camera over the shoulder to put the viewer inside the action.",
            "duration_sec": 6.0,
        },
        {
            "shot_label": "Insert / detail",
            "intent": "Cut to the key prop or obstacle that resolves or escalates the action.",
            "duration_sec": 1.5,
        },
        {
            "shot_label": "Wide resolution",
            "intent": "Pull back to show the aftermath and the new status-quo in the environment.",
            "duration_sec": 3.0,
        },
    ],
    "dialogue": [
        {
            "shot_label": "Two-shot establishing",
            "intent": "Show both speakers in relation to the space before cutting.",
            "duration_sec": 4.0,
        },
        {
            "shot_label": "OTS A → B",
            "intent": "Over-the-shoulder on Speaker A looking at Speaker B.",
            "duration_sec": 5.0,
        },
        {
            "shot_label": "OTS B → A",
            "intent": "Reverse: over-the-shoulder on Speaker B looking at Speaker A.",
            "duration_sec": 5.0,
        },
        {
            "shot_label": "Close-up A",
            "intent": "Tight on Speaker A's face at the emotional peak of their line.",
            "duration_sec": 3.0,
        },
        {
            "shot_label": "Close-up B reaction",
            "intent": "Speaker B's silent reaction as they absorb the key revelation.",
            "duration_sec": 2.5,
        },
    ],
    "montage": [
        {
            "shot_label": "Montage beat 1",
            "intent": "Opening image that establishes the montage theme.",
            "duration_sec": 2.0,
        },
        {
            "shot_label": "Montage beat 2",
            "intent": "Second beat — escalate or contrast with beat 1.",
            "duration_sec": 2.0,
        },
        {
            "shot_label": "Montage beat 3",
            "intent": "Third beat — midpoint of the montage arc.",
            "duration_sec": 2.0,
        },
        {
            "shot_label": "Montage beat 4",
            "intent": "Fourth beat — rising tension or accelerating pace.",
            "duration_sec": 1.5,
        },
        {
            "shot_label": "Montage closing image",
            "intent": "Final image that resolves or transforms the opening theme.",
            "duration_sec": 3.0,
        },
    ],
    "default": [
        {
            "shot_label": "Establishing wide",
            "intent": "Establish the location and the relationship between subjects.",
            "duration_sec": 4.0,
        },
        {
            "shot_label": "Coverage medium",
            "intent": "Standard medium coverage for the scene's main action or dialogue.",
            "duration_sec": 6.0,
        },
        {
            "shot_label": "Close-up detail",
            "intent": "Isolate the key narrative detail that the scene turns on.",
            "duration_sec": 2.5,
        },
    ],
}


def _scene_type_key(scene_type: str) -> str:
    st = (scene_type or "").lower()
    if any(w in st for w in ("action", "fight", "chase", "stunt", "battle")):
        return "action"
    if any(w in st for w in ("dialogue", "conversation", "interview", "argument")):
        return "dialogue"
    if any(w in st for w in ("montage", "sequence", "training")):
        return "montage"
    return "default"


def _make_shot_id(scene_id: str, index: int) -> str:
    """Generate a deterministic shot id: shot_<scene_suffix>_<index>_<short uuid>."""
    scene_suffix = scene_id.replace("scene_", "")[:8]
    short = uuid.uuid4().hex[:6]
    return f"shot_{scene_suffix}_{index:02d}_{short}"


class ShotPlanningAgent(BaseAgent):
    """Decomposes a scene description into an ordered list of Shot intents.

    This agent generates the *what* of each shot (intent, duration, label).
    ShotDesignerAgent then generates the *how* (camera + lighting specs)
    for each shot in the list.

    Input dict:
        scene_id (str)         — identifier of the parent scene (must match
                                 scene_ prefix convention, e.g. "scene_0001")
        scene_type (str)       — "action" | "dialogue" | "montage" | "default"
        scene_description (str) — prose description of what happens in the scene
        location_name (str)    — optional location name for context
        num_shots (int)        — optional override for number of shots to generate
                                 (default: use template length, max 10)

    Output dict:
        shots (list[dict])     — ordered list of shot specs, each containing:
                                   shot_id, scene_id, label, intent, duration_sec
        scene_id (str)         — echoed for traceability
        scene_type (str)       — resolved scene type key used
        coverage_warning (str | None) — advisory if num_shots was clamped
    """

    WRITABLE_FIELDS: frozenset[str] = frozenset({"Scene.shots"})
    DIAGNOSTIC_KEYS: frozenset[str] = frozenset({
        "shots",
        "scene_id",
        "scene_type",
        "proposals",
    })

    def __init__(self) -> None:
        super().__init__(name="shot_planner_agent")

    def run(self, input: dict) -> dict:  # noqa: A002
        scene_id = str(input.get("scene_id") or "scene_0001")
        scene_type = str(input.get("scene_type") or "")
        num_shots_raw = input.get("num_shots")

        type_key = _scene_type_key(scene_type)
        template = _SCENE_TYPE_TEMPLATES[type_key]

        # Honour num_shots override; clamp to [1, 10]
        coverage_warning: str | None = None
        if num_shots_raw is not None:
            try:
                requested = int(num_shots_raw)
            except (TypeError, ValueError):
                requested = len(template)
            if requested > 10:
                coverage_warning = (
                    f"num_shots={requested} exceeds max (10); clamped to 10."
                )
                requested = 10
            elif requested < 1:
                coverage_warning = (
                    "num_shots < 1 is invalid; defaulting to template length."
                )
                requested = len(template)
            shots_template = template[:requested]
        else:
            shots_template = template

        shots = []
        for i, tmpl in enumerate(shots_template):
            shot_id = _make_shot_id(scene_id, i + 1)
            shots.append(
                {
                    "shot_id": shot_id,
                    "scene_id": scene_id,
                    "label": tmpl["shot_label"],
                    "intent": tmpl["intent"],
                    "duration_sec": tmpl["duration_sec"],
                }
            )

        output = {
            "shots": shots,
            "scene_id": scene_id,
            "scene_type": type_key,
            "coverage_warning": coverage_warning,
        }
        return self._enforce_scope(output)
