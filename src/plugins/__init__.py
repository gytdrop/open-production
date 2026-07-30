"""Plugin subsystem \u2014 four plugin surfaces + central registry.

Public API
----------
    Base types
        PluginCategory       \u2014 enum: GENERATION | EXPORT_FORMAT | ASSET_TYPE | AGENT_ROLE
        PluginCapability     \u2014 enum of capability flags
        PluginHealth         \u2014 health-check result dataclass

    Protocols (and built-in mock implementations)
        GenerationPlugin / MockGenerationPlugin / CostEstimate
        ExportFormatPlugin / JsonExportPlugin / Mp4PlaceholderPlugin / ExportResult
        AssetTypePlugin / ImageAssetType / VideoAssetType / AudioAssetType /
                         DocumentAssetType / AssetValidationResult
        AgentRolePlugin / CustomReviewerRole / ComplianceReviewerRole /
                         AgentRoleResult

    Registry
        PluginRegistry             \u2014 central lookup + health-check
        PluginNotFound
        DuplicatePluginRegistration
        CapabilityMismatch
"""
from __future__ import annotations

from src.plugins.base import (
    PluginCapability,
    PluginCategory,
    PluginHealth,
    CATEGORY_CAPABILITIES,
)
from src.plugins.generation import (
    GenerationPlugin,
    MockGenerationPlugin,
    CostEstimate,
)
from src.plugins.export_format import (
    ExportFormatPlugin,
    ExportResult,
    JsonExportPlugin,
    Mp4PlaceholderPlugin,
)
from src.plugins.asset_type import (
    AssetTypePlugin,
    AssetValidationResult,
    ImageAssetType,
    VideoAssetType,
    AudioAssetType,
    DocumentAssetType,
)
from src.plugins.agent_role import (
    AgentRolePlugin,
    AgentRoleResult,
    CustomReviewerRole,
    ComplianceReviewerRole,
)
from src.plugins.registry import (
    PluginRegistry,
    PluginRegistration,
    PluginNotFound,
    DuplicatePluginRegistration,
    CapabilityMismatch,
)

__all__ = [
    # base
    "PluginCategory", "PluginCapability", "PluginHealth", "CATEGORY_CAPABILITIES",
    # generation
    "GenerationPlugin", "MockGenerationPlugin", "CostEstimate",
    # export
    "ExportFormatPlugin", "ExportResult",
    "JsonExportPlugin", "Mp4PlaceholderPlugin",
    # asset type
    "AssetTypePlugin", "AssetValidationResult",
    "ImageAssetType", "VideoAssetType", "AudioAssetType", "DocumentAssetType",
    # agent role
    "AgentRolePlugin", "AgentRoleResult",
    "CustomReviewerRole", "ComplianceReviewerRole",
    # registry
    "PluginRegistry", "PluginRegistration",
    "PluginNotFound", "DuplicatePluginRegistration", "CapabilityMismatch",
]
