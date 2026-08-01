"""BrainCell memory cells module

Provides automatic cell discovery and registry functionality.
"""
import pkgutil
import importlib
from pathlib import Path
from typing import List

from .base import MemoryCell


def discover_cells() -> List[MemoryCell]:
    """
    Automatically discover and load all memory cells in the cells package.
    
    Returns:
        List of MemoryCell instances
    """
    cells = []
    cells_dir = Path(__file__).parent
    
    # Iterate through all subdirectories (cell modules)
    for item in cells_dir.iterdir():
        if item.is_dir() and not item.name.startswith('_'):
            cell_module_name = item.name
            try:
                # Import the cell module
                module = importlib.import_module(f".{cell_module_name}.cell", package=__package__)
                
                # Look for 'cell' attribute (should be MemoryCell instance)
                if hasattr(module, 'cell') and isinstance(module.cell, MemoryCell):
                    cells.append(module.cell)
            except (ImportError, AttributeError) as e:
                # Silently skip cells that fail to load
                pass
    
    return cells


__all__ = ['discover_cells', 'MemoryCell']
