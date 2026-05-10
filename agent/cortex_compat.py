#!/usr/bin/env python3
"""
cortex_compat.py — Compatibility shim for the distillation plugin.

Bridges the old plugin API to the new unified CortexDB.

Provides:
  - get_db() → returns CortexDB instance
  - _check_duplicate() → checks for duplicate tips
  - _normalize_domain() → normalizes domain strings
  - cortex_sync module for dual-write
"""

import sys
import os
from pathlib import Path

# Ensure hermes-agent is in path for imports
_HERMES_DIR = str(Path.home() / "hermes-agent")
if _HERMES_DIR not in sys.path:
    sys.path.insert(0, _HERMES_DIR)

from agent.cortex_access import CortexDB, cortex_cursor

# Singleton instance
_db_instance = None

def get_db():
    """Get or create CortexDB singleton."""
    global _db_instance
    if _db_instance is None:
        _db_instance = CortexDB()
    return _db_instance


def _check_duplicate(condition: str, recommendation: str, domain: str = "general") -> str:
    """Check if a tip already exists. Returns existing ID or None."""
    try:
        db = get_db()
        # Search for similar text
        results = db.search_text(recommendation, node_type="tip", limit=5)
        for r in results:
            existing_text = r.get("text", "")
            # Simple similarity check
            if len(existing_text) > 10 and len(recommendation) > 10:
                # Check if they're very similar (80%+ overlap)
                existing_words = set(existing_text.lower().split())
                new_words = set(recommendation.lower().split())
                if existing_words and new_words:
                    overlap = len(existing_words & new_words) / max(len(existing_words), len(new_words))
                    if overlap > 0.7:
                        return str(r.get("id", ""))
        return None
    except Exception:
        return None


def _normalize_domain(domain: str) -> str:
    """Normalize domain string."""
    domain_map = {
        "tool_usage": "tool_use",
        "terminal": "terminal",
        "browser": "browser",
        "api": "api",
        "database": "database",
        "deployment": "deployment",
        "memory": "memory",
        "research": "research",
        "training": "training",
        "meta": "meta",
        "skill": "skill",
        "general": "general",
    }
    return domain_map.get(domain.lower(), domain.lower())


# Dual-write helper for the plugin
def sync_tip(tip_data: dict) -> bool:
    """Sync a tip to Cortex. Called by the distillation plugin."""
    try:
        db = get_db()
        
        # Check for duplicates
        existing_id = _check_duplicate(
            condition=tip_data.get("condition", ""),
            recommendation=tip_data.get("recommendation", ""),
            domain=tip_data.get("domain", "general")
        )
        if existing_id:
            return False
        
        # Build full text
        condition = tip_data.get("condition", "")
        recommendation = tip_data.get("recommendation", "")
        if condition and recommendation:
            full_text = f"{condition} {recommendation}"
        else:
            full_text = recommendation or condition or ""
        
        # Insert into Cortex
        node_id = db.insert_node(
            text=full_text,
            node_type="tip",
            domain=_normalize_domain(tip_data.get("domain", "general")),
            confidence=tip_data.get("confidence", 0.5),
            tip_type=tip_data.get("tip_type", "heuristic"),
            condition=condition,
            recommendation=recommendation,
            rationale=tip_data.get("rationale", ""),
            tool_name=tip_data.get("tool_name", ""),
            provenance="distillation_plugin",
            metadata={
                "source": "post_tool_call",
                "tip_type": tip_data.get("tip_type", "heuristic"),
            }
        )
        
        return node_id is not None
    except Exception as e:
        # Silently fail - plugin should not crash
        return False


# Backward compatibility: cortex_sync module
cortex_sync = sys.modules[__name__]
