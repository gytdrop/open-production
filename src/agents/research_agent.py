"""ResearchAgent â€” collects references and validates the â‰¥3-sources gate.

Pipeline position: Stage 2 (Research / Discovery), after intent capture and
before any generation stage.

Gate rule (plan spec): the research stage is blocked unless at least 3
distinct, non-empty source IDs are collected.  A production that clears this
gate enters APPROVED state (for downstream agents); one that does not is
flagged with a "sources_insufficient" verdict and must not proceed.

Two operations:
  default / "gate" â€” original gate-check interface (backward compatible):
      Validates sources against the MIN_SOURCES threshold.
      Always returns: verdict, gate_passed, source_count, required_count,
      sources, missing, rationale, proposals.

  "synthesise" â€” angle-proposal interface (Stage 2 extended):
      Produces 3 research angle summaries for the topic with rationale and gaps.

  "validate" â€” lightweight gate check returning {valid, issues, source_count}.

Scope contract:
  WRITABLE_FIELDS is frozenset() â€” research agent proposes but never writes
  production state fields directly. Sources are written to Production.references
  only after human approval through the service layer.
"""
from __future__ import annotations

from agents.base import BaseAgent

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIN_SOURCES = 3  # plan specification: "at least 3 sources" gate

# ---------------------------------------------------------------------------
# Research angle templates keyed on topic register
# ---------------------------------------------------------------------------

_ANGLE_TEMPLATES = {
    "scientific": [
        {
            "angle_name": "Empirical Evidence Review",
            "summary": "Survey peer-reviewed findings directly relevant to the topic.",
            "source_types": ["academic paper", "meta-analysis", "clinical study"],
            "gaps": ["publication bias", "funding source disclosure", "replication status"],
            "rationale": (
                "Scientific claims require peer-reviewed grounding. "
                "This angle establishes the evidentiary floor for the production."
            ),
        },
        {
            "angle_name": "Expert Dissent & Critique",
            "summary": "Surface credentialled voices that challenge the mainstream framing.",
            "source_types": ["review article", "letter to editor", "expert interview"],
            "gaps": ["fringe vs. credible minority", "conflict of interest"],
            "rationale": (
                "No scientific consensus is unanimous. Representing credible dissent "
                "strengthens the production's epistemic honesty."
            ),
        },
        {
            "angle_name": "Real-World Application Gap",
            "summary": "Document where lab findings diverge from field or policy reality.",
            "source_types": ["implementation report", "policy brief", "case study"],
            "gaps": ["access disparities", "translation lag", "regulatory lag"],
            "rationale": (
                "The gap between evidence and practice is often the most compelling story. "
                "This angle surfaces that gap with concrete examples."
            ),
        },
    ],
    "cultural": [
        {
            "angle_name": "Historical Context",
            "summary": "Trace how the topic has been understood and represented over time.",
            "source_types": ["archival material", "historical account", "documentary record"],
            "gaps": ["whose history is centred", "surviving record bias"],
            "rationale": (
                "Context prevents presentism. Historical framing locates the topic "
                "in a longer arc of human understanding."
            ),
        },
        {
            "angle_name": "Lived Experience",
            "summary": "Centre first-person accounts from people directly affected by the topic.",
            "source_types": ["interview", "oral history", "memoir", "testimony"],
            "gaps": ["sample diversity", "power dynamics in testimony collection"],
            "rationale": (
                "Lived experience grounds abstract topics in human stakes. "
                "First-person voices resist over-simplification."
            ),
        },
        {
            "angle_name": "Structural / Systemic Frame",
            "summary": "Analyse the institutional and systemic forces shaping the topic.",
            "source_types": ["policy analysis", "investigative report", "systemic review"],
            "gaps": ["causation vs. correlation", "data availability by group"],
            "rationale": (
                "Individual stories without structural context can mislead. "
                "This angle keeps the production honest about power and access."
            ),
        },
    ],
    "general": [
        {
            "angle_name": "Current State of Play",
            "summary": "Map the topic as it stands today: key actors and what is contested.",
            "source_types": ["recent news", "trade publication", "expert commentary"],
            "gaps": ["recency bias", "dominant narrative vs. marginalised perspectives"],
            "rationale": (
                "The production audience needs a current baseline. "
                "This angle establishes shared ground before introducing complexity."
            ),
        },
        {
            "angle_name": "Stakeholder Mapping",
            "summary": "Identify who benefits, who is harmed, and who has voice on this topic.",
            "source_types": ["stakeholder report", "advocacy document", "industry analysis"],
            "gaps": ["whose interests are not represented", "power asymmetries"],
            "rationale": (
                "Stakeholder framing makes the politics of the topic visible "
                "without reducing it to a simple binary."
            ),
        },
        {
            "angle_name": "What Is Still Unknown",
            "summary": "Document open questions, methodological limits, and knowledge gaps.",
            "source_types": ["literature review", "research agenda", "gap analysis"],
            "gaps": ["known unknowns vs. unknown unknowns", "research funding priorities"],
            "rationale": (
                "Intellectual honesty about limits is more credible than false certainty. "
                "This angle prepares the audience for nuance."
            ),
        },
    ],
}


def _topic_key(topic: str) -> str:
    t = topic.lower()
    scientific_signals = ("research", "study", "science", "clinical", "data",
                          "medical", "crispr", "gene", "health", "experiment")
    cultural_signals = ("culture", "history", "community", "society", "identity",
                        "race", "gender", "art", "media", "representation")
    if any(w in t for w in scientific_signals):
        return "scientific"
    if any(w in t for w in cultural_signals):
        return "cultural"
    return "general"


class ResearchAgent(BaseAgent):
    """Collects references, enforces the â‰¥3-sources gate, and proposes research angles.

    Default / "gate" operation â€” backward-compatible gate interface:
        Input:  topic (str), sources (list[dict]), require_min_sources (int, optional)
        Output: verdict, gate_passed, source_count, required_count,
                sources, missing, rationale, proposals

    "synthesise" operation â€” angle-proposal interface:
        Input:  operation="synthesise", topic (str), sources (list[dict], optional)
        Output: proposals (list[dict] â€” 3 angles), topic, source_count

    "validate" operation â€” lightweight gate check:
        Input:  operation="validate", sources (list[dict])
        Output: valid (bool), issues (list[str]), source_count (int)
    """


    WRITABLE_FIELDS: frozenset[str] = frozenset()  # proposals only; writes go through service
    DIAGNOSTIC_KEYS: frozenset[str] = frozenset({
        "verdict",
        "gate_passed",
        "source_count",
        "required_count",
        "sources",
        "missing",
        "rationale",
        "topic",
        "proposals",
    })
    DIAGNOSTIC_KEYS: frozenset[str] = frozenset({
        "verdict", "gate_passed", "source_count", "required_count",
        "sources", "missing", "rationale", "topic", "proposals",
    })

    def __init__(self) -> None:
        super().__init__(name="research_agent")

    def run(self, input: dict) -> dict:  # noqa: A002
        operation = str(input.get("operation") or "gate")
        if operation == "synthesise":
            return self._synthesise(input)
        if operation == "validate":
            return self._validate(input)
        return self._gate(input)

    # ------------------------------------------------------------------

    def _gate(self, input: dict) -> dict:
        """Original gate-check interface (backward compatible)."""
        topic = str(input.get("topic") or "")
        raw_sources = list(input.get("sources") or [])
        required = int(input.get("require_min_sources") or MIN_SOURCES)

        valid_sources = [
            s for s in raw_sources
            if isinstance(s, dict) and str(s.get("id") or "").strip()
        ]
        count = len(valid_sources)
        gate_passed = count >= required
        missing = max(0, required - count)

        if gate_passed:
            verdict = "sources_sufficient"
            rationale = (
                f"Research gate passed: {count} source(s) collected for "
                f"'{topic}' â€” meets the minimum of {required}."
            )
        else:
            verdict = "sources_insufficient"
            rationale = (
                f"Research gate BLOCKED: only {count} source(s) collected for "
                f"'{topic}' â€” {missing} more required (minimum {required})."
            )

        proposal = {
            "label": "Research brief",
            "topic": topic,
            "source_count": count,
            "sources": valid_sources,
            "gate_passed": gate_passed,
            "rationale": rationale,
        }

        output = {
            "verdict": verdict,
            "gate_passed": gate_passed,
            "source_count": count,
            "required_count": required,
            "sources": valid_sources,
            "missing": missing,
            "rationale": rationale,
            "proposals": [proposal],
        }
        return self._enforce_scope(output)

    def _synthesise(self, input: dict) -> dict:
        topic = str(input.get("topic") or "")
        sources = list(input.get("sources") or [])
        key = _topic_key(topic)
        return {
            "proposals": list(_ANGLE_TEMPLATES[key]),
            "topic": topic,
            "source_count": len(sources),
        }

    def _validate(self, input: dict) -> dict:
        """Alias for _gate â€” 'validate' and default operation share the same output shape."""
        return self._gate(input)

