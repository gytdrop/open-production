"""PublisherAgent — generates the publish manifest and readiness report.

Scope contract (Appendix K.10 of open-production-plan.md):
  Can write:  Production.metadata["publish_manifest"]  (sub-key partition)
  Cannot write: any generation parameter, Shot.*, Scene.*

Sub-key partition (paired with AssetLibraryAgent):
  This agent owns ``Production.metadata["publish_manifest"]``.
  ``AssetLibraryAgent`` owns the disjoint key ``Production.metadata["asset_library"]``.
  These namespaces are non-overlapping by convention. There is no runtime
  enforcement of disjointness beyond this docstring; review any change that
  adds a new top-level key under ``Production.metadata`` to ensure it does
  not step on another agent's reserved key.

The PublisherAgent sits at Stage 25 of the production pipeline.  It never
publishes silently — it proposes a manifest and waits for human approval.

Three proposal styles:
  "platform_native"  — optimised for a single platform (YouTube, TikTok, etc.)
  "multi_platform"   — master + derivative cuts for multiple platforms
  "archive"          — broadcast/archival master with full provenance chain
"""
from __future__ import annotations

from agents.base import BaseAgent
from validation.gates import PublicationGate

# ---------------------------------------------------------------------------
# Platform target definitions
# ---------------------------------------------------------------------------

_PLATFORMS = {
    "youtube":  {"aspect": "16:9", "max_duration_sec": None, "codec": "H.264", "resolution": "1080p"},
    "tiktok":   {"aspect": "9:16", "max_duration_sec": 60,   "codec": "H.264", "resolution": "1080p"},
    "instagram": {"aspect": "9:16", "max_duration_sec": 90,  "codec": "H.264", "resolution": "1080p"},
    "broadcast": {"aspect": "16:9", "max_duration_sec": None, "codec": "ProRes", "resolution": "4K"},
    "archive":   {"aspect": "16:9", "max_duration_sec": None, "codec": "ProRes", "resolution": "4K"},
}


def _build_platform_spec(platform: str) -> dict:
    spec = _PLATFORMS.get(platform.lower(), _PLATFORMS["youtube"])
    return {"platform": platform, **spec}


class PublisherAgent(BaseAgent):
    """Generates publish manifest proposals and runs a readiness check.

    Input dict:
        production_id (str)         — identifier of the production
        title (str)                 — production title
        platforms (list[str])       — target platforms (e.g. ["youtube", "tiktok"])
        doi (str)                   — DOI or unique identifier for the work
        authors (list[str])         — list of author / rights-holder names
        date (str)                  — release date (ISO 8601)
        rights_statement (str)      — rights and licensing note (optional)
        total_duration_sec (float)  — total runtime of the production
        scene_count (int)           — number of scenes
        shot_count (int)            — number of approved shots
        brand_kit (dict | None)     — optional brand kit reference

    Output dict:
        proposals (list[dict])      — up to 3 manifest proposals
        readiness_check (dict)      — result of PublicationGate check
        blocking (bool)             — True if readiness check fails
        missing_fields (list[str])  — fields required before publishing
    """

    WRITABLE_FIELDS: frozenset[str] = frozenset({"Production.metadata"})
    DIAGNOSTIC_KEYS: frozenset[str] = frozenset({
        "blocking",
        "missing_fields",
        "proposals",
        "readiness_check",
    })

    def __init__(self) -> None:
        super().__init__(name="publisher_agent")
        self._pub_gate = PublicationGate()

    def run(self, input: dict) -> dict:  # noqa: A002
        production_id = str(input.get("production_id") or "unknown")
        title = str(input.get("title") or "Untitled")
        platforms = input.get("platforms") or ["youtube"]
        doi = str(input.get("doi") or "")
        authors = input.get("authors") or []
        date = str(input.get("date") or "")
        rights_statement = str(input.get("rights_statement") or "All rights reserved.")
        total_duration_sec = float(input.get("total_duration_sec") or 0.0)
        scene_count = int(input.get("scene_count") or 0)
        shot_count = int(input.get("shot_count") or 0)

        # Run publication gate first
        metadata_for_gate = {"doi": doi, "authors": authors, "date": date}
        gate_ok, gate_reason = self._pub_gate.check(metadata_for_gate)

        # Identify missing fields
        missing: list[str] = []
        if not doi:
            missing.append("doi")
        if not authors:
            missing.append("authors")
        if not date:
            missing.append("date")
        if shot_count == 0:
            missing.append("shot_count (no approved shots)")

        proposals: list[dict] = []

        # Proposal 1: Platform-native (first platform in list)
        primary_platform = platforms[0] if platforms else "youtube"
        proposals.append({
            "label": f"Platform-native ({primary_platform})",
            "rationale": f"Optimised export for {primary_platform}. Single deliverable, fastest turnaround.",
            "targets": [_build_platform_spec(primary_platform)],
            "manifest": self._build_manifest(
                production_id, title, [primary_platform], doi, authors, date,
                rights_statement, total_duration_sec, scene_count, shot_count,
            ),
        })

        # Proposal 2: Multi-platform (all requested platforms)
        if len(platforms) > 1:
            proposals.append({
                "label": "Multi-platform package",
                "rationale": (
                    f"Master + {len(platforms)} platform derivatives. "
                    "One approval, all formats delivered simultaneously."
                ),
                "targets": [_build_platform_spec(p) for p in platforms],
                "manifest": self._build_manifest(
                    production_id, title, platforms, doi, authors, date,
                    rights_statement, total_duration_sec, scene_count, shot_count,
                ),
            })

        # Proposal 3: Archive master
        proposals.append({
            "label": "Archive master",
            "rationale": (
                "ProRes 4K master with full provenance chain. For long-term preservation. "
                "Default retention: 7 years (2 555 days) per SMPTE RP 2050."
            ),
            "targets": [_build_platform_spec("archive")],
            "manifest": self._build_manifest(
                production_id, title, ["archive"], doi, authors, date,
                rights_statement, total_duration_sec, scene_count, shot_count,
                include_provenance=True,
            ),
            "retention_policy": {
                "retention_days": 2555,
                "policy_ref": "SMPTE RP 2050 / open-production-plan Appendix K.26",
                "artifacts": ["production.json", "audit.jsonl"],
                "note": "Call ProductionService.archive() after PUBLISHED state to record expires_at.",
            },
        })

        return {
            "proposals": proposals[:3],
            "readiness_check": {
                "gate": "publication_gate",
                "passed": gate_ok,
                "reason": gate_reason,
            },
            "blocking": not gate_ok,
            "missing_fields": missing,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_manifest(
        production_id: str,
        title: str,
        platforms: list[str],
        doi: str,
        authors: list[str],
        date: str,
        rights_statement: str,
        total_duration_sec: float,
        scene_count: int,
        shot_count: int,
        include_provenance: bool = False,
    ) -> dict:
        manifest: dict = {
            "production_id": production_id,
            "title": title,
            "doi": doi or None,
            "authors": authors,
            "release_date": date or None,
            "rights": rights_statement,
            "total_duration_sec": total_duration_sec,
            "scene_count": scene_count,
            "shot_count": shot_count,
            "targets": platforms,
        }
        if include_provenance:
            manifest["provenance"] = {
                "production_id": production_id,
                "schema_version": "1.0.0",
                "audit_trail_required": True,
                "consistency_contracts_enforced": True,
            }
        return manifest
