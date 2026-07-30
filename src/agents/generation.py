"""GenerationAgent — executes a mock generation backend and gates the result.

Stage 16 of the 26-stage production pipeline.

Scope contract (adjacent to ShotDesignerAgent, upstream of ReviewerAgent):
  Can write:  Shot.generation, Shot.status, Shot.version_history
  Cannot write: Shot.camera, Shot.lighting, Production.characters, Scene.*

Design
------
The GenerationAgent wraps a GenerationPlugin (a protocol/interface), calls
``plugin.generate()``, attaches the result to the shot, then delegates
quality gating to ReviewerAgent.

A GenerationPlugin must satisfy::

    class MyPlugin:
        backend_name: str           # e.g. "video-synthesis-v1"
        backend_version: str        # semver string, e.g. "1.0.0"

        def generate(self, shot: dict, production: dict) -> dict:
            # Returns a GenerationResult-shaped dict:
            #   id, produced_at, produced_by, backend, backend_version,
            #   prompt_hash, output_uri, output_sha256,
            #   reviewer_verdict, cost_estimate_usd, latency_ms,
            #   attributes (list[str]),  quality_score (float), metadata (dict)

The ``MockGenerationPlugin`` bundled here is the default.  Swap it for a real
backend (Runway, Veo, local diffusion) by passing ``plugin=`` to the
constructor or to ``run()`` via the ``plugin`` key.
"""
from __future__ import annotations

import hashlib
import time
import uuid
from typing import Protocol, runtime_checkable

from agents.base import BaseAgent
from agents.reviewer import ReviewerAgent


# ---------------------------------------------------------------------------
# GenerationPlugin protocol — the swap-in interface for real backends
# ---------------------------------------------------------------------------

@runtime_checkable
class GenerationPlugin(Protocol):
    """Minimal contract every generation backend must satisfy.

    A class is a valid GenerationPlugin if it has a ``generate`` method with
    this signature.  No base class required — duck typing enforced via
    ``isinstance(plugin, GenerationPlugin)`` at runtime.
    """

    backend_name: str
    backend_version: str

    def generate(self, shot: dict, production: dict) -> dict:
        """Run the generation backend for one shot.

        Args:
            shot:       Shot-shaped dict (intent, camera, lighting, characters, …)
            production: Full production document dict (for prompt construction)

        Returns:
            A dict shaped like GenerationResult plus extra diagnostic keys:
                id (str)                    — gen_<12hex>
                produced_at (str)           — UTC ISO
                produced_by (str)           — agent / backend name
                backend (str)               — backend identifier
                backend_version (str)       — semver
                prompt_hash (str | None)    — SHA-256 of synthesised prompt
                output_uri (str | None)     — S3 / file URI of the output
                output_sha256 (str | None)  — integrity hash
                reviewer_verdict (dict)     — populated by ReviewerAgent later
                cost_estimate_usd (float)   — estimated cost
                latency_ms (int)            — wall-clock ms
                attributes (list[str])      — visual attributes for ReviewerAgent
                quality_score (float)       — 0.0–1.0 quality signal
                metadata (dict)             — framing, mood, color_temp_k, etc.
        """
        ...


# ---------------------------------------------------------------------------
# MockGenerationPlugin — deterministic mock; replace with real backend
# ---------------------------------------------------------------------------

class MockGenerationPlugin:
    """Deterministic mock generation backend.

    Produces a fixed set of plausible attributes keyed on shot intent mood.
    No external calls, no side-effects.  A real integration would replace
    this class with a REST/gRPC client to Runway, Veo, or a local model.
    """

    backend_name: str = "mock-generation-v1"
    backend_version: str = "1.0.0"

    # Attribute sets keyed on coarse shot intent category
    _MOCK_ATTRIBUTES: dict[str, list[str]] = {
        "tense": [
            "high_angle", "cold_lighting", "hard_shadows", "medium_framing",
            "desaturated_palette", "tight_composition",
        ],
        "warm": [
            "golden_hour_light", "soft_shadows", "warm_palette",
            "medium_framing", "shallow_depth_of_field",
        ],
        "default": [
            "neutral_lighting", "balanced_shadows", "medium_framing",
            "standard_focal_length",
        ],
    }

    def _intent_key(self, intent: str) -> str:
        lower = intent.lower()
        if any(w in lower for w in ("tense", "threat", "danger", "confrontation", "fear")):
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
            # Diagnostic keys consumed by ReviewerAgent
            "attributes": attributes,
            "quality_score": 0.85,
            "metadata": {
                "framing": (shot.get("camera") or {}).get("framing") or "medium",
                "mood": key,
                "color_temp_k": color_temp_k,
            },
        }


def _utc_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# GenerationAgent
# ---------------------------------------------------------------------------

class GenerationAgent(BaseAgent):
    """Runs a generation backend for a shot and gates the result.

    Workflow per call:
      1. Call ``plugin.generate(shot, production)`` → raw GenerationResult dict
      2. Pass the result to ReviewerAgent for quality gating
      3. Attach reviewer verdict back onto the GenerationResult
      4. Return GenerationResult + gate verdict + updated shot status

    Input dict:
        shot (dict)                — Shot-shaped dict (shot_id, intent, camera, …)
        production (dict)          — Full production document dict
        plugin (GenerationPlugin)  — Optional backend override; defaults to
                                     MockGenerationPlugin
        check_types (list[str])    — ReviewerAgent check types to run
                                     (default: all 5)

    Output dict:
        generation_result (dict)   — GenerationResult-shaped dict with reviewer
                                     verdict embedded
        verdict (str)              — "pass" | "warn" | "fail"
        score (float)              — 0.0–1.0 reviewer aggregate score
        blocking (bool)            — True = do not deliver to user
        shot_status (str)          — suggested Shot.status after this run:
                                       "generated"   when verdict == "pass"/"warn"
                                       "rejected"    when blocking == True
        suggestion_layer (dict | None)
    """

    WRITABLE_FIELDS: frozenset[str] = frozenset({
    DIAGNOSTIC_KEYS: frozenset[str] = frozenset({
        "generation_result",
        "verdict",
        "blocking",
        "score",
        "checks",
        "suggestion_layer",
        "shot_id",
        "shot_status",
    })
        "Shot.generation",
        "Shot.status",
        "Shot.version_history",
    })

    def __init__(self, plugin: GenerationPlugin | None = None) -> None:
        super().__init__(name="generation_agent")
        self._default_plugin: GenerationPlugin = plugin or MockGenerationPlugin()
        self._reviewer = ReviewerAgent()

    def run(self, input: dict) -> dict:  # noqa: A002
        shot = input.get("shot") or {}
        production = input.get("production") or {}
        check_types = input.get("check_types") or None

        # Allow per-call plugin override
        plugin: GenerationPlugin = input.get("plugin") or self._default_plugin

        # 1. Generate
        gen_result = plugin.generate(shot, production)

        # 2. Gate via ReviewerAgent
        reviewer_input: dict = {
            "shot_id": shot.get("shot_id") or shot.get("id") or "unknown",
            "generation_result": gen_result,
            "production": production,
        }
        if check_types is not None:
            reviewer_input["check_types"] = check_types

        review = self._reviewer.run(reviewer_input)

        # 3. Embed verdict back into the generation result
        gen_result["reviewer_verdict"] = {
            "verdict": review["verdict"],
            "score": review["score"],
            "blocking": review["blocking"],
        }

        # 4. Derive shot status
        if review["blocking"]:
            shot_status = "rejected"
        else:
            shot_status = "generated"

        output = {
            "generation_result": gen_result,
            "verdict": review["verdict"],
            "score": review["score"],
            "blocking": review["blocking"],
            "shot_status": shot_status,
            "suggestion_layer": review.get("suggestion_layer"),
        }
        return self._enforce_scope(output)
