"""Tests for GenerationAgent and MockGenerationPlugin — Stage 16."""
from __future__ import annotations

import pytest

from agents.generation import GenerationAgent, MockGenerationPlugin, GenerationPlugin


@pytest.fixture
def agent():
    return GenerationAgent()


@pytest.fixture
def shot():
    return {
        "shot_id": "shot_scene01_01_abc123",
        "scene_id": "scene_0001",
        "intent": "Wide establishing shot — show the protagonist in the empty office.",
        "duration_sec": 4.0,
        "camera": {"framing": "wide", "angle": "eye_level"},
        "lighting": {"color_temp_k": 5600, "preset_id": "daylight_neutral"},
    }


@pytest.fixture
def production():
    return {
        "id": "prod_testprod001",
        "state": "DRAFT",
        "intent": {"topic": "Corporate story", "tone": "professional"},
        "characters": [],
        "environments": [],
    }


# ---------------------------------------------------------------------------
# Basic output shape
# ---------------------------------------------------------------------------

def test_generation_agent_returns_required_keys(agent, shot, production):
    """run() must return generation_result, verdict, score, blocking, shot_status."""
    out = agent.run({"shot": shot, "production": production})
    assert "generation_result" in out
    assert "verdict" in out
    assert "score" in out
    assert "blocking" in out
    assert "shot_status" in out


def test_generation_result_has_required_fields(agent, shot, production):
    """generation_result must contain id, produced_at, backend, output_uri."""
    out = agent.run({"shot": shot, "production": production})
    gr = out["generation_result"]
    assert gr["id"].startswith("gen_")
    assert gr["produced_at"]
    assert gr["backend"] == "mock-generation-v1"
    assert gr["output_uri"] is not None
    assert gr["output_sha256"] is not None
    assert gr["reviewer_verdict"]  # must be populated after gating


def test_generation_result_reviewer_verdict_embedded(agent, shot, production):
    """reviewer_verdict inside generation_result must have verdict/score/blocking."""
    out = agent.run({"shot": shot, "production": production})
    rv = out["generation_result"]["reviewer_verdict"]
    assert "verdict" in rv
    assert "score" in rv
    assert "blocking" in rv


# ---------------------------------------------------------------------------
# Verdict + shot status logic
# ---------------------------------------------------------------------------

def test_generation_agent_pass_verdict_yields_generated_status(agent, shot, production):
    """When reviewer passes, shot_status should be 'generated'."""
    out = agent.run({"shot": shot, "production": production})
    # Default mock always scores well; DRAFT state is in the permitted set
    assert out["verdict"] in ("pass", "warn")
    assert out["shot_status"] == "generated"
    assert out["blocking"] is False


def test_generation_agent_rejected_state_triggers_blocking(agent, shot):
    """Production in PUBLISHED state is not in the reviewer's permitted states,
    causing a fail on the stage_gate check → blocking=True → shot_status='rejected'.
    """
    production_published = {
        "id": "prod_pubtest001",
        "state": "PUBLISHED",
        "intent": {"topic": "Test"},
        "characters": [],
    }
    out = agent.run({"shot": shot, "production": production_published})
    assert out["blocking"] is True
    assert out["shot_status"] == "rejected"


# ---------------------------------------------------------------------------
# Score and blocking thresholds
# ---------------------------------------------------------------------------

def test_generation_agent_score_is_float_in_range(agent, shot, production):
    """score must be a float between 0.0 and 1.0."""
    out = agent.run({"shot": shot, "production": production})
    assert isinstance(out["score"], float)
    assert 0.0 <= out["score"] <= 1.0


# ---------------------------------------------------------------------------
# MockGenerationPlugin
# ---------------------------------------------------------------------------

def test_mock_plugin_is_generation_plugin():
    """MockGenerationPlugin must satisfy the GenerationPlugin protocol."""
    plugin = MockGenerationPlugin()
    assert isinstance(plugin, GenerationPlugin)


def test_mock_plugin_returns_required_keys(shot, production):
    """MockGenerationPlugin.generate() returns all required keys."""
    plugin = MockGenerationPlugin()
    result = plugin.generate(shot, production)
    for key in ("id", "produced_at", "produced_by", "backend", "backend_version",
                "prompt_hash", "output_uri", "output_sha256", "attributes",
                "quality_score", "metadata"):
        assert key in result, f"missing key: {key!r}"


def test_mock_plugin_gen_id_format(shot, production):
    """MockGenerationPlugin.generate() must return id starting with 'gen_'."""
    plugin = MockGenerationPlugin()
    result = plugin.generate(shot, production)
    assert result["id"].startswith("gen_")


def test_mock_plugin_tense_intent_uses_tense_attributes(production):
    """Tense intent selects the tense attribute set."""
    plugin = MockGenerationPlugin()
    tense_shot = {"shot_id": "shot_t_001_aaa111", "intent": "The threat closes in on the cornered protagonist."}
    result = plugin.generate(tense_shot, production)
    assert "cold_lighting" in result["attributes"] or "high_angle" in result["attributes"]


def test_mock_plugin_warm_intent_uses_warm_attributes(production):
    """Warm intent selects the warm attribute set."""
    plugin = MockGenerationPlugin()
    warm_shot = {"shot_id": "shot_w_001_bbb222", "intent": "A warm reunion full of love and joy."}
    result = plugin.generate(warm_shot, production)
    assert "golden_hour_light" in result["attributes"] or "warm_palette" in result["attributes"]


def test_mock_plugin_prompt_hash_is_sha256(shot, production):
    """prompt_hash must be a 64-char hex string (SHA-256)."""
    plugin = MockGenerationPlugin()
    result = plugin.generate(shot, production)
    assert len(result["prompt_hash"]) == 64
    assert all(c in "0123456789abcdef" for c in result["prompt_hash"])


# ---------------------------------------------------------------------------
# Plugin injection
# ---------------------------------------------------------------------------

def test_generation_agent_accepts_custom_plugin(shot, production):
    """A custom plugin can be injected via run() input dict."""

    class DoubleQualityPlugin:
        backend_name = "test-double"
        backend_version = "0.0.1"

        def generate(self, shot, production):  # noqa: ARG002
            import uuid
            return {
                "id": "gen_" + uuid.uuid4().hex[:12],
                "produced_at": "2026-01-01T00:00:00+00:00",
                "produced_by": "test-double",
                "backend": "test-double",
                "backend_version": "0.0.1",
                "prompt_hash": "a" * 64,
                "output_uri": "mock://test/output.mp4",
                "output_sha256": "b" * 64,
                "reviewer_verdict": {},
                "cost_estimate_usd": 0.0,
                "latency_ms": 50,
                "attributes": ["neutral_lighting"],
                "quality_score": 0.99,
                "metadata": {"framing": "medium", "mood": "default", "color_temp_k": 5600},
            }

    out = GenerationAgent().run({
        "shot": shot,
        "production": production,
        "plugin": DoubleQualityPlugin(),
    })
    assert out["generation_result"]["backend"] == "test-double"
    assert out["verdict"] in ("pass", "warn", "fail")


# ---------------------------------------------------------------------------
# Safe on minimal input
# ---------------------------------------------------------------------------

def test_generation_agent_safe_on_empty_input(agent):
    """run({}) must not raise (K.11 rule 4)."""
    out = agent.run({})
    assert "generation_result" in out
    assert "verdict" in out


# ---------------------------------------------------------------------------
# Scope contract
# ---------------------------------------------------------------------------

def test_generation_agent_writable_fields_contract(agent):
    """WRITABLE_FIELDS must cover Shot.generation, Shot.status, Shot.version_history."""
    assert "Shot.generation" in GenerationAgent.WRITABLE_FIELDS
    assert "Shot.status" in GenerationAgent.WRITABLE_FIELDS
    assert "Shot.version_history" in GenerationAgent.WRITABLE_FIELDS
