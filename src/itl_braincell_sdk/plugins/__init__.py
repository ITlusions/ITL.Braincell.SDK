"""BrainCell Plugin System - Infrastructure for extending with external plugins.

This module provides the core abstractions and utilities for plugin management:
- Plugin base classes and lifecycle hooks
- Plugin bundling and composition
- Hot reload system for runtime updates
- Configuration management
- Dependency validation
"""

from .base import (
    CELL_PLUGIN_ENTRY_POINT_GROUP,
    PLUGIN_CONFIG_ENTRY_POINT_GROUP,
    CellCollectionPlugin,
    PluginConfig,
    PluginMetadata,
)
from .bundles import (
    PluginBundle,
    BUNDLES,
    get_bundle,
    list_bundles,
    install_bundle,
)
from .hot_reload import (
    HotReloadManager,
    get_hot_reload_manager,
    setup_hot_reload_endpoints,
)

__all__ = [
    # Base abstractions
    "CELL_PLUGIN_ENTRY_POINT_GROUP",
    "PLUGIN_CONFIG_ENTRY_POINT_GROUP",
    "CellCollectionPlugin",
    "PluginConfig",
    "PluginMetadata",
    # Bundling
    "PluginBundle",
    "BUNDLES",
    "get_bundle",
    "list_bundles",
    "install_bundle",
    # Hot reload
    "HotReloadManager",
    "get_hot_reload_manager",
    "setup_hot_reload_endpoints",
]
