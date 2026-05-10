"""
Subconscious Plugin Loader for Hermes Agent

Loads all cognitive systems from agent/ as Hermes plugins.
This bridges the external subconscious modules into the Hermes agent loop.
"""

import logging
import os
import sys
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

SUBCONSCIOUS_DIR = Path.home() / "hermes-agent"

class SubconsciousPlugin:
    """Plugin wrapper for subconscious cognitive systems."""
    
    def __init__(self, name: str, module_path: Path):
        self.name = name
        self.module_path = module_path
        self.module = None
        self.loaded = False
        self.error = None
        
    def load(self) -> bool:
        """Load the subconscious module."""
        try:
            spec = importlib.util.spec_from_file_location(
                f"subconscious.{self.name}", 
                self.module_path
            )
            self.module = importlib.util.module_from_spec(spec)
            sys.modules[f"subconscious.{self.name}"] = self.module
            spec.loader.exec_module(self.module)
            self.loaded = True
            return True
        except Exception as e:
            self.error = str(e)
            logger.warning(f"Failed to load subconscious module {self.name}: {e}")
            return False
    
    def call(self, method: str, *args, **kwargs) -> Any:
        """Call a method on the loaded module."""
        if not self.loaded or not self.module:
            return None
        try:
            fn = getattr(self.module, method, None)
            if fn and callable(fn):
                return fn(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Failed to call {method} on {self.name}: {e}")
        return None
    
    def get_attr(self, attr: str) -> Any:
        """Get an attribute from the loaded module."""
        if not self.loaded or not self.module:
            return None
        return getattr(self.module, attr, None)


def load_all_subconscious_plugins() -> Dict[str, SubconsciousPlugin]:
    """Load all subconscious modules as plugins."""
    plugins = {}
    
    if not SUBCONSCIOUS_DIR.exists():
        logger.warning(f"Subconscious directory not found: {SUBCONSCIOUS_DIR}")
        return plugins
    
    for py_file in sorted(SUBCONSCIOUS_DIR.glob("*.py")):
        if py_file.name.startswith("__"):
            continue
            
        name = py_file.stem
        plugin = SubconsciousPlugin(name, py_file)
        if plugin.load():
            plugins[name] = plugin
            logger.info(f"Loaded subconscious plugin: {name}")
        else:
            logger.warning(f"Failed to load subconscious plugin: {name} ({plugin.error})")
    
    return plugins

# Global plugin registry
_subconscious_plugins: Dict[str, SubconsciousPlugin] = {}

def get_subconscious_plugin(name: str) -> Optional[SubconsciousPlugin]:
    """Get a loaded subconscious plugin by name."""
    return _subconscious_plugins.get(name)

def list_subconscious_plugins() -> List[str]:
    """List all loaded subconscious plugin names."""
    return list(_subconscious_plugins.keys())

def init_subconscious_plugins() -> Dict[str, SubconsciousPlugin]:
    """Initialize all subconscious plugins. Call once at startup."""
    global _subconscious_plugins
    _subconscious_plugins = load_all_subconscious_plugins()
    logger.info(f"Subconscious plugin system loaded: {len(_subconscious_plugins)} modules")
    return _subconscious_plugins

# Auto-init on import
init_subconscious_plugins()
