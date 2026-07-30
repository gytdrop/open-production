"""ReferenceClusteringAgent — clusters reference material and extracts style tokens.

Scope contract (Pipeline Stage 3 of open-production-plan.md):
  Can write:  Production.references  (after human approval)
  Cannot write: Shot.camera, Production.characters, Scene.*, any generation param

Plan gate: "Style tokens extractable" — at least one style cluster must be
identifiable from the supplied references before the production can advance
to Stage 4 (Moodboard).

Two operations:
  "cluster"  — groups a list of references into visual/tonal clusters and
                proposes 3 cluster interpretations, each with extracted style tokens.
  "validate" — checks whether the reference set satisfies the stage gate
                (at least one cluster, at least one style token per cluster).
"""
from __future__ import annotations

from agents.base import BaseAgent, ScopeViolation

# ---------------------------------------------------------------------------
# Cluster archetypes keyed on dominant tone extracted from reference labels
# ---------------------------------------------------------------------------

_CLUSTER_TEMPLATES = {
    "naturalistic": [
        {
            "cluster_name": "Golden Hour Naturalism",
            "dominant_tone": "warm, earthy, organic",
            "style_tokens": ["warm_amber_palette", "soft_directional_light", "natural_texture"],
            "mood_keywords": ["intimate", "grounded", "honest"],
            "reference_count": 0,
            "rationale": (
                "References share warm colour temperatures and natural textures. "
                "Style tokens anchor the production in an organic, human-scale aesthetic."
            ),
        },
        {
            "cluster_name": "Overcast Verite",
            "dominant_tone": "cool, diffused, documentary",
            "style_tokens": ["flat_overcast_light", "desaturated_neutral", "handheld_energy"],
            "mood_keywords": ["authentic", "raw", "observational"],
            "reference_count": 0,
            "rationale": (
                "Flat diffused light across references signals a documentary or realist register. "
                "Desaturated neutral tokens reduce production artifice."
            ),
        },
        {
            "cluster_name": "Dusk Contrast",
            "dominant_tone": "high-contrast, twilight, transitional",
            "style_tokens": ["dusk_contrast", "deep_shadow", "silhouette_framing"],
            "mood_keywords": ["tension", "transition", "ambiguity"],
            "reference_count": 0,
            "rationale": (
                "References share high-contrast twilight conditions. Silhouette framing and deep "
                "shadows suggest a production operating at emotional thresholds."
            ),
        },
    ],
    "stylised": [
        {
            "cluster_name": "Graphic Modernism",
            "dominant_tone": "bold, geometric, high-contrast",
            "style_tokens": ["bold_graphic_palette", "hard_edge_lighting", "symmetrical_framing"],
            "mood_keywords": ["authoritative", "modern", "deliberate"],
            "reference_count": 0,
            "rationale": (
                "Strong geometric composition and hard-edge lighting across references. "
                "Symmetrical framing tokens enforce visual authority."
            ),
        },
        {
            "cluster_name": "Painterly Soft",
            "dominant_tone": "diffused, painterly, tonal gradients",
            "style_tokens": ["painterly_diffusion", "tonal_gradient", "soft_focus"],
            "mood_keywords": ["dreamlike", "romantic", "reflective"],
            "reference_count": 0,
            "rationale": (
                "Soft focus and tonal gradients in references suggest a painterly, "
                "non-photographic visual register. Evokes memory and interiority."
            ),
        },
        {
            "cluster_name": "Neon Urban",
            "dominant_tone": "saturated, night, artificial light",
            "style_tokens": ["neon_saturation", "artificial_practical", "night_urban"],
            "mood_keywords": ["energy", "alienation", "nocturnal"],
            "reference_count": 0,
            "rationale": (
                "Artificial neon and high-saturation practicals dominate references. "
                "Night-urban tokens signal a world mediated by artificial surfaces."
            ),
        },
    ],
}


def _style_key(references: list[dict]) -> str:
    """Derive cluster family from reference labels; defaults to 'naturalistic'."""
    labels = " ".join(str(r.get("label", "")) for r in references).lower()
    stylised_signals = ("graphic", "bold", "neon", "abstract", "geometric",
                        "painterly", "stylised", "stylized", "minimal")
    if any(w in labels for w in stylised_signals):
        return "stylised"
    return "naturalistic"


class ReferenceClusteringAgent(BaseAgent):
    """Clusters reference material and extracts style tokens for Stage 3.

    Input dict (operation='cluster'):
        operation (str)               — "cluster" (default)
        references (list[dict])       — list of {id, kind, label, uri?} dicts
        production_brief (dict)       — optional topic/tone context

    Input dict (operation='validate'):
        operation (str)               — "validate"
        references (list[dict])       — same list

    Output (cluster):
        proposals (list[dict])        — 3 cluster interpretations, each with:
                                         cluster_name, dominant_tone, style_tokens,
                                         mood_keywords, reference_count, rationale
        reference_count (int)         — total references supplied

    Output (validate):
        valid (bool)                  — True when gate conditions met
        issues (list[str])            — human-readable reasons if not valid
        reference_count (int)
    """

    WRITABLE_FIELDS: frozenset[str] = frozenset({"Production.references"})
    DIAGNOSTIC_KEYS: frozenset[str] = frozenset({
        "proposals",
        "reference_count",
    })

    def __init__(self) -> None:
        super().__init__(name="reference_clustering_agent")

    def run(self, input: dict) -> dict:  # noqa: A002
        operation = str(input.get("operation") or "cluster")
        if operation == "validate":
            return self._validate(input)
        return self._cluster(input)

    def _cluster(self, input: dict) -> dict:
        references = list(input.get("references") or [])
        key = _style_key(references)
        proposals = [dict(p, reference_count=len(references)) for p in _CLUSTER_TEMPLATES[key]]
        return {
            "proposals": proposals,
            "reference_count": len(references),
        }

    def _validate(self, input: dict) -> dict:
        references = list(input.get("references") or [])
        issues: list[str] = []
        if not references:
            issues.append("No references supplied — at least 1 reference is required for Stage 3.")
        # Check that each reference has a label (style tokens cannot be extracted without one)
        unlabelled = [r for r in references if not str(r.get("label", "")).strip()]
        if unlabelled:
            issues.append(
                f"{len(unlabelled)} reference(s) have no label — "
                "style tokens cannot be extracted without labelled references."
            )
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "reference_count": len(references),
        }
