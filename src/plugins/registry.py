"""PluginRegistry \u2014 central lookup, health-check, and capability matching.

The registry owns one PluginRegistry instance per process. Plugins are
registered under a PluginCategory and looked up by name or capability.

Semantics (per open-production-plan.md \u00a717):
    - A plugin that fails its health_check() is *automatically disabled*.
    - The kernel continues with remaining healthy plugins.
    - Users are notified of any disabled plugins (via disabled_plugins()).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from src.plugins.base import (
    CATEGORY_CAPABILITIES,
    PluginCapability,
    PluginCategory,
    PluginHealth,
)


class PluginNotFound(LookupError):
    """Raised when a requested plugin name is not registered."""


class DuplicatePluginRegistration(ValueError):
    """Raised when the same name is registered twice in one category."""


class CapabilityMismatch(ValueError):
    """Raised when a plugin's declared capabilities don't fit its category."""


@dataclass
class PluginRegistration:
    """Internal record for one registered plugin."""

    plugin: object
    category: PluginCategory
    capabilities: frozenset[PluginCapability]
    healthy: bool = True
    last_health: PluginHealth | None = None


class PluginRegistry:
    """Holds registered plugins, runs health checks, supports lookup.

    Usage:
        reg = PluginRegistry()
        reg.register(MockGenerationPlugin())
        reg.register(JsonExportPlugin())
        reg.health_check_all()

        plugin = reg.get(PluginCategory.GENERATION, "mock-generation-v1")
        video_plugins = reg.by_capability(PluginCategory.GENERATION,
                                          PluginCapability.VIDEO)
        disabled = reg.disabled_plugins()
    """

    def __init__(self) -> None:
        self._by_category: dict[PluginCategory, dict[str, PluginRegistration]] = {
            cat: {} for cat in PluginCategory
        }

    # ------------------------------------------------------------------ register
    def register(self, plugin) -> None:
        """Register a plugin. The plugin's category is read from its
        declared attribute (or inferred by protocol).

        Raises:
            DuplicatePluginRegistration: same name registered twice
            CapabilityMismatch: capabilities don't match the category
        """
        category, name, capabilities = _inspect(plugin)
        bucket = self._by_category[category]
        if name in bucket:
            raise DuplicatePluginRegistration(
                f"plugin {name!r} already registered in {category.value}"
            )
        allowed = CATEGORY_CAPABILITIES[category]
        invalid = capabilities - allowed
        if invalid:
            raise CapabilityMismatch(
                f"plugin {name!r} declared capabilities {invalid} "
                f"that don't fit {category.value}; allowed: {allowed}"
            )
        bucket[name] = PluginRegistration(
            plugin=plugin,
            category=category,
            capabilities=capabilities,
            healthy=True,
        )

    # ------------------------------------------------------------------ lookup
    def get(self, category: PluginCategory, name: str):
        """Return a healthy plugin by name. Raises PluginNotFound."""
        reg = self._by_category[category].get(name)
        if reg is None:
            raise PluginNotFound(
                f"no plugin named {name!r} in category {category.value}"
            )
        if not reg.healthy:
            raise PluginNotFound(
                f"plugin {name!r} in {category.value} is disabled "
                f"(last health: {reg.last_health.reason if reg.last_health else ''})"
            )
        return reg.plugin

    def try_get(self, category: PluginCategory, name: str):
        """Return a plugin by name, or None if missing / disabled."""
        try:
            return self.get(category, name)
        except PluginNotFound:
            return None

    def list(self, category: PluginCategory) -> list[str]:
        """Names of all registered plugins in a category (incl. disabled)."""
        return sorted(self._by_category[category].keys())

    def by_capability(
        self,
        category: PluginCategory,
        capability: PluginCapability,
    ) -> list:
        """Healthy plugins in a category that advertise `capability`."""
        return [
            r.plugin
            for r in self._by_category[category].values()
            if r.healthy and capability in r.capabilities
        ]

    def all_plugins(self, category: PluginCategory) -> list:
        """All registered plugins in a category (healthy + disabled)."""
        return list(self._by_category[category].values())

    # ------------------------------------------------------------------ health
    def health_check(self, category: PluginCategory, name: str) -> PluginHealth:
        """Run health_check() on one plugin and update its state."""
        reg = self._by_category[category].get(name)
        if reg is None:
            raise PluginNotFound(
                f"no plugin named {name!r} in category {category.value}"
            )
        health: PluginHealth = reg.plugin.health_check()
        reg.last_health = health
        reg.healthy = health.healthy
        return health

    def health_check_all(self) -> dict[PluginCategory, list[PluginHealth]]:
        """Run health_check() on every registered plugin.

        Returns a dict of per-category health results. Disabled plugins
        (healthy=False) stay disabled until re-registered.
        """
        out: dict[PluginCategory, list[PluginHealth]] = {
            cat: [] for cat in PluginCategory
        }
        for cat, bucket in self._by_category.items():
            for reg in bucket.values():
                health = reg.plugin.health_check()
                reg.last_health = health
                reg.healthy = health.healthy
                out[cat].append(health)
        return out

    def disable(self, category: PluginCategory, name: str) -> None:
        """Manually disable a plugin (e.g. for testing fallback paths)."""
        reg = self._by_category[category].get(name)
        if reg is None:
            raise PluginNotFound(
                f"no plugin named {name!r} in category {category.value}"
            )
        reg.healthy = False

    def re_enable(self, category: PluginCategory, name: str) -> None:
        """Re-enable a previously-disabled plugin (after a fresh health check)."""
        self.health_check(category, name)

    def disabled_plugins(self) -> list[tuple[PluginCategory, str, str]]:
        """Return a list of (category, name, reason) for every disabled plugin."""
        out: list[tuple[PluginCategory, str, str]] = []
        for cat, bucket in self._by_category.items():
            for name, reg in bucket.items():
                if not reg.healthy:
                    reason = reg.last_health.reason if reg.last_health else ""
                    out.append((cat, name, reason))
        return out

    def clear(self) -> None:
        """Remove all registrations. Mainly for testing."""
        self._by_category = {cat: {} for cat in PluginCategory}


# ---------------------------------------------------------------------------
# Plugin introspection
# ---------------------------------------------------------------------------

# Per-protocol mapping used to infer a plugin's category from its class.
_PROTOCOL_CATEGORY: list[tuple[type, PluginCategory]] = []


def _register_protocol_category(protocol: type, category: PluginCategory) -> None:
    """Test helper / init hook: record which Protocol maps to which category."""
    _PROTOCOL_CATEGORY.append((protocol, category))


def _inspect(plugin) -> tuple[PluginCategory, str, frozenset[PluginCapability]]:
    """Read category / name / capabilities off a plugin object.

    Resolution order:
      1. Explicit `plugin.plugin_category` attribute (rare; for tests).
      2. `isinstance` against the four Protocol types.
      3. Attribute presence on the plugin itself.
    """
    from src.plugins.generation import GenerationPlugin
    from src.plugins.export_format import ExportFormatPlugin
    from src.plugins.asset_type import AssetTypePlugin
    from src.plugins.agent_role import AgentRolePlugin

    cat = getattr(plugin, "plugin_category", None)
    if isinstance(cat, PluginCategory):
        category = cat
    elif isinstance(plugin, GenerationPlugin):
        category = PluginCategory.GENERATION
    elif isinstance(plugin, ExportFormatPlugin):
        category = PluginCategory.EXPORT_FORMAT
    elif isinstance(plugin, AssetTypePlugin):
        category = PluginCategory.ASSET_TYPE
    elif isinstance(plugin, AgentRolePlugin):
        category = PluginCategory.AGENT_ROLE
    else:
        raise CapabilityMismatch(
            f"plugin {type(plugin).__name__} does not implement any known "
            "Plugin protocol; cannot determine category"
        )

    # Name resolution differs slightly per category.
    if category is PluginCategory.AGENT_ROLE:
        name = getattr(plugin, "role_name", None) or getattr(plugin, "name", None)
    else:
        name = getattr(plugin, "name", None)

    if not name:
        raise CapabilityMismatch(
            f"plugin {type(plugin).__name__} has no name (or role_name) attribute"
        )

    caps = getattr(plugin, "capabilities", frozenset())
    if not isinstance(caps, frozenset):
        caps = frozenset(caps)
    return category, name, caps
