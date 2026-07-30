"""ExportFormatPlugin protocol and built-in mock implementations.

An ExportFormatPlugin is a publish-target adapter: it takes a Production
dict and writes it out to one specific deliverable format / destination.

Examples (real-world implementations live outside this repo):
    - JsonExportPlugin  \u2014 writes the production as a JSON manifest
    - Mp4PlaceholderPlugin \u2014 simulates an MP4 export (real one calls ffmpeg)
    - YoutubeDraftPlugin \u2014 creates a YouTube draft via the YouTube API
    - VimeoUploadPlugin \u2014 uploads to Vimeo

The contract is intentionally minimal: name, capabilities, export(),
health_check(). The plugin owns the rest.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from src.plugins.base import PluginCapability, PluginHealth


@dataclass(frozen=True)
class ExportResult:
    """Returned by ExportFormatPlugin.export()."""

    plugin_name: str
    output_uri: str  # final file / remote URI produced
    bytes_written: int
    success: bool
    summary: dict = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.summary is None:
            object.__setattr__(self, "summary", {})


@runtime_checkable
class ExportFormatPlugin(Protocol):
    """Contract every publish-target plugin must satisfy."""

    name: str
    capabilities: frozenset[PluginCapability]

    def export(
        self,
        production: dict,
        output_path: str,
        *,
        options: dict | None = None,
    ) -> ExportResult:
        """Write the production to the target file or remote destination.

        Args:
            production:  Full production document as a dict.
            output_path: Where to write. May be a local path or a URI
                         the plugin recognises (e.g. `vimeo://draft/123`).
            options:     Plugin-specific options (e.g. `{"bitrate": 5000}`).

        Returns:
            ExportResult describing what was produced.
        """
        ...

    def estimate_size(self, production: dict) -> int:
        """Approximate output size in bytes (for budget planning)."""
        ...

    def health_check(self) -> PluginHealth:
        """Return current health. Unhealthy plugins are disabled."""
        ...


# ---------------------------------------------------------------------------
# Built-in mock implementations
# ---------------------------------------------------------------------------


class JsonExportPlugin:
    """Writes a Production dict as a JSON manifest file.

    Real publishers would extend this to fmt the manifest per a partner
    schema (e.g. YouTube's metadata API). The mock just calls `json.dumps`.
    """

    name: str = "json-export-v1"
    capabilities: frozenset[PluginCapability] = frozenset(
        {PluginCapability.LOCAL_FILE}
    )

    def export(
        self,
        production: dict,
        output_path: str,
        *,
        options: dict | None = None,
    ) -> ExportResult:
        import json as _json

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = _json.dumps(production, indent=2, ensure_ascii=False)
        path.write_text(payload, encoding="utf-8")
        return ExportResult(
            plugin_name=self.name,
            output_uri=str(path),
            bytes_written=len(payload.encode("utf-8")),
            success=True,
            summary={"format": "json", "indicators": list(production.keys())},
        )

    def estimate_size(self, production: dict) -> int:
        import json as _json

        return len(_json.dumps(production).encode("utf-8"))

    def health_check(self) -> PluginHealth:
        from datetime import datetime, timezone

        return PluginHealth(
            healthy=True,
            plugin_name=self.name,
            checked_at=datetime.now(timezone.utc).isoformat(),
        )


class Mp4PlaceholderPlugin:
    """STAND-IN for a real MP4 export plugin.

    A real implementation would shell out to ffmpeg or call a render
    service. This one writes a tiny stub file with a JSON manifest so
    downstream tools can see what would have been produced.
    """

    name: str = "mp4-placeholder-v1"
    capabilities: frozenset[PluginCapability] = frozenset(
        {PluginCapability.LOCAL_FILE}
    )

    def export(
        self,
        production: dict,
        output_path: str,
        *,
        options: dict | None = None,
    ) -> ExportResult:
        import json as _json

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        bitrate = (options or {}).get("bitrate", 5000)
        scenes = len(production.get("scenes", []))
        # Very rough: 1 MB per scene at the default bitrate
        approx_bytes = max(1, scenes) * 1024 * 1024
        stub = {
            "format": "mp4",
            "stub": True,
            "production_id": production.get("id"),
            "bitrate_kbps": bitrate,
            "scene_count": scenes,
            "approx_bytes": approx_bytes,
        }
        payload = _json.dumps(stub, indent=2)
        path.write_text(payload, encoding="utf-8")
        return ExportResult(
            plugin_name=self.name,
            output_uri=str(path),
            bytes_written=len(payload.encode("utf-8")),
            success=True,
            summary={"would_be_mp4": True, "approx_bytes": approx_bytes},
        )

    def estimate_size(self, production: dict) -> int:
        scenes = len(production.get("scenes", []))
        return max(1, scenes) * 1024 * 1024

    def health_check(self) -> PluginHealth:
        from datetime import datetime, timezone

        return PluginHealth(
            healthy=True,
            plugin_name=self.name,
            checked_at=datetime.now(timezone.utc).isoformat(),
            metrics={"note": "placeholder; no ffmpeg invoked"},
        )
