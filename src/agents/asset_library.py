"""AssetLibraryAgent — assembles the asset inventory and reports gaps.

Stage 15 of the 26-stage production pipeline.

Scope contract:
  Can write:  Production.metadata["asset_library"]  (sub-key partition)
  Cannot write: Shot.*, Scene.*, Production.characters, Production.environments

Sub-key partition (paired with PublisherAgent):
  This agent owns ``Production.metadata["asset_library"]``.
  ``PublisherAgent`` owns the disjoint key ``Production.metadata["publish_manifest"]``.
  These namespaces are non-overlapping by convention. There is no runtime
  enforcement of disjointness beyond this docstring; review any change that
  adds a new top-level key under ``Production.metadata`` to ensure it does
  not step on another agent's reserved key.

The agent collects every named asset from the Production document:
  • Production.references          — explicit media references
  • Production.brand_kit           — logo files, palette tokens, typography tokens
  • Production.style_tokens        — creative style tokens
  • Character.visual_anchors       — per-character reference images
  • Environment.visual_anchors     — per-environment reference images

It then runs a gap-detection pass: assets that are declared (present in the
schema with an id) but have no URI or SHA-256 hash are flagged as gaps.

Three operations:
  "assemble" (default) — collect and categorise all assets; report gaps.
  "check_gaps"         — gap-only report (lighter weight; same logic).
  "ingest"             — hash raw bytes via AssetLibraryService and store
                         them content-addressed; returns sha256 + uri.
  "retrieve"           — retrieve stored bytes by sha256 from the service.

Output (assemble):
    assets (list[dict])        — full inventory, each entry:
                                    id, kind, label, uri, sha256, source, status
    gaps (list[dict])          — assets missing uri or sha256:
                                    id, kind, label, source, reason
    summary (dict)             — counts: total, complete, incomplete, gap_count
    ready (bool)               — True when gap_count == 0

Output (check_gaps):
    gaps (list[dict])          — same as above
    gap_count (int)
    ready (bool)

Output (ingest):
    sha256 (str)               — hex digest of ingested bytes
    uri (str)                  — content-address URI: "asset://<sha256>"
    size (int)                 — byte count
    already_existed (bool)     — True if the object was already in the store

Output (retrieve):
    sha256 (str)               — hex digest
    filename (str)
    kind (str)
    label (str)
    size (int)
    ingested_at (str)
    ingested_by (str)
    found (bool)               — False (and other fields absent) when not found
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from agents.base import BaseAgent

if TYPE_CHECKING:
    from service.asset_library_service import AssetLibraryService

# ---------------------------------------------------------------------------
# Asset kind labels
# ---------------------------------------------------------------------------

_KIND_REFERENCE = "reference"
_KIND_LOGO = "logo"
_KIND_PALETTE = "style_token:color"
_KIND_TYPOGRAPHY = "style_token:typography"
_KIND_STYLE_TOKEN = "style_token"
_KIND_VISUAL_ANCHOR = "visual_anchor"


def _asset_entry(
    asset_id: str,
    kind: str,
    label: str,
    uri: str | None,
    sha256: str | None,
    source: str,
) -> dict:
    """Build a normalised asset entry dict."""
    status = "complete" if (uri or sha256) else "incomplete"
    return {
        "id": asset_id,
        "kind": kind,
        "label": label,
        "uri": uri,
        "sha256": sha256,
        "source": source,
        "status": status,
    }


def _gap_entry(asset_id: str, kind: str, label: str, source: str, reason: str) -> dict:
    return {"id": asset_id, "kind": kind, "label": label, "source": source, "reason": reason}


def _collect_assets(production: dict) -> list[dict]:
    """Walk the production dict and collect every known asset."""
    assets: list[dict] = []

    # ---- Production.references ------------------------------------------------
    for ref in production.get("references") or []:
        assets.append(_asset_entry(
            asset_id=ref.get("id", "ref_unknown"),
            kind=_KIND_REFERENCE,
            label=ref.get("label") or ref.get("id", ""),
            uri=ref.get("uri"),
            sha256=ref.get("sha256"),
            source="Production.references",
        ))

    # ---- Production.brand_kit -------------------------------------------------
    brand_kit = production.get("brand_kit") or {}

    for logo in brand_kit.get("logos") or []:
        assets.append(_asset_entry(
            asset_id=logo.get("id", "ref_unknown"),
            kind=_KIND_LOGO,
            label=logo.get("label") or logo.get("id", ""),
            uri=logo.get("uri"),
            sha256=logo.get("sha256"),
            source="Production.brand_kit.logos",
        ))

    for tok in brand_kit.get("palette") or []:
        assets.append(_asset_entry(
            asset_id=tok.get("id", "tok_unknown"),
            kind=_KIND_PALETTE,
            label=tok.get("name") or tok.get("id", ""),
            uri=None,           # style tokens are inline values, no URI
            sha256=None,
            source="Production.brand_kit.palette",
        ))

    for tok in brand_kit.get("typography") or []:
        assets.append(_asset_entry(
            asset_id=tok.get("id", "tok_unknown"),
            kind=_KIND_TYPOGRAPHY,
            label=tok.get("name") or tok.get("id", ""),
            uri=None,
            sha256=None,
            source="Production.brand_kit.typography",
        ))

    # ---- Production.style_tokens ----------------------------------------------
    for tok in production.get("style_tokens") or []:
        assets.append(_asset_entry(
            asset_id=tok.get("id", "tok_unknown"),
            kind=_KIND_STYLE_TOKEN,
            label=tok.get("name") or tok.get("id", ""),
            uri=None,
            sha256=None,
            source="Production.style_tokens",
        ))

    # ---- Character.visual_anchors ---------------------------------------------
    for char in production.get("characters") or []:
        char_name = char.get("name") or char.get("id", "unknown")
        for anchor in char.get("visual_anchors") or []:
            assets.append(_asset_entry(
                asset_id=anchor.get("id", "ref_unknown"),
                kind=_KIND_VISUAL_ANCHOR,
                label=anchor.get("label") or f"{char_name} anchor",
                uri=anchor.get("uri"),
                sha256=anchor.get("sha256"),
                source=f"Character[{char_name}].visual_anchors",
            ))

    # ---- Environment.visual_anchors -------------------------------------------
    for env in production.get("environments") or []:
        env_name = env.get("name") or env.get("id", "unknown")
        for anchor in env.get("visual_anchors") or []:
            assets.append(_asset_entry(
                asset_id=anchor.get("id", "ref_unknown"),
                kind=_KIND_VISUAL_ANCHOR,
                label=anchor.get("label") or f"{env_name} anchor",
                uri=anchor.get("uri"),
                sha256=anchor.get("sha256"),
                source=f"Environment[{env_name}].visual_anchors",
            ))

    return assets


def _detect_gaps(assets: list[dict]) -> list[dict]:
    """Return gap entries for any asset that lacks both uri and sha256.

    Style tokens (palette, typography, standalone) are inline value objects —
    they do not need a URI, so they are excluded from gap reporting.
    """
    no_uri_kinds = {_KIND_PALETTE, _KIND_TYPOGRAPHY, _KIND_STYLE_TOKEN}
    gaps: list[dict] = []
    for a in assets:
        if a["kind"] in no_uri_kinds:
            continue
        if not a["uri"] and not a["sha256"]:
            gaps.append(_gap_entry(
                asset_id=a["id"],
                kind=a["kind"],
                label=a["label"],
                source=a["source"],
                reason="Missing both uri and sha256 — asset not yet ingested.",
            ))
    return gaps


class AssetLibraryAgent(BaseAgent):
    """Assembles the asset inventory from a Production document and detects gaps.

    Optionally wraps an AssetLibraryService instance for content-addressed
    binary storage (ingest / retrieve operations).

    Input dict:
        operation (str)         — "assemble" (default) | "check_gaps"
                                  | "ingest" | "retrieve"
        production (dict)       — the full production document as a dict
                                  (assemble / check_gaps only)

        # ingest
        data (bytes)            — raw binary content to store
        filename (str)          — original filename
        kind (str)              — ReferenceKind ("image", "video", …)
        label (str)             — human-readable label
        ingested_by (str)       — actor string (default: "system")

        # retrieve
        sha256 (str)            — hex digest to look up

    Output (operation='assemble'):
        assets (list[dict])     — full inventory
        gaps (list[dict])       — assets missing uri and sha256
        summary (dict)          — {total, complete, incomplete, gap_count}
        ready (bool)            — True when gap_count == 0

    Output (operation='check_gaps'):
        gaps (list[dict])
        gap_count (int)
        ready (bool)

    Output (operation='ingest'):
        sha256 (str)
        uri (str)               — "asset://<sha256>"
        size (int)
        already_existed (bool)

    Output (operation='retrieve'):
        found (bool)
        sha256, filename, kind, label, size, ingested_at, ingested_by
        (all present only when found=True)
    """

    WRITABLE_FIELDS: frozenset[str] = frozenset({"Production.metadata"})
    DIAGNOSTIC_KEYS: frozenset[str] = frozenset({
        "assets",
        "gaps",
        "summary",
        "ready",
        "gap_count",
        "proposals",
        "sha256",
        "uri",
        "size",
        "already_existed",
        "filename",
        "ingested_at",
        "ingested_by",
        "found",
        "error",
        "kind",
        "label",
    })

    def __init__(self, service: "AssetLibraryService | None" = None) -> None:
        super().__init__(name="asset_library_agent")
        self._service = service

    def run(self, input: dict) -> dict:  # noqa: A002
        operation = str(input.get("operation") or "assemble")

        if operation == "ingest":
            return self._enforce_scope(self._ingest(input))
        if operation == "retrieve":
            return self._enforce_scope(self._retrieve(input))

        production = input.get("production") or {}
        assets = _collect_assets(production)
        gaps = _detect_gaps(assets)

        if operation == "check_gaps":
            output = {
                "gaps": gaps,
                "gap_count": len(gaps),
                "ready": len(gaps) == 0,
            }
            return self._enforce_scope(output)

        # Default: assemble
        complete = sum(1 for a in assets if a["status"] == "complete")
        incomplete = len(assets) - complete

        output = {
            "assets": assets,
            "gaps": gaps,
            "summary": {
                "total": len(assets),
                "complete": complete,
                "incomplete": incomplete,
                "gap_count": len(gaps),
            },
            "ready": len(gaps) == 0,
        }
        return self._enforce_scope(output)

    # ------------------------------------------------------------------
    # ingest / retrieve delegates
    # ------------------------------------------------------------------

    def _ingest(self, input: dict) -> dict:
        """Delegate an ingest operation to the wrapped AssetLibraryService."""
        if self._service is None:
            return {
                "error": "No AssetLibraryService configured on this agent instance.",
                "found": False,
            }
        data = input.get("data")
        if not isinstance(data, (bytes, bytearray)):
            return {"error": "ingest requires 'data' (bytes).", "found": False}
        result = self._service.ingest(
            data=bytes(data),
            filename=str(input.get("filename") or "asset"),
            kind=str(input.get("kind") or "image"),
            label=str(input.get("label") or ""),
            ingested_by=str(input.get("ingested_by") or "system"),
        )
        return {
            "sha256": result.sha256,
            "uri": result.uri,
            "size": result.size,
            "already_existed": result.already_existed,
        }

    def _retrieve(self, input: dict) -> dict:
        """Delegate a retrieve operation to the wrapped AssetLibraryService."""
        if self._service is None:
            return {"found": False, "error": "No AssetLibraryService configured."}
        sha256 = str(input.get("sha256") or "")
        if not sha256:
            return {"found": False, "error": "retrieve requires 'sha256'."}
        result = self._service.retrieve(sha256)
        if result is None:
            return {"found": False}
        return {
            "found": True,
            "sha256": result.sha256,
            "filename": result.filename,
            "kind": result.kind,
            "label": result.label,
            "size": result.size,
            "ingested_at": result.ingested_at,
            "ingested_by": result.ingested_by,
        }
