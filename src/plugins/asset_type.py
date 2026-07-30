"""AssetTypePlugin protocol and built-in mock implementations.

An AssetTypePlugin knows how to validate and shape one kind of asset
(image, video, audio, document). It defines:

  - the JSON Schema for the asset's metadata
  - a validator that runs over a dict
  - a provenance requirement (what fields must be present)

Built-in mocks cover the four asset kinds the system actually uses today.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from src.plugins.base import PluginCapability, PluginHealth


@dataclass(frozen=True)
class AssetValidationResult:
    """Outcome of AssetTypePlugin.validate()."""

    plugin_name: str
    asset_id: str
    valid: bool
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "plugin_name": self.plugin_name,
            "asset_id": self.asset_id,
            "valid": self.valid,
            "issues": list(self.issues),
        }


@runtime_checkable
class AssetTypePlugin(Protocol):
    """Contract every asset-type plugin must satisfy."""

    name: str
    asset_kind: str  # matches production_document.ReferenceKind values
    capabilities: frozenset[PluginCapability]

    def validate(self, asset: dict) -> AssetValidationResult:
        """Return whether `asset` is a valid instance of this asset kind."""
        ...

    def required_fields(self) -> list[str]:
        """Names of fields that must be present on a valid asset."""
        ...

    def health_check(self) -> PluginHealth:
        """Return current plugin health."""
        ...


# ---------------------------------------------------------------------------
# Built-in mock implementations
# ---------------------------------------------------------------------------


class ImageAssetType:
    """Image asset type. Requires `uri` OR `sha256` and a non-empty label."""

    name: str = "image-asset-type-v1"
    asset_kind: str = "image"
    capabilities: frozenset[PluginCapability] = frozenset(
        {PluginCapability.CONTENT_ADDRESSED, PluginCapability.BINARY}
    )

    def validate(self, asset: dict) -> AssetValidationResult:
        issues: list[str] = []
        if not asset.get("label"):
            issues.append("missing label")
        if not (asset.get("uri") or asset.get("sha256")):
            issues.append("missing both uri and sha256")
        if asset.get("size_bytes") is not None:
            try:
                int(asset["size_bytes"])
            except (TypeError, ValueError):
                issues.append("size_bytes must be an integer")
        return AssetValidationResult(
            plugin_name=self.name,
            asset_id=str(asset.get("id", "")),
            valid=not issues,
            issues=issues,
        )

    def required_fields(self) -> list[str]:
        return ["id", "kind", "label", "uri_or_sha256"]

    def health_check(self) -> PluginHealth:
        from datetime import datetime, timezone

        return PluginHealth(
            healthy=True,
            plugin_name=self.name,
            checked_at=datetime.now(timezone.utc).isoformat(),
        )


class VideoAssetType:
    """Video asset type. Same provenance requirements + duration_sec optional."""

    name: str = "video-asset-type-v1"
    asset_kind: str = "video"
    capabilities: frozenset[PluginCapability] = frozenset(
        {PluginCapability.CONTENT_ADDRESSED, PluginCapability.BINARY}
    )

    def validate(self, asset: dict) -> AssetValidationResult:
        issues: list[str] = []
        if not asset.get("label"):
            issues.append("missing label")
        if not (asset.get("uri") or asset.get("sha256")):
            issues.append("missing both uri and sha256")
        duration = asset.get("duration_sec")
        if duration is not None:
            try:
                d = float(duration)
                if d <= 0:
                    issues.append("duration_sec must be positive")
            except (TypeError, ValueError):
                issues.append("duration_sec must be numeric")
        return AssetValidationResult(
            plugin_name=self.name,
            asset_id=str(asset.get("id", "")),
            valid=not issues,
            issues=issues,
        )

    def required_fields(self) -> list[str]:
        return ["id", "kind", "label", "uri_or_sha256"]

    def health_check(self) -> PluginHealth:
        from datetime import datetime, timezone

        return PluginHealth(
            healthy=True,
            plugin_name=self.name,
            checked_at=datetime.now(timezone.utc).isoformat(),
        )


class AudioAssetType:
    """Audio asset type. Same provenance requirements + sample_rate optional."""

    name: str = "audio-asset-type-v1"
    asset_kind: str = "audio"
    capabilities: frozenset[PluginCapability] = frozenset(
        {PluginCapability.CONTENT_ADDRESSED, PluginCapability.BINARY}
    )

    def validate(self, asset: dict) -> AssetValidationResult:
        issues: list[str] = []
        if not asset.get("label"):
            issues.append("missing label")
        if not (asset.get("uri") or asset.get("sha256")):
            issues.append("missing both uri and sha256")
        sr = asset.get("sample_rate_hz")
        if sr is not None:
            try:
                int(sr)
            except (TypeError, ValueError):
                issues.append("sample_rate_hz must be an integer")
        return AssetValidationResult(
            plugin_name=self.name,
            asset_id=str(asset.get("id", "")),
            valid=not issues,
            issues=issues,
        )

    def required_fields(self) -> list[str]:
        return ["id", "kind", "label", "uri_or_sha256"]

    def health_check(self) -> PluginHealth:
        from datetime import datetime, timezone

        return PluginHealth(
            healthy=True,
            plugin_name=self.name,
            checked_at=datetime.now(timezone.utc).isoformat(),
        )


class DocumentAssetType:
    """Document asset type. Textual capability. uri/sha256 optional (inline ok)."""

    name: str = "document-asset-type-v1"
    asset_kind: str = "document"
    capabilities: frozenset[PluginCapability] = frozenset(
        {PluginCapability.CONTENT_ADDRESSED, PluginCapability.TEXTUAL}
    )

    def validate(self, asset: dict) -> AssetValidationResult:
        issues: list[str] = []
        if not asset.get("label"):
            issues.append("missing label")
        if not (asset.get("uri") or asset.get("sha256") or asset.get("body")):
            issues.append("document must have uri, sha256, or inline body")
        return AssetValidationResult(
            plugin_name=self.name,
            asset_id=str(asset.get("id", "")),
            valid=not issues,
            issues=issues,
        )

    def required_fields(self) -> list[str]:
        return ["id", "kind", "label"]

    def health_check(self) -> PluginHealth:
        from datetime import datetime, timezone

        return PluginHealth(
            healthy=True,
            plugin_name=self.name,
            checked_at=datetime.now(timezone.utc).isoformat(),
        )
