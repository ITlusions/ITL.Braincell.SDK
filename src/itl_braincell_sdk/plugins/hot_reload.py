"""Hot reload system for plugins and cells.

Allows reloading installed plugins and cells without restarting the server.
Exposed as FastAPI endpoints via optional middleware.
"""
from __future__ import annotations

import importlib
import logging
import sys
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class HotReloadManager:
    """Manages hot reloading of plugins and cells at runtime."""
    
    def __init__(self):
        self.reload_count = 0
        self.last_reloaded: Dict[str, float] = {}
    
    def reload_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Reload a single plugin by name.
        
        Args:
            plugin_name: Name of the plugin (e.g., "security", "architecture")
        
        Returns:
            Status dictionary with success flag and details
        """
        try:
            logger.info(f"Hot reloading plugin: {plugin_name}")
            
            # Import the plugin module
            module_name = f"itl_braincell_cells_{plugin_name.lower()}"
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
            
            # Re-discover cells to pick up changes
            from itl_braincell_sdk.cells import discover_cells
            cells = discover_cells(include_plugins=True)
            plugin_cells = [c for c in cells if c.name.startswith(plugin_name)]
            
            self.reload_count += 1
            try:
                self.last_reloaded[plugin_name] = importlib.metadata.version("itl-braincell-sdk")
            except:
                pass
            
            return {
                "success": True,
                "plugin": plugin_name,
                "cells_discovered": len(plugin_cells),
                "cells": [c.name for c in plugin_cells],
                "message": f"Reloaded plugin '{plugin_name}' with {len(plugin_cells)} cells"
            }
        except Exception as e:
            logger.error(f"Failed to reload plugin '{plugin_name}': {e}")
            return {
                "success": False,
                "plugin": plugin_name,
                "error": str(e),
                "message": f"Failed to reload plugin '{plugin_name}'"
            }
    
    def reload_all_plugins(self) -> Dict[str, Any]:
        """Reload all installed plugins.
        
        Returns:
            Status dictionary with results for each plugin
        """
        logger.info("Hot reloading all plugins...")
        
        from itl_braincell_sdk.cells import discover_cell_plugins
        plugins = discover_cell_plugins()
        
        results = {
            "success": True,
            "total_plugins": len(plugins),
            "plugins": {}
        }
        
        for plugin in plugins:
            result = self.reload_plugin(plugin.name)
            results["plugins"][plugin.name] = result
            if not result["success"]:
                results["success"] = False
        
        self.reload_count += 1
        return results
    
    def reload_cells(self) -> Dict[str, Any]:
        """Reload all cell modules.
        
        Returns:
            Status dictionary with discovery results
        """
        try:
            logger.info("Hot reloading all cells...")
            
            # Reload the cells module to re-discover
            import itl_braincell_sdk.cells
            importlib.reload(itl_braincell_sdk.cells)
            
            from itl_braincell_sdk.cells import discover_cells
            cells = discover_cells(include_plugins=True)
            
            self.reload_count += 1
            
            return {
                "success": True,
                "cells_discovered": len(cells),
                "cells": [c.name for c in cells],
                "message": f"Discovered {len(cells)} cells"
            }
        except Exception as e:
            logger.error(f"Failed to reload cells: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to reload cells"
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current reload manager status.
        
        Returns:
            Status dictionary with statistics
        """
        from itl_braincell_sdk.cells import discover_cells, discover_cell_plugins
        
        cells = discover_cells(include_plugins=True)
        plugins = discover_cell_plugins()
        
        return {
            "reload_count": self.reload_count,
            "total_cells": len(cells),
            "total_plugins": len(plugins),
            "cells": [c.name for c in cells],
            "plugins": [p.name for p in plugins],
            "last_reloaded": self.last_reloaded,
        }


# Global manager instance
_hot_reload_manager: HotReloadManager | None = None


def get_hot_reload_manager() -> HotReloadManager:
    """Get or create the global hot reload manager."""
    global _hot_reload_manager
    if _hot_reload_manager is None:
        _hot_reload_manager = HotReloadManager()
    return _hot_reload_manager


def setup_hot_reload_endpoints(app: Any) -> None:
    """Setup hot reload API endpoints on FastAPI app.
    
    Requires FastAPI. Call this during app initialization.
    
    Args:
        app: FastAPI application instance
    
    Example:
        from fastapi import FastAPI
        from itl_braincell_sdk.plugins.hot_reload import setup_hot_reload_endpoints
        
        app = FastAPI()
        setup_hot_reload_endpoints(app)
        # Exposes POST /api/admin/hot-reload/* endpoints
    """
    try:
        from fastapi import HTTPException
    except ImportError:
        logger.warning("FastAPI not available, hot reload endpoints not registered")
        return
    
    manager = get_hot_reload_manager()
    
    @app.post("/api/admin/hot-reload/plugins/{plugin_name}")
    async def reload_plugin_endpoint(plugin_name: str):
        """Reload a specific plugin.
        
        Example:
            POST /api/admin/hot-reload/plugins/security
        """
        result = manager.reload_plugin(plugin_name)
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    
    @app.post("/api/admin/hot-reload/plugins")
    async def reload_all_plugins_endpoint():
        """Reload all plugins.
        
        Example:
            POST /api/admin/hot-reload/plugins
        """
        result = manager.reload_all_plugins()
        if not result["success"]:
            raise HTTPException(status_code=500, detail="Some plugins failed to reload")
        return result
    
    @app.post("/api/admin/hot-reload/cells")
    async def reload_cells_endpoint():
        """Reload all cells.
        
        Example:
            POST /api/admin/hot-reload/cells
        """
        result = manager.reload_cells()
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    
    @app.get("/api/admin/hot-reload/status")
    async def reload_status_endpoint():
        """Get hot reload manager status.
        
        Example:
            GET /api/admin/hot-reload/status
        """
        return manager.get_status()
    
    logger.info("Hot reload endpoints registered at /api/admin/hot-reload/*")


__all__ = [
    "HotReloadManager",
    "get_hot_reload_manager",
    "setup_hot_reload_endpoints",
]
