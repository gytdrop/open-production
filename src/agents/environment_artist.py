"""EnvironmentArtistAgent — proposes environment specs for named locations.

Scope contract (Appendix K.4 of open-production-plan.md):
  Can write:  Production.environments (after human approval)
  Cannot write: Shot.camera, Shot.lighting, Production.characters, Scene.*

Three operations:
  "create"  — proposes 3 visual interpretations of a location from a script excerpt
  "review"  — consistency check of a generation against a ConsistencyContract
              (delegates to ConsistencyContractGate)
"""
from __future__ import annotations

from agents.base import BaseAgent
from validation.gates import ConsistencyContractGate

# ---------------------------------------------------------------------------
# Mock environment archetypes keyed on location_type
# ---------------------------------------------------------------------------

_ARCHETYPES = {
    "interior": [
        {
            "visual_description": "Warm domestic interior, lived-in textures, soft diffused window light.",
            "distinctive_features": ["warm colour temperature", "soft shadows", "personal objects visible"],
            "lighting_presets": ["warm_interior", "window_fill"],
            "time_of_day_variants": ["morning", "afternoon", "evening"],
            "consistency_notes": "Colour temperature must stay 2800K–3400K across all shots in this environment.",
        },
        {
            "visual_description": "Clinical or corporate interior, hard overhead fluorescents, minimal personal items.",
            "distinctive_features": ["cold overhead lighting", "clean lines", "neutral palette"],
            "lighting_presets": ["fluorescent_cool", "office_neutral"],
            "time_of_day_variants": ["day"],
            "consistency_notes": "Colour temperature 5000K–6000K. No warm practicals.",
        },
        {
            "visual_description": "Atmospheric interior, low-key practical lighting, strong shadows and pools of light.",
            "distinctive_features": ["deep shadows", "strong contrast", "practical light sources visible"],
            "lighting_presets": ["dramatic_interior", "low_key"],
            "time_of_day_variants": ["night", "evening"],
            "consistency_notes": "Motivated lighting only. Key source must remain consistent across cuts.",
        },
    ],
    "exterior": [
        {
            "visual_description": "Open urban exterior, mixed natural and artificial lighting, busy background.",
            "distinctive_features": ["city backdrop", "ambient crowd noise", "mixed light sources"],
            "lighting_presets": ["urban_day", "golden_hour_city"],
            "time_of_day_variants": ["dawn", "midday", "dusk", "night"],
            "consistency_notes": "Time-of-day must be locked per scene; do not mix daylight and night in same scene.",
        },
        {
            "visual_description": "Natural landscape, uncontrolled light, horizon and sky visible.",
            "distinctive_features": ["sky visible", "natural textures", "environmental sound"],
            "lighting_presets": ["natural_day", "overcast", "golden_hour"],
            "time_of_day_variants": ["dawn", "midday", "dusk"],
            "consistency_notes": "Weather condition must be consistent within a scene. Overcast vs sunny are different contracts.",
        },
        {
            "visual_description": "Industrial or transitional exterior — loading docks, alleys, parking structures.",
            "distinctive_features": ["hard architectural surfaces", "artificial practicals", "industrial textures"],
            "lighting_presets": ["industrial_sodium", "mixed_practical"],
            "time_of_day_variants": ["night", "dusk"],
            "consistency_notes": "Sodium vs LED colour temperature difference must be locked in contract.",
        },
    ],
    "abstract": [
        {
            "visual_description": "Non-representational space, stylised lighting design, symbolic colour palette.",
            "distinctive_features": ["colour as narrative signal", "minimal realism", "controlled palette"],
            "lighting_presets": ["stylised_abstract", "colour_wash"],
            "time_of_day_variants": ["timeless"],
            "consistency_notes": "Palette tokens are the consistency contract — physical realism is not enforced.",
        },
    ],
}


def _location_key(location_type: str) -> str:
    lt = location_type.lower()
    if any(w in lt for w in ("interior", "indoor", "room", "office", "home", "studio")):
        return "interior"
    if any(w in lt for w in ("exterior", "outdoor", "street", "park", "field", "landscape")):
        return "exterior"
    if any(w in lt for w in ("abstract", "stylised", "stylized", "dream", "void")):
        return "abstract"
    return "interior"  # safe default


class EnvironmentArtistAgent(BaseAgent):
    """Proposes environment visual specs and reviews environment consistency.

    Input dict (operation='create'):
        operation (str)           — "create"
        location_name (str)       — name of the location
        location_type (str)       — "interior" | "exterior" | "abstract"
        script_excerpt (str)      — lines/stage directions involving this location
        production_brief (dict)   — optional production context

    Input dict (operation='review'):
        operation (str)               — "review"
        environment_id (str)          — identifier of the environment
        generation_result (dict)      — dict with 'attributes' list
        consistency_contract (dict)   — the contract to check against

    Output (create):
        proposals (list[dict])  — 3 visual interpretations

    Output (review):
        consistent (bool)
        issues (list[str])
        severity (str)  — "pass" | "warn" | "fail"
    """

    WRITABLE_FIELDS: frozenset[str] = frozenset({"Production.environments"})
    DIAGNOSTIC_KEYS: frozenset[str] = frozenset({
        "proposals",
    })

    def __init__(self) -> None:
        super().__init__(name="environment_artist_agent")
        self._cc_gate = ConsistencyContractGate()

    def run(self, input: dict) -> dict:  # noqa: A002
        operation = str(input.get("operation") or "create")
        if operation == "review":
            return self._review(input)
        return self._create(input)

    def _create(self, input: dict) -> dict:
        location_type = str(input.get("location_type") or "interior")
        key = _location_key(location_type)
        return {"proposals": _ARCHETYPES[key]}

    def _review(self, input: dict) -> dict:
        contract = input.get("consistency_contract") or {}
        generation_result = input.get("generation_result") or {}
        environment_id = input.get("environment_id", "unknown")

        if not contract:
            return {
                "consistent": True,
                "issues": ["No consistency contract set — check skipped."],
                "severity": "pass",
                "environment_id": environment_id,
            }

        ok, reason = self._cc_gate.check(contract, generation_result)
        if ok:
            return {"consistent": True, "issues": [], "severity": "pass",
                    "environment_id": environment_id}
        return {"consistent": False, "issues": [reason],
                "severity": "fail", "environment_id": environment_id}
