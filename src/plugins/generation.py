"""GenerationPlugin protocol and built-in mock implementations.

Per open-production-plan.md \u00a717, a GenerationPlugin is a backend for
producing one shot's output. The full spec requires:

  - name + version
  - capabilities (advertised)
  - generate(shot, production) -> GenerationResult
  - estimate_cost(shot) -> CostEstimate
  - health_check() -> PluginHealth

The pre-existing `MockGenerationPlugin` (originally in
`src/agents/generation.py`) satisfies the original two-method contract.
This module upgrades it to the full spec with no breaking changes.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from src.plugins.base import PluginCapability, PluginHealth


@dataclass(frozen=True)
class CostEstimate:
    """Returned by GenerationPlugin.estimate_cost()."""

    backend_name: str
    estimated_usd: float
    estimated_latency_ms: int
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "backend_name": self.backend_name,
            "estimated_usd": self.estimated_usd,
            "estimated_latency_ms": self.estimated_latency_ms,
            "notes": self.notes,
        }


@runtime_checkable
class GenerationPlugin(Protocol):
    """Contract every generation backend must satisfy.

    A class is a valid GenerationPlugin if it has `generate`,
    `estimate_cost`, and `health_check` methods plus the
    `name`, `capabilities`, `backend_name`, and `backend_version`
    attributes.
    """

    name: str
    capabilities: frozenset[PluginCapability]
    backend_name: str
    backend_version: str

    def generate(self, shot: dict, production: dict) -> dict:
        """Run the generation backend for one shot.

        Returns a GenerationResult-shaped dict:
            id, produced_at, produced_by, backend, backend_version,
            prompt_hash, output_uri, output_sha256,
            reviewer_verdict, cost_estimate_usd, latency_ms,
            attributes (list[str]),  quality_score (float), metadata (dict)
        """
        ...

    def estimate_cost(self, shot: dict) -> CostEstimate:
        """Estimate USD cost and latency for one shot."""
        ...

    def health_check(self) -> PluginHealth:
        """Return current plugin health. Unhealthy plugins are disabled."""
        ...


# ---------------------------------------------------------------------------
# Built-in mock implementation (the default backend)
# ---------------------------------------------------------------------------


class MockGenerationPlugin:
    """Deterministic mock generation backend.

    Produces a fixed set of plausible attributes keyed on shot intent mood.
    No external calls, no side-effects.  A real integration would replace
    this class with a REST/gRPC client to Runway, Veo, or a local model.
    """

    name: str = "mock-generation-v1"
    backend_name: str = "mock-generation-v1"
    backend_version: str = "1.0.0"
    capabilities: frozenset[PluginCapability] = frozenset(
        {PluginCapability.VIDEO, PluginCapability.IMAGE}
    )

    # Attribute sets keyed on coarse shot intent category
    _MOCK_ATTRIBUTES: dict[str, list[str]] = {
        "tense": [
            "high_angle", "cold_lighting", "hard_shadows", "medium_framing",
            "desaturated_palette", "tight_composition",
        ],
        "warm": [
            "low_angle", "warm_lighting", "soft_shadows", "wide_framing",
            "saturated_palette", "open_composition",
        ],
        "default": [
            "neutral_angle", "neutral_lighting", "soft_shadows", "medium_framing",
            "balanced_palette", "standard_composition",
        ],
    }

    def _intent_key(self, intent: str) -> str:
        lower = (intent or "").lower()
        if any(w in lower for w in ("dark", "cold", "tense", "fight", "chase")):
            return "tense"
        if any(w in lower for w in ("warm", "joy", "love", "celebration", "reunion", "hope")):
            return "warm"
        return "default"

    def generate(self, shot: dict, production: dict) -> dict:  # noqa: ARG002
        intent = str(shot.get("intent") or "")
        key = self._intent_key(intent)
        attributes = list(self._MOCK_ATTRIBUTES[key])

        # Synthesise a prompt string from shot fields for a stable hash
        prompt_parts = [
            intent,
            str(shot.get("shot_id") or ""),
            str((shot.get("camera") or {}).get("framing") or ""),
            str((shot.get("lighting") or {}).get("preset_id") or ""),
        ]
        prompt_str = "|".join(prompt_parts)
        prompt_hash = hashlib.sha256(prompt_str.encode()).hexdigest()

        gen_id = "gen_" + uuid.uuid4().hex[:12]

        # Mock latency and cost
        latency_ms = 1200
        cost_usd = 0.012

        # Mock output URI (content-addressed pattern)
        output_sha = hashlib.sha256((gen_id + prompt_hash).encode()).hexdigest()
        output_uri = f"mock://outputs/{gen_id}/{output_sha[:16]}.mp4"

        # Color temp from lighting spec, for ReviewerAgent continuity check
        color_temp_k = (shot.get("lighting") or {}).get("color_temp_k") or 5600

        return {
            "id": gen_id,
            "produced_at": _utc_now(),
            "produced_by": self.backend_name,
            "backend": self.backend_name,
            "backend_version": self.backend_version,
            "prompt_hash": prompt_hash,
            "output_uri": output_uri,
            "output_sha256": output_sha,
            "reviewer_verdict": {},     # filled in after ReviewerAgent runs
            "cost_estimate_usd": cost_usd,
            "latency_ms": latency_ms,
            "attributes": attributes,
            "quality_score": 0.85,
            "metadata": {
                "framing": (shot.get("camera") or {}).get("framing") or "medium",
                "mood": key,
                "color_temp_k": color_temp_k,
            },
        }

    def estimate_cost(self, shot: dict) -> CostEstimate:
        intent = str(shot.get("intent") or "")
        key = self._intent_key(intent)
        # Tense shots are slightly more expensive in the mock heuristic.
        multiplier = 1.0 if key == "default" else 1.5
        return CostEstimate(
            backend_name=self.backend_name,
            estimated_usd=round(0.012 * multiplier, 4),
            estimated_latency_ms=int(1200 * multiplier),
            notes=f"mock estimate for {key} intent",
        )

    def health_check(self) -> PluginHealth:
        from datetime import datetime, timezone

        return PluginHealth(
            healthy=True,
            plugin_name=self.name,
            checked_at=datetime.now(timezone.utc).isoformat(),
            metrics={"backend_version": self.backend_version, "mode": "mock"},
        )


def _utc_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
