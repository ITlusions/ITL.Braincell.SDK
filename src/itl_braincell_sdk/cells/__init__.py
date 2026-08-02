"""BrainCell memory cells module.

Provides automatic discovery for built-in cells and installed cell collection
plugins.
"""
from __future__ import annotations

import importlib
import logging
from collections.abc import Iterable
from importlib import metadata
from pathlib import Path
from typing import List

from .base import MemoryCell
from itl_braincell_sdk.plugins import CELL_PLUGIN_ENTRY_POINT_GROUP, CellCollectionPlugin, PluginConfig, PluginMetadata

logger = logging.getLogger(__name__)


def _discover_builtin_cells() -> list[MemoryCell]:
    cells: list[MemoryCell] = []
    cells_dir = Path(__file__).parent

    for item in cells_dir.iterdir():
        if not item.is_dir() or item.name.startswith("_"):
            continue

        try:
            module = importlib.import_module(f".{item.name}.cell", package=__package__)
        except ImportError:
            continue

        cell = getattr(module, "cell", None)
        if isinstance(cell, MemoryCell):
            cells.append(cell)

    return cells


def _normalize_cells(value: object) -> list[MemoryCell]:
    if isinstance(value, MemoryCell):
        return [value]

    if isinstance(value, CellCollectionPlugin):
        return value.get_cells()

    if callable(value):
        return _normalize_cells(value())

    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict)):
        cells = list(value)
        if all(isinstance(cell, MemoryCell) for cell in cells):
            return cells

    return []


def discover_cell_plugins() -> list[CellCollectionPlugin]:
    """Load installed cell collection plugins from entry points.
    
    Validates plugin dependencies and logs warnings if required plugins are missing.
    """
    plugins: list[CellCollectionPlugin] = []
    entry_points = metadata.entry_points()
    group = entry_points.select(group=CELL_PLUGIN_ENTRY_POINT_GROUP)
    
    # First pass: load all plugins
    loaded_plugins = {}
    for entry_point in group:
        try:
            plugin_value = entry_point.load()
        except Exception as exc:  # pragma: no cover - defensive plugin isolation
            logger.warning("Failed to load cell plugin '%s': %s", entry_point.name, exc)
            continue

        normalized_cells = _normalize_cells(plugin_value)
        if normalized_cells:
            plugin = _LoadedCellPlugin(entry_point.name, normalized_cells)
            loaded_plugins[entry_point.name] = plugin
            continue

        logger.warning(
            "Entry point '%s' did not resolve to a cell collection plugin or cells",
            entry_point.name,
        )
    
    # Second pass: validate dependencies
    installed_plugin_names = list(loaded_plugins.keys())
    for plugin_name, plugin in loaded_plugins.items():
        if hasattr(plugin, 'validate_dependencies'):
            if not plugin.validate_dependencies(installed_plugin_names):
                logger.warning(
                    "Plugin '%s' has unmet dependencies, skipping",
                    plugin_name
                )
                continue
        
        plugins.append(plugin)

    return plugins


def discover_cells(include_plugins: bool = True) -> List[MemoryCell]:
    """Discover built-in cells and optionally cells from installed plugins."""
    discovered: list[MemoryCell] = []
    seen_names: set[str] = set()

    for cell in _discover_builtin_cells():
        if cell.name in seen_names:
            continue
        seen_names.add(cell.name)
        discovered.append(cell)

    if include_plugins:
        for plugin in discover_cell_plugins():
            for cell in plugin.get_cells():
                if cell.name in seen_names:
                    logger.warning(
                        "Skipping duplicate cell '%s' from plugin '%s'",
                        cell.name,
                        plugin.name,
                    )
                    continue
                seen_names.add(cell.name)
                discovered.append(cell)

    return discovered


class _LoadedCellPlugin(CellCollectionPlugin):
    def __init__(self, name: str, cells: list[MemoryCell]) -> None:
        self._name = name
        self._cells = cells

    @property
    def name(self) -> str:
        return self._name

    def get_cells(self) -> list[MemoryCell]:
        return self._cells


__all__ = [
    "CELL_PLUGIN_ENTRY_POINT_GROUP",
    "CellCollectionPlugin",
    "PluginConfig",
    "PluginMetadata",
    "discover_cell_plugins",
    "discover_cells",
    "MemoryCell",
]
