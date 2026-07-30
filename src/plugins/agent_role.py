"""AgentRolePlugin protocol and built-in mock implementations.

An AgentRolePlugin is a scoped agent adapter that runs inside the multi-agent
crew. It owns:

  - a unique role name (e.g. `"copywriter"`, `"legal_reviewer"`)
  - the scope contract \u2014 what it can read / write on the Production
  - the `run(input, production) -> output` body
  - whether its verdict is blocking or advisory
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from src.plugins.base import PluginCapability, PluginHealth


@dataclass(frozen=True)
class AgentRoleResult:
    """Returned by AgentRolePlugin.run()."""

    role_name: str
    proposal: dict  # role-specific proposal payload
    blocking: bool  # True if rejection by this role halts the pipeline
    score: float = 0.0
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "role_name": self.role_name,
            "proposal": dict(self.proposal),
            "blocking": self.blocking,
            "score": self.score,
            "notes": self.notes,
        }


@runtime_checkable
class AgentRolePlugin(Protocol):
    """Contract every agent-role plugin must satisfy."""

    role_name: str
    capabilities: frozenset[PluginCapability]
    scope_contract: dict  # {can_read: [...], can_write: [...]}

    def run(
        self,
        input: dict,        # noqa: A002 \u2014 'input' is the public API name in spec
        production: dict,
        *,
        options: dict | None = None,
    ) -> AgentRoleResult:
        """Run this agent role once and return a proposal + gate signal."""
        ...

    def health_check(self) -> PluginHealth:
        """Return current plugin health."""
        ...


# ---------------------------------------------------------------------------
# Built-in mock implementations
# ---------------------------------------------------------------------------


class CustomReviewerRole:
    """Advisory reviewer role.

    Adds a subjective quality verdict on top of the built-in ReviewerAgent
    (which runs the five standard checks). Blocking OFF \u2014 the user still
    sees this verdict but it doesn't hard-gate the pipeline.
    """

    role_name: str = "subjective_reviewer"
    capabilities: frozenset[PluginCapability] = frozenset(
        {PluginCapability.ADVISORY, PluginCapability.BLOCKING_REVIEW}
    )
    scope_contract: dict = field(
        default_factory=lambda: {
            "can_read": ["Production.*", "Shot.*", "Scene.*"],
            "can_write": ["Shot.version_history"],
        }
    )

    def run(
        self,
        input: dict,
        production: dict,
        *,
        options: dict | None = None,
    ) -> AgentRoleResult:
        shots = sum(len(s.get("shots", [])) for s in production.get("scenes", []))
        quality = options.get("min_quality", 0.7) if options else 0.7
        # Heuristic only \u2014 advisory role; score derived from shot count.
        score = 0.6 + min(0.4, shots * 0.05)
        blocking = False  # advisory by default
        if options and options.get("strict"):
            blocking = score < quality
        return AgentRoleResult(
            role_name=self.role_name,
            proposal={
                "verdict": "pass" if score >= quality else "warn",
                "shot_count": shots,
                "threshold": quality,
            },
            blocking=blocking,
            score=score,
            notes=f"subjective_reviewer advisory verdict at {score:.2f}",
        )

    def health_check(self) -> PluginHealth:
        from datetime import datetime, timezone

        return PluginHealth(
            healthy=True,
            plugin_name=self.role_name,
            checked_at=datetime.now(timezone.utc).isoformat(),
        )


class ComplianceReviewerRole:
    """Hard-gate compliance reviewer (e.g. brand safety / legal).

    Blocking on. A rejection halts the pipeline.
    """

    role_name: str = "compliance_reviewer"
    capabilities: frozenset[PluginCapability] = frozenset(
        {PluginCapability.BLOCKING_REVIEW}
    )
    scope_contract: dict = field(
        default_factory=lambda: {
            "can_read": ["Production.*", "Shot.intent", "Shot.script"],
            "can_write": ["Shot.status"],
        }
    )

    FORBIDDEN_PATTERNS = frozenset({"confidential", "do not share", "internal only"})

    def run(
        self,
        input: dict,
        production: dict,
        *,
        options: dict | None = None,
    ) -> AgentRoleResult:
        # Walk every script line and check for compliance patterns.
        findings: list[str] = []
        for scene in production.get("scenes", []):
            for shot in scene.get("shots", []):
                script_text = str(shot.get("script") or "").lower()
                for pattern in self.FORBIDDEN_PATTERNS:
                    if pattern in script_text:
                        findings.append(
                            f"shot {shot.get('id')}: contains {pattern!r}"
                        )
        score = 1.0 if not findings else max(0.0, 1.0 - 0.1 * len(findings))
        blocking = bool(findings)
        return AgentRoleResult(
            role_name=self.role_name,
            proposal={
                "verdict": "pass" if not findings else "fail",
                "findings": findings,
            },
            blocking=blocking,
            score=score,
            notes=f"compliance_reviewer found {len(findings)} issue(s)",
        )

    def health_check(self) -> PluginHealth:
        from datetime import datetime, timezone

        return PluginHealth(
            healthy=True,
            plugin_name=self.role_name,
            checked_at=datetime.now(timezone.utc).isoformat(),
        )
