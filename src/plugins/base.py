"""Plugin base types — shared across all four plugin surfaces.

Per open-production-plan.md \u00a717, plugins extend one of four surfaces:

    1. Generation backends   (GenerationPlugin)
    2. Export formats        (ExportFormatPlugin)
    3. Asset types           (AssetTypePlugin)
    4. Agent roles           (AgentRolePlugin)

This module is the common vocabulary: capabilities, categories,
health-check semantics, and a tiny PluginHealth dataclass.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class PluginCategory(str, Enum):
    """Which of the four plugin surfaces a plugin belongs to."""

    GENERATION = "generation"
    EXPORT_FORMAT = "export_format"
    ASSET_TYPE = "asset_type"
    AGENT_ROLE = "agent_role"


class PluginCapability(str, Enum):
    """Coarse-grained capability flags a plugin advertises.

    Plugins declare which of these they support. The kernel uses these
    to decide whether a plugin is suitable for a given shot / format.
    """

    # Generation capabilities
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    TEXT = "text"
    # Export capabilities
    LOCAL_FILE = "local_file"
    REMOTE_TARGET = "remote_target"
    # Asset capabilities
    CONTENT_ADDRESSED = "content_addressed"
    BINARY = "binary"
    TEXTUAL = "textual"
    # Agent capabilities
    BLOCKING_REVIEW = "blocking_review"
    ADVISORY = "advisory"


@dataclass
class PluginHealth:
    """Result of a plugin health check.

    A plugin that fails its health check is automatically disabled by
    the registry. The kernel falls back to remaining healthy plugins.
    """

    healthy: bool
    plugin_name: str
    checked_at: str  # ISO-8601 UTC
    reason: str = ""
    metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "healthy": self.healthy,
            "plugin_name": self.plugin_name,
            "checked_at": self.checked_at,
            "reason": self.reason,
            "metrics": dict(self.metrics),
        }


# Allowable capability sets per category (used by registry validation)
CATEGORY_CAPABILITIES: dict[PluginCategory, set[PluginCapability]] = {
    PluginCategory.GENERATION: {
        PluginCapability.VIDEO,
        PluginCapability.IMAGE,
        PluginCapability.AUDIO,
        PluginCapability.TEXT,
    },
    PluginCategory.EXPORT_FORMAT: {
        PluginCapability.LOCAL_FILE,
        PluginCapability.REMOTE_TARGET,
    },
    PluginCategory.ASSET_TYPE: {
        PluginCapability.CONTENT_ADDRESSED,
        PluginCapability.BINARY,
        PluginCapability.TEXTUAL,
    },
    PluginCategory.AGENT_ROLE: {
        PluginCapability.BLOCKING_REVIEW,
        PluginCapability.ADVISORY,
    },
}
