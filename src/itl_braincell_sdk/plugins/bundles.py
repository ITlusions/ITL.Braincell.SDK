"""Plugin bundle/composition system for grouping related plugins.

Bundles allow shipping collections of plugins together as a single package.
Example: "security-ops-platform" = security + operations + architecture plugins.
"""
from __future__ import annotations

import logging
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PluginBundle:
    """A named collection of plugins that work together."""
    
    name: str
    description: str = ""
    version: str = "0.1.0"
    plugins: List[str] = None  # List of plugin package names to install
    
    def __post_init__(self):
        if self.plugins is None:
            self.plugins = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Export bundle as dictionary for configuration files."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "plugins": self.plugins,
        }
    
    def to_yaml(self) -> str:
        """Export bundle as YAML."""
        import yaml
        return yaml.dump(self.to_dict(), default_flow_style=False)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> PluginBundle:
        """Load bundle from dictionary."""
        return PluginBundle(
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=data.get("version", "0.1.0"),
            plugins=data.get("plugins", []),
        )
    
    @staticmethod
    def from_yaml(yaml_str: str) -> PluginBundle:
        """Load bundle from YAML string."""
        import yaml
        data = yaml.safe_load(yaml_str)
        return PluginBundle.from_dict(data)


# Pre-defined bundles
BUNDLES = {
    "security-ops": PluginBundle(
        name="security-ops",
        description="Security & Operations platform: threat intelligence, incidents, tasks, architecture",
        version="0.1.0",
        plugins=[
            "itl-braincell-cells-security",
            "itl-braincell-cells-operations",
            "itl-braincell-cells-architecture",
        ],
    ),
    "full-stack": PluginBundle(
        name="full-stack",
        description="Complete BrainCell platform with all plugins",
        version="0.1.0",
        plugins=[
            "itl-braincell-cells-security",
            "itl-braincell-cells-architecture",
            "itl-braincell-cells-codebase",
            "itl-braincell-cells-operations",
        ],
    ),
    "codebase-intel": PluginBundle(
        name="codebase-intel",
        description="Codebase intelligence: dependencies, versions, errors, research",
        version="0.1.0",
        plugins=[
            "itl-braincell-cells-codebase",
            "itl-braincell-cells-architecture",
        ],
    ),
}


def get_bundle(name: str) -> PluginBundle | None:
    """Get a pre-defined bundle by name."""
    return BUNDLES.get(name)


def list_bundles() -> Dict[str, PluginBundle]:
    """List all available bundles."""
    return BUNDLES.copy()


def install_bundle(name: str, dry_run: bool = False) -> bool:
    """Install a plugin bundle.
    
    Args:
        name: Bundle name
        dry_run: If True, only print what would be installed
    
    Returns:
        True if successful, False otherwise
    """
    bundle = get_bundle(name)
    if not bundle:
        logger.error(f"Unknown bundle: {name}")
        return False
    
    import subprocess
    import sys
    
    logger.info(f"Installing bundle '{name}' ({bundle.description})")
    logger.info(f"Plugins to install: {', '.join(bundle.plugins)}")
    
    if dry_run:
        logger.info("[DRY RUN] Would install plugins above")
        return True
    
    try:
        cmd = [sys.executable, "-m", "pip", "install", "-e"] + bundle.plugins
        logger.debug(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"✓ Bundle '{name}' installed successfully")
        logger.debug(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install bundle '{name}':")
        logger.error(e.stderr)
        return False
    except Exception as e:
        logger.error(f"Unexpected error installing bundle '{name}': {e}")
        return False


__all__ = [
    "PluginBundle",
    "BUNDLES",
    "get_bundle",
    "list_bundles",
    "install_bundle",
]
