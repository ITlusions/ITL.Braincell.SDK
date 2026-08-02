"""Cell collection plugin abstractions.

External packages can expose installable collections of cells by publishing an
entry point in the ``itl_braincell_sdk.cell_plugins`` group.

Plugin Features:
- Lifecycle hooks (on_install, on_uninstall, health_check)
- Configuration management (environment-driven settings)
- Dependency management (plugin-to-plugin dependencies)
- Namespacing (optional table prefix)
- Metrics collection
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List

from pydantic import BaseModel

from itl_braincell_sdk.cells.base import MemoryCell

logger = logging.getLogger(__name__)

CELL_PLUGIN_ENTRY_POINT_GROUP = "itl_braincell_sdk.cell_plugins"
PLUGIN_CONFIG_ENTRY_POINT_GROUP = "itl_braincell_sdk.plugin_configs"


class PluginConfig(BaseModel):
    """Base configuration class for plugins.
    
    Plugins can subclass this to define their own settings.
    Configuration is environment-driven via Pydantic BaseSettings.
    """
    
    class Config:
        """Allow extra fields for flexibility"""
        extra = "allow"


class PluginMetadata(BaseModel):
    """Plugin metadata for compatibility and versioning."""
    
    name: str
    version: str = "0.1.0"
    api_version: str = "1.0"  # Breaking changes = major version bump
    namespace: Optional[str] = None  # Table prefix (e.g., "security_", "ops_")
    requires_plugins: List[str] = []  # Names of required plugins


class CellCollectionPlugin(ABC):
    """Base class for installable collections of BrainCell cells.
    
    Supports lifecycle hooks, configuration, dependencies, and metrics.
    
    Example:
        class SecurityPlugin(CellCollectionPlugin):
            @property
            def metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="security",
                    version="0.1.0",
                    requires_plugins=["architecture"],
                )
            
            async def on_install(self):
                logger.info("Initializing security plugin...")
            
            async def health_check(self) -> bool:
                return True
    """

    @property
    def name(self) -> str:
        """Plugin name (defaults to class name)"""
        return self.__class__.__name__

    @property
    def description(self) -> str:
        """Human-readable plugin description"""
        return ""

    @property
    def metadata(self) -> PluginMetadata:
        """Plugin metadata including version and dependencies.
        
        Override to customize.
        """
        return PluginMetadata(name=self.name)

    @property
    def config_class(self) -> type[PluginConfig] | None:
        """Optional configuration class for this plugin.
        
        If provided, settings are loaded from environment variables.
        
        Example:
            class SecurityConfig(PluginConfig):
                threat_alert_threshold: int = 7
                max_iocs_per_report: int = 1000
                
                class Config:
                    env_prefix = "BRAINCELL_SECURITY_"
        """
        return None

    def get_config(self) -> PluginConfig | None:
        """Get instantiated config from environment.
        
        Returns None if config_class is not defined.
        """
        if self.config_class is None:
            return None
        try:
            return self.config_class()
        except Exception as e:
            logger.warning(f"Failed to load config for plugin {self.name}: {e}")
            return None

    @abstractmethod
    def get_cells(self) -> list[MemoryCell]:
        """Return the cell instances provided by this plugin."""

    async def on_install(self) -> None:
        """Called when plugin is first installed or initialized.
        
        Use for:
        - Initializing external resources (APIs, databases)
        - Registering webhooks
        - Seeding default data
        
        Override to customize.
        """
        pass

    async def on_uninstall(self) -> None:
        """Called when plugin is being removed or shut down.
        
        Use for:
        - Cleaning up resources
        - Unregistering webhooks
        - Archiving data
        
        Override to customize.
        """
        pass

    async def health_check(self) -> bool:
        """Check if plugin is healthy and all dependencies are available.
        
        Returns:
            True if healthy, False otherwise.
        
        Override to customize (default is True).
        """
        return True

    async def get_metrics(self) -> Dict[str, Any]:
        """Return plugin metrics for monitoring.
        
        Example:
            return {
                "total_threats": await self.count_threats(),
                "active_incidents": await self.count_active_incidents(),
                "last_sync": await self.get_last_sync_time(),
            }
        
        Returns:
            Dictionary of metric name -> value. Exposed as /api/metrics/<plugin>.
        
        Override to customize.
        """
        return {}

    def validate_dependencies(self, installed_plugins: List[str]) -> bool:
        """Validate that all required plugins are installed.
        
        Args:
            installed_plugins: List of installed plugin names
        
        Returns:
            True if all dependencies met, False otherwise
        """
        missing = set(self.metadata.requires_plugins) - set(installed_plugins)
        if missing:
            logger.error(
                f"Plugin {self.name} has missing dependencies: {', '.join(missing)}"
            )
            return False
        return True


__all__ = [
    "CELL_PLUGIN_ENTRY_POINT_GROUP",
    "PLUGIN_CONFIG_ENTRY_POINT_GROUP",
    "CellCollectionPlugin",
    "PluginConfig",
    "PluginMetadata",
]
