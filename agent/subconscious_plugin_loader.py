"""
Subconscious Plugin Loader — DEPRECATED

This module is kept for backward compatibility.
All cognitive systems are now registered via the Hermes plugin system
in ~/.hermes/plugins/cognitive-systems/.

The init_subconscious_plugins() function is now a no-op alias
that delegates to the proper plugin registration.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Legacy no-op — cognitive systems now load via Hermes plugin system
def init_subconscious_plugins() -> None:
    """
    DEPRECATED: Cognitive systems now auto-load via Hermes plugin discovery.
    This function is a no-op for backward compatibility.
    """
    logger.debug("init_subconscious_plugins() is deprecated — cognitive systems load via plugin system")
    pass

# Keep old aliases for compatibility
get_subconscious_plugin = lambda name: None
list_subconscious_plugins = lambda: []

__all__ = ["init_subconscious_plugins", "get_subconscious_plugin", "list_subconscious_plugins"]
