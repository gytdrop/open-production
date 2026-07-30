"""CharacterDirectorAgent — creates and consistency-reviews characters.

Scope contract (Appendix K.3 of open-production-plan.md):
  Can write:  Production.characters (after human approval)
  Cannot write: Shot.camera, Shot.lighting, Production.scenes

Three operations:
  "create"  — proposes 3 visual interpretations of a character from a script excerpt
  "review"  — consistency check of a generation against a ConsistencyContract
              (delegates to ConsistencyContractGate, proving crew ↔ gate integration)
  "commit"  — packages an approved proposal into a Character-ready dict for
              service write-back.  The caller passes this dict to
              ProductionService via apply_event() to persist to Production.characters.
"""
from __future__ import annotations

import uuid

from agents.base import BaseAgent
from validation.gates import ConsistencyContractGate

# ---------------------------------------------------------------------------
# Mock visual archetypes for "create" operation
# ---------------------------------------------------------------------------

_ARCHETYPES = {
    "protagonist": [
        {
            "visual_description": "Mid-30s, sharp eyes, slightly worn clothing suggesting practical experience.",
            "distinctive_features": ["sharp cheekbones", "alert posture", "worn jacket"],
            "costume_invariants": ["worn jacket", "dark trousers"],
            "suggested_anchors": [
                "character standing in natural light, medium shot, sharp focus",
                "character close-up, determined expression",
            ],
        },
        {
            "visual_description": "Late 20s, earnest expression, well-fitted clothes reflecting hidden competence.",
            "distinctive_features": ["earnest eyes", "upright posture", "fitted clothes"],
            "costume_invariants": ["fitted coat", "minimal accessories"],
            "suggested_anchors": [
                "character in profile, natural window light",
                "character three-quarter view, confident stance",
            ],
        },
        {
            "visual_description": "Early 40s, weathered but composed, showing the weight of past decisions.",
            "distinctive_features": ["weathered face", "steady gaze", "understated style"],
            "costume_invariants": ["neutral palette", "no flashy accessories"],
            "suggested_anchors": [
                "character in low-key interior light",
                "character outdoor, overcast sky",
            ],
        },
    ],
    "antagonist": [
        {
            "visual_description": "Polished authority figure, immaculate dress concealing ruthless intent.",
            "distinctive_features": ["immaculate suit", "cold eyes", "controlled smile"],
            "costume_invariants": ["suit or formal attire", "no casual elements"],
            "suggested_anchors": [
                "character in power-position framing, low angle",
                "character lit from above, hard shadows",
            ],
        },
        {
            "visual_description": "Unpredictable presence, mismatched clothing signalling disregard for convention.",
            "distinctive_features": ["mismatched clothing", "unpredictable movement", "intense gaze"],
            "costume_invariants": ["signature unusual accessory"],
            "suggested_anchors": [
                "character in wide shot showing full unpredictable silhouette",
                "character extreme close-up on eyes",
            ],
        },
        {
            "visual_description": "Bureaucratic authority, bland presentation masking systemic danger.",
            "distinctive_features": ["forgettable face", "corporate attire", "neutral expression"],
            "costume_invariants": ["office attire", "no distinctive markings"],
            "suggested_anchors": [
                "character in fluorescent-lit office environment",
                "character at desk, face partially obscured",
            ],
        },
    ],
    "supporting": [
        {
            "visual_description": "Warm, reliable presence with lived-in appearance and expressive face.",
            "distinctive_features": ["laugh lines", "comfortable clothing", "open posture"],
            "costume_invariants": ["warm colour palette", "practical accessories"],
            "suggested_anchors": [
                "character in warm interior light, medium shot",
                "character smiling, golden hour exterior",
            ],
        },
        {
            "visual_description": "Nervous energy, quick movement, clothing slightly too formal for the situation.",
            "distinctive_features": ["restless hands", "over-formal dress", "darting eyes"],
            "costume_invariants": ["slightly too-formal outfit"],
            "suggested_anchors": [
                "character mid-action, slightly out of frame",
                "character checking surroundings, telephoto shot",
            ],
        },
        {
            "visual_description": "Quiet competence, minimal personal expression, clearly defined role.",
            "distinctive_features": ["functional clothing", "economical movement", "direct gaze"],
            "costume_invariants": ["functional, role-appropriate attire"],
            "suggested_anchors": [
                "character working, environmental context visible",
                "character in conversation, listening posture",
            ],
        },
    ],
}


class CharacterDirectorAgent(BaseAgent):
    """Creates character visual proposals, reviews consistency, and commits characters.

    Input dict (operation='create'):
        operation (str)         — "create"
        character_name (str)    — name of the character
        narrative_role (str)    — "protagonist" | "antagonist" | "supporting"
        script_excerpt (str)    — lines/actions involving this character
        production_brief (dict) — optional production context

    Input dict (operation='review'):
        operation (str)               — "review"
        character_id (str)            — identifier of the character
        generation_result (dict)      — dict with 'attributes' list
        consistency_contract (dict)   — the contract to check against

    Input dict (operation='commit'):
        operation (str)          — "commit"
        character_name (str)     — canonical name
        narrative_role (str)     — role string stored on Character.role
        approved_proposal (dict) — one of the dicts returned by 'create'
        character_id (str)       — optional; generated as 'char_<hex>' if absent

    Output (create):
        proposals (list[dict])  — 3 visual interpretations

    Output (review):
        consistent (bool)
        issues (list[str])
        severity (str)  — "pass" | "warn" | "fail"

    Output (commit):
        character (dict)        — Character-schema-ready dict for service write-back
        character_id (str)      — the id assigned to the committed character
        rationale (str)
    """

    WRITABLE_FIELDS: frozenset[str] = frozenset({"Production.characters"})
    DIAGNOSTIC_KEYS: frozenset[str] = frozenset({
        "proposals",
        "character",
    })

    def __init__(self) -> None:
        super().__init__(name="character_director_agent")
        self._cc_gate = ConsistencyContractGate()

    def run(self, input: dict) -> dict:  # noqa: A002
        operation = str(input.get("operation") or "create")
        if operation == "review":
            return self._review(input)
        if operation == "commit":
            return self._commit(input)
        return self._create(input)

    def _create(self, input: dict) -> dict:
        role = str(input.get("narrative_role") or "supporting").lower()
        key = role if role in _ARCHETYPES else "supporting"
        return {"proposals": _ARCHETYPES[key]}

    def _review(self, input: dict) -> dict:
        contract = input.get("consistency_contract") or {}
        generation_result = input.get("generation_result") or {}
        character_id = input.get("character_id", "unknown")

        if not contract:
            return {
                "consistent": True,
                "issues": ["No consistency contract set — check skipped."],
                "severity": "pass",
                "character_id": character_id,
            }

        ok, reason = self._cc_gate.check(contract, generation_result)
        if ok:
            return {"consistent": True, "issues": [], "severity": "pass",
                    "character_id": character_id}
        return {"consistent": False, "issues": [reason],
                "severity": "fail", "character_id": character_id}

    def _commit(self, input: dict) -> dict:
        """Package an approved proposal into a Character-ready dict for write-back.

        The caller is responsible for passing this dict to the service layer
        (e.g. via apply_event with action_type='decision') to persist it to
        Production.characters.  The agent itself never mutates production state.
        """
        name = str(input.get("character_name") or "Unknown").strip()
        role = str(input.get("narrative_role") or "supporting").strip()
        proposal = dict(input.get("approved_proposal") or {})
        char_id = str(input.get("character_id") or "").strip()
        if not char_id or not char_id.startswith("char_"):
            char_id = f"char_{uuid.uuid4().hex[:8]}"

        # Build a minimal ConsistencyContract from the proposal's anchors, if present.
        required_attrs: list[str] = list(proposal.get("distinctive_features") or [])
        prohibited_attrs: list[str] = []

        character = {
            "id": char_id,
            "name": name,
            "role": role,
            "voice_id": None,
            "visual_anchors": [],
            "consistency_contract": {
                "subject_id": char_id,
                "visual_anchors": [],
                "required_attributes": required_attrs,
                "prohibited_attributes": prohibited_attrs,
                "variance_tolerance": 0.15,
                "reviewer_checklist": list(proposal.get("costume_invariants") or []),
            },
        }
        return self._enforce_scope({
            "character": character,
            "character_id": char_id,
            "rationale": (
                f"Character '{name}' (role={role}) packaged for service write-back. "
                f"id={char_id}. Apply via ProductionService to persist to "
                "Production.characters."
            ),
        })
