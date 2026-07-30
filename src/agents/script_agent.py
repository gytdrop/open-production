"""ScriptAgent — writes script scenes and enforces the "script locked" gate.

Pipeline position: Stage 7 (Script), after story structure is locked
and before character, location, and shot planning stages.

Three operations:
  "draft"    — default; generates 3 scene templates for the topic/genre.
  "lock"     — validates a complete script (all scenes present) and returns
               script_locked=True when the check passes.
  "validate" — lightweight check returning {valid, issues, script_locked}.

Scope contract:
  WRITABLE_FIELDS is frozenset() — ScriptAgent proposes script content but
  never writes production state fields directly.  Approved script content is
  written to Production.metadata["script"] only after human approval through
  the service layer (same pattern as ResearchAgent and StoryAgent).
"""
from __future__ import annotations

from agents.base import BaseAgent

# ---------------------------------------------------------------------------
# Default scene templates by genre register
# ---------------------------------------------------------------------------

_SCENE_TEMPLATES: dict[str, list[dict]] = {
    "dramatic": [
        {
            "scene_type": "Establishing Scene",
            "description": "Open on the world before the disruption — set tone and character.",
            "sample_lines": [
                {"character": "PROTAGONIST", "line": "This used to be enough.", "direction": "Low, to themselves"},
                {"character": "ACTION", "line": "(A quiet moment — ordinary routine. Something is off but unnamed.)"},
            ],
            "duration_hint_sec": 45,
            "rationale": "An establishing scene anchors the audience in the protagonist's world, making the coming disruption meaningful.",
        },
        {
            "scene_type": "Inciting Incident",
            "description": "The event that disrupts the ordinary world and demands response.",
            "sample_lines": [
                {"character": "SECONDARY", "line": "It's happening. Now.", "direction": "Urgent, barely controlled"},
                {"character": "PROTAGONIST", "line": "Not yet. Not like this.", "direction": "Denial giving way to action"},
            ],
            "duration_hint_sec": 60,
            "rationale": "The inciting incident creates the central dramatic question the audience will spend the rest of the production resolving.",
        },
        {
            "scene_type": "Midpoint Reversal",
            "description": "Stakes double — the protagonist's approach is revealed as insufficient.",
            "sample_lines": [
                {"character": "ANTAGONIST", "line": "You were never playing the right game.", "direction": "Cold, assured"},
                {"character": "PROTAGONIST", "line": "What have I missed?", "direction": "Internal — realisation forming"},
            ],
            "duration_hint_sec": 50,
            "rationale": "A midpoint reversal keeps the second act from sagging. The audience's expectations are reset.",
        },
    ],
    "informational": [
        {
            "scene_type": "Opening Statement",
            "description": "Present the central question or claim that will be examined.",
            "sample_lines": [
                {"character": "NARRATOR", "line": "Every year, this happens. Nobody notices. We decided to look closer.", "direction": "Direct, measured"},
            ],
            "duration_hint_sec": 30,
            "rationale": "A clear opening statement sets an epistemic contract with the audience — this is what we will prove or disprove.",
        },
        {
            "scene_type": "Evidence Scene",
            "description": "Data, interview, or demonstration that supports or complicates the claim.",
            "sample_lines": [
                {"character": "EXPERT", "line": "The numbers have been consistent for a decade. And yet the policy hasn't changed.", "direction": "Matter-of-fact — the absurdity speaks for itself"},
            ],
            "duration_hint_sec": 90,
            "rationale": "Evidence scenes must be concrete. Abstract claims lose audiences. Show, don't summarise.",
        },
        {
            "scene_type": "Counter-Voice",
            "description": "A credible challenge to the main argument — included to strengthen, not neutralise, the production.",
            "sample_lines": [
                {"character": "DISSENTING EXPERT", "line": "The model works — under ideal conditions. Which don't exist.", "direction": "Not hostile — cautionary"},
            ],
            "duration_hint_sec": 60,
            "rationale": "Including a counter-voice signals intellectual honesty and makes the final synthesis more credible.",
        },
    ],
}


def _genre_key(genre: str, topic: str) -> str:
    t = (genre + " " + topic).lower()
    informational_signals = (
        "documentary", "explainer", "report", "investigation", "educational",
        "informational", "how", "why", "analysis",
    )
    if any(w in t for w in informational_signals):
        return "informational"
    return "dramatic"


class ScriptAgent(BaseAgent):
    """Drafts scene scripts and enforces the script-locked gate.

    "draft" operation (default):
        Input:  topic (str), genre (str, optional), act_label (str, optional),
                structure_locked (bool, optional) — if False, a warning is attached
        Output: proposals (list[dict] — 3 scene templates), script_locked=False,
                genre (str), act_label (str), structure_warning (if unlocked)

    "lock" operation:
        Input:  operation="lock", script (dict) — must have 'scenes' list (non-empty)
        Output: script_locked (bool), scene_count (int), rationale (str)

    "validate" operation:
        Input:  operation="validate", script (dict or None)
        Output: valid (bool), issues (list[str]), script_locked (bool)
    """

    WRITABLE_FIELDS: frozenset[str] = frozenset()  # proposals only; writes go through service
    DIAGNOSTIC_KEYS: frozenset[str] = frozenset({
        "proposals",
        "topic",
        "genre",
        "act_label",
        "script_locked",
        "scene_count",
        "structure_warning",
        "needs_story_outline",
        "script",
        "rationale",
        "issues",
        "valid",
    })

    def __init__(self) -> None:
        super().__init__(name="script_agent")

    def run(self, input: dict) -> dict:  # noqa: A002
        operation = str(input.get("operation") or "draft")
        if operation == "lock":
            return self._lock(input)
        if operation == "validate":
            return self._validate(input)
        return self._draft(input)

    # ------------------------------------------------------------------

    def _draft(self, input: dict) -> dict:
        topic = str(input.get("topic") or "")
        genre = str(input.get("genre") or "")
        act_label = str(input.get("act_label") or "")
        structure_locked = bool(input.get("structure_locked", False))

        key = _genre_key(genre, topic)
        templates = list(_SCENE_TEMPLATES[key])

        out: dict = {
            "proposals": templates,
            "topic": topic,
            "genre": genre or key,
            "act_label": act_label,
            "script_locked": False,
        }
        if not structure_locked:
            out["structure_warning"] = (
                "Story structure not locked — run StoryAgent(operation='lock') "
                "before finalising the script. Draft may be revised after structure lock."
            )
        return self._enforce_scope(out)

    def _lock(self, input: dict) -> dict:
        script = input.get("script") or {}
        scenes = script.get("scenes") or []
        if not scenes:
            return self._enforce_scope({
                "script_locked": False,
                "scene_count": 0,
                "rationale": (
                    "Script lock REJECTED: script has no scenes. "
                    "Provide a 'scenes' list with at least one scene before locking."
                ),
            })
        # Check that every scene has at least a type or description
        incomplete = [
            i for i, s in enumerate(scenes)
            if not (s.get("scene_type") or s.get("description"))
        ]
        if incomplete:
            return self._enforce_scope({
                "script_locked": False,
                "scene_count": len(scenes),
                "rationale": (
                    f"Script lock REJECTED: {len(incomplete)} scene(s) have neither "
                    "'scene_type' nor 'description'. Every scene must be labelled "
                    "before locking."
                ),
            })
        return self._enforce_scope({
            "script_locked": True,
            "scene_count": len(scenes),
            "rationale": (
                f"Script locked and approved: {len(scenes)} scene(s). "
                "CharacterDirectorAgent, ShotDesignerAgent, and "
                "StoryboardArtistAgent may now proceed."
            ),
        })

    def _validate(self, input: dict) -> dict:
        script = input.get("script") or {}
        issues: list[str] = []
        if not script:
            issues.append(
                "No script present — Stage 7 gate cannot pass. "
                "Run ScriptAgent with operation='draft', select scenes, "
                "then lock with operation='lock'."
            )
            return {"valid": False, "issues": issues, "script_locked": False}
        scenes = script.get("scenes") or []
        if not scenes:
            issues.append("script has no 'scenes' list — at least one scene is required.")
        locked = bool(script.get("script_locked", False))
        if not locked:
            issues.append(
                "script.script_locked is False — "
                "call ScriptAgent(operation='lock') to advance past Stage 7."
            )
        return {"valid": len(issues) == 0, "issues": issues, "script_locked": locked}
