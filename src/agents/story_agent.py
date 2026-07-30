"""StoryAgent — structures narrative and enforces the "structure locked" gate.

Pipeline position: Stage 6 (Story), after creative direction and before scripting.

Plan specification gate rule: the story stage is blocked until a complete
three-act structure has been proposed and approved.  Once the producer calls
operation="lock", the structure_locked flag is set in the output and downstream
agents (ScriptAgent, CharacterDirectorAgent, etc.) may proceed.

Three operations:
  "propose"  — default; generates 3 narrative structure options for the topic.
  "lock"     — validates a chosen structure and returns structure_locked=True.
  "validate" — lightweight check returning {valid, issues, structure_locked}.

Scope contract:
  WRITABLE_FIELDS is frozenset() — StoryAgent proposes structure but never
  writes production state fields directly.  The chosen structure is written
  to Production.metadata["story_structure"] only after human approval through
  the service layer (same pattern as ResearchAgent).
"""
from __future__ import annotations

from agents.base import BaseAgent

# ---------------------------------------------------------------------------
# Structure templates keyed on narrative register
# ---------------------------------------------------------------------------

_STRUCTURES = {
    "dramatic": [
        {
            "structure_name": "Classical Three-Act",
            "acts": [
                {
                    "act": 1,
                    "label": "Setup",
                    "description": "Establish world, protagonist, and the inciting incident that disrupts the status quo.",
                    "beats": ["ordinary world", "call to action", "crossing the threshold"],
                },
                {
                    "act": 2,
                    "label": "Confrontation",
                    "description": "Protagonist pursues goal, obstacles escalate, midpoint reversal raises stakes.",
                    "beats": ["rising action", "midpoint", "dark night of the soul"],
                },
                {
                    "act": 3,
                    "label": "Resolution",
                    "description": "Climax, consequence, and a changed world — protagonist transformed.",
                    "beats": ["climax", "falling action", "denouement"],
                },
            ],
            "tone": "dramatic",
            "rationale": (
                "The classical three-act shape is the most legible structure for "
                "audiences. It anchors the production in familiar story grammar "
                "while leaving full creative latitude inside each act."
            ),
        },
        {
            "structure_name": "Non-Linear Parallel",
            "acts": [
                {
                    "act": 1,
                    "label": "Present Thread",
                    "description": "Open in media res at a moment of crisis; establish the emotional stakes immediately.",
                    "beats": ["in media res opening", "flash-forward hook"],
                },
                {
                    "act": 2,
                    "label": "Past Thread",
                    "description": "Intercut the backstory that explains how the crisis was reached.",
                    "beats": ["origin reveal", "parallel escalation"],
                },
                {
                    "act": 3,
                    "label": "Convergence",
                    "description": "Past and present collide — the audience connects the full picture.",
                    "beats": ["timeline merge", "revelation", "resolution"],
                },
            ],
            "tone": "complex",
            "rationale": (
                "Non-linear structure creates intrinsic audience engagement through "
                "mystery and dramatic irony. Best when the 'how' is more compelling "
                "than the 'what'."
            ),
        },
        {
            "structure_name": "Escalating Vignettes",
            "acts": [
                {
                    "act": 1,
                    "label": "Portrait A",
                    "description": "First self-contained vignette introducing the central theme through one lens.",
                    "beats": ["introduce subject", "tension seed"],
                },
                {
                    "act": 2,
                    "label": "Portrait B",
                    "description": "Second vignette reframes the theme through a contrasting perspective.",
                    "beats": ["contrast introduced", "mirror moment"],
                },
                {
                    "act": 3,
                    "label": "Synthesis",
                    "description": "Vignettes collide — the gap between perspectives becomes the point.",
                    "beats": ["convergence", "thematic statement", "open question"],
                },
            ],
            "tone": "literary",
            "rationale": (
                "Vignette structure suits documentary and essay-form productions. "
                "It lets the audience hold two contradictory truths simultaneously, "
                "producing more durable emotional impact."
            ),
        },
    ],
    "informational": [
        {
            "structure_name": "Problem–Solution Arc",
            "acts": [
                {
                    "act": 1,
                    "label": "Problem",
                    "description": "Establish the problem with concrete evidence and human stakes.",
                    "beats": ["hook statistic or image", "problem definition", "human cost"],
                },
                {
                    "act": 2,
                    "label": "Context",
                    "description": "Why the problem persists — systemic and historical framing.",
                    "beats": ["root causes", "failed attempts", "scale"],
                },
                {
                    "act": 3,
                    "label": "Solution",
                    "description": "Viable path forward — evidence-based with honest caveats.",
                    "beats": ["solution options", "evidence", "call to action"],
                },
            ],
            "tone": "informational",
            "rationale": (
                "Problem–solution is the native shape of impact-oriented informational "
                "content. It creates urgency and equips the audience with agency."
            ),
        },
        {
            "structure_name": "Journey Arc",
            "acts": [
                {
                    "act": 1,
                    "label": "Before",
                    "description": "The state of the world or subject before the central event or discovery.",
                    "beats": ["baseline", "expectation setting"],
                },
                {
                    "act": 2,
                    "label": "Journey",
                    "description": "The event, experiment, or investigation unfolds in real time.",
                    "beats": ["process", "obstacles", "turning point"],
                },
                {
                    "act": 3,
                    "label": "After",
                    "description": "Consequence, learning, and implications for the broader world.",
                    "beats": ["outcome", "implications", "open horizon"],
                },
            ],
            "tone": "experiential",
            "rationale": (
                "Journey structure is ideal for behind-the-scenes, investigative, "
                "and process-driven content. Audiences experience discovery alongside "
                "the subject."
            ),
        },
        {
            "structure_name": "Comparative Mosaic",
            "acts": [
                {
                    "act": 1,
                    "label": "Case A",
                    "description": "First case study presented fully — context, event, outcome.",
                    "beats": ["introduce case", "context", "outcome A"],
                },
                {
                    "act": 2,
                    "label": "Case B",
                    "description": "Second case study — intentionally chosen to contrast or mirror Case A.",
                    "beats": ["introduce case", "contrast or parallel", "outcome B"],
                },
                {
                    "act": 3,
                    "label": "Analysis",
                    "description": "Synthesise the two cases into a testable insight the audience can apply.",
                    "beats": ["comparison", "insight", "application"],
                },
            ],
            "tone": "analytical",
            "rationale": (
                "Comparative mosaic is well-suited to explainer and educational content. "
                "Juxtaposition is one of the most efficient ways to produce new "
                "understanding in an audience."
            ),
        },
    ],
}


def _register_key(topic: str) -> str:
    t = topic.lower()
    informational_signals = (
        "how", "why", "what", "explain", "documentary", "investigation",
        "study", "research", "science", "history", "report", "analysis",
    )
    if any(w in t for w in informational_signals):
        return "informational"
    return "dramatic"


class StoryAgent(BaseAgent):
    """Proposes narrative structures and enforces the structure-locked gate.

    "propose" operation (default):
        Input:  topic (str), genre (str, optional), num_acts (int, optional)
        Output: proposals (list[dict] — 3 structure options with acts)

    "lock" operation:
        Input:  operation="lock", chosen_structure (dict) — must have 'structure_name'
        Output: structure_locked (bool), structure_name (str), rationale (str)

    "validate" operation:
        Input:  operation="validate", story_structure (dict or None)
        Output: valid (bool), issues (list[str]), structure_locked (bool)
    """

    WRITABLE_FIELDS: frozenset[str] = frozenset()  # proposals only; writes go through service
    DIAGNOSTIC_KEYS: frozenset[str] = frozenset({
        "proposals",
        "topic",
        "structure_count",
        "structure_locked",
        "structure_name",
        "needs_creative_brief",
        "story_outline",
        "locked",
        "rationale",
        "issues",
        "valid",
        "needs_story_outline",
    })

    def __init__(self) -> None:
        super().__init__(name="story_agent")

    def run(self, input: dict) -> dict:  # noqa: A002
        operation = str(input.get("operation") or "propose")
        if operation == "lock":
            return self._lock(input)
        if operation == "validate":
            return self._validate(input)
        return self._propose(input)

    # ------------------------------------------------------------------

    def _propose(self, input: dict) -> dict:
        topic = str(input.get("topic") or "")
        key = _register_key(topic)
        return self._enforce_scope({
            "proposals": list(_STRUCTURES[key]),
            "topic": topic,
            "structure_count": len(_STRUCTURES[key]),
        })

    def _lock(self, input: dict) -> dict:
        chosen = input.get("chosen_structure") or {}
        name = str(chosen.get("structure_name") or "").strip()
        if not name:
            return self._enforce_scope({
                "structure_locked": False,
                "structure_name": "",
                "rationale": (
                    "Structure lock REJECTED: chosen_structure has no "
                    "'structure_name'. Select a named structure before locking."
                ),
            })
        acts = chosen.get("acts") or []
        if not acts:
            return self._enforce_scope({
                "structure_locked": False,
                "structure_name": name,
                "rationale": (
                    f"Structure lock REJECTED: '{name}' has no acts defined. "
                    "A valid structure requires at least one act."
                ),
            })
        return self._enforce_scope({
            "structure_locked": True,
            "structure_name": name,
            "rationale": (
                f"Structure locked and approved: '{name}' with {len(acts)} act(s). "
                "ScriptAgent and downstream agents may now proceed."
            ),
        })

    def _validate(self, input: dict) -> dict:
        story_structure = input.get("story_structure") or {}
        issues: list[str] = []
        if not story_structure:
            issues.append(
                "No story_structure present — Stage 6 gate cannot pass. "
                "Run StoryAgent with operation='propose', select a structure, "
                "then lock it with operation='lock'."
            )
            return {"valid": False, "issues": issues, "structure_locked": False}
        name = str(story_structure.get("structure_name") or "").strip()
        if not name:
            issues.append("story_structure has no 'structure_name'.")
        acts = story_structure.get("acts") or []
        if not acts:
            issues.append("story_structure has no acts — a structure must have at least one act.")
        locked = bool(story_structure.get("structure_locked", False))
        if not locked:
            issues.append(
                "story_structure.structure_locked is False — "
                "call StoryAgent(operation='lock') to advance past Stage 6."
            )
        return {"valid": len(issues) == 0, "issues": issues, "structure_locked": locked}
