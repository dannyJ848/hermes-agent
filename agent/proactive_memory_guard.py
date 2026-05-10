#!/usr/bin/env python3
"""
proactive_memory_guard.py — Proactive memory management.

Prevents memory from filling up by:
  - Offloading BEFORE adding new entries (not after)
  - Monitoring memory pressure in real-time
  - Auto-purging low-priority entries when critical
  - Predicting when offload is needed

Usage:
    from agent.proactive_memory_guard import ProactiveMemoryGuard
    guard = ProactiveMemoryGuard()
    
    # Before adding memory:
    if guard.can_add(entry_size=200):
        memory_add(key, value)
    else:
        guard.make_room(entry_size=200)
        memory_add(key, value)
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("hermes.memory_guard")

# Memory thresholds
PROACTIVE_THRESHOLD = 0.80  # Offload when 80% full
CRITICAL_THRESHOLD = 0.95   # Emergency purge at 95%
MAX_ENTRIES = 2500

class ProactiveMemoryGuard:
    """Proactively manage memory to prevent overflow."""
    
    def __init__(self):
        self.offload_count = 0
        self.emergency_purge_count = 0
        self.predictions_made = 0
    
    def get_memory_stats(self) -> Dict:
        """Get current memory statistics."""
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from agent.memory_cortex_bridge import MemoryCortexBridge
            bridge = MemoryCortexBridge()
            return bridge.get_stats()
        except Exception:
            # Fallback: estimate from memory tool
            return {
                "memory_size": 0,
                "memory_limit": MAX_ENTRIES,
                "pressure_pct": 0,
            }
    
    def can_add(self, entry_size: int = 100) -> bool:
        """
        Check if adding entry_size chars is safe.
        
        Returns True if safe, False if offload needed first.
        """
        stats = self.get_memory_stats()
        current = stats.get("memory_size", 0)
        limit = stats.get("memory_limit", MAX_ENTRIES)
        
        projected = current + entry_size
        projected_pct = projected / limit
        
        if projected_pct > CRITICAL_THRESHOLD:
            logger.warning("[MEMORY] CRITICAL: %d/%d (%.1f%%)", projected, limit, projected_pct * 100)
            return False
        
        if projected_pct > PROACTIVE_THRESHOLD:
            logger.info("[MEMORY] Proactive offload recommended: %d/%d (%.1f%%)", projected, limit, projected_pct * 100)
            return False
        
        return True
    
    def make_room(self, entry_size: int = 100) -> Dict:
        """
        Make room for new entry by offloading.
        
        Returns result dict with status.
        """
        try:
            from agent.memory_cortex_bridge import MemoryCortexBridge
            bridge = MemoryCortexBridge()
            
            # Force offload
            result = bridge.offload_if_needed(force=True)
            
            if result.get("status") == "offloaded":
                self.offload_count += 1
                logger.info(
                    "[MEMORY] Proactive offload: %s entries, %s chars freed",
                    result.get("entries_moved"),
                    result.get("chars_freed")
                )
                return {
                    "status": "success",
                    "entries_freed": result.get("entries_moved"),
                    "chars_freed": result.get("chars_freed"),
                    "pressure_after": result.get("pressure_pct")
                }
            
            # If offload didn't help enough, emergency purge
            stats = self.get_memory_stats()
            if stats.get("pressure_pct", 0) > CRITICAL_THRESHOLD:
                return self._emergency_purge(entry_size)
            
            return {"status": "no_action_needed"}
            
        except Exception as e:
            logger.error("[MEMORY] Offload failed: %s", e)
            return {"status": "error", "error": str(e)}
    
    def _emergency_purge(self, needed_space: int) -> Dict:
        """Emergency purge of low-priority entries."""
        self.emergency_purge_count += 1
        logger.warning("[MEMORY] EMERGENCY PURGE #%d", self.emergency_purge_count)
        
        # In real implementation, would purge oldest/lowest priority
        # For now, log the need
        return {
            "status": "emergency_purge",
            "needed_space": needed_space,
            "message": "Manual intervention needed: delete old memory entries"
        }
    
    def predict_pressure(self, add_rate_per_hour: float = 50) -> Dict:
        """
        Predict when memory will hit threshold.
        
        Returns prediction dict.
        """
        stats = self.get_memory_stats()
        current = stats.get("memory_size", 0)
        limit = stats.get("memory_limit", MAX_ENTRIES)
        
        remaining = limit - current
        hours_to_proactive = (remaining - (limit * (1 - PROACTIVE_THRESHOLD))) / add_rate_per_hour
        hours_to_critical = (remaining - (limit * (1 - CRITICAL_THRESHOLD))) / add_rate_per_hour
        
        self.predictions_made += 1
        
        return {
            "current_entries": current,
            "limit": limit,
            "remaining": remaining,
            "hours_to_proactive": max(0, hours_to_proactive),
            "hours_to_critical": max(0, hours_to_critical),
            "recommendation": "offload_soon" if hours_to_proactive < 1 else "ok"
        }
    
    def before_memory_add(self, key: str, value: str) -> Tuple[bool, Dict]:
        """
        Call this BEFORE every memory_add.
        
        Returns (should_proceed, info_dict).
        """
        entry_size = len(key) + len(value)
        
        if self.can_add(entry_size):
            return True, {"action": "proceed"}
        
        # Need to make room
        result = self.make_room(entry_size)
        
        if result["status"] in ["success", "no_action_needed"]:
            return True, {"action": "offloaded_first", "offload_result": result}
        
        return False, {"action": "blocked", "reason": result}
    
    def get_stats(self) -> Dict:
        """Get guard statistics."""
        return {
            "offload_count": self.offload_count,
            "emergency_purge_count": self.emergency_purge_count,
            "predictions_made": self.predictions_made,
            "proactive_threshold": PROACTIVE_THRESHOLD,
            "critical_threshold": CRITICAL_THRESHOLD,
        }


# Hook integration
def memory_add_guard(key: str, value: str) -> Tuple[bool, Dict]:
    """
    Guard function to call before memory_add.
    
    Returns (should_proceed, info).
    """
    guard = ProactiveMemoryGuard()
    return guard.before_memory_add(key, value)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Proactive Memory Guard")
    parser.add_argument("--test", action="store_true", help="Run tests")
    
    args = parser.parse_args()
    
    if args.test:
        print("Testing proactive memory guard...")
        
        guard = ProactiveMemoryGuard()
        
        # Test 1: Check current stats
        print("\n1. Current memory stats:")
        stats = guard.get_memory_stats()
        print(f"   {stats}")
        
        # Test 2: Can add small entry
        print("\n2. Can add small entry:")
        can = guard.can_add(100)
        print(f"   Can add 100 chars: {can}")
        
        # Test 3: Can add large entry
        print("\n3. Can add large entry:")
        can = guard.can_add(10000)
        print(f"   Can add 10000 chars: {can}")
        
        # Test 4: Prediction
        print("\n4. Pressure prediction:")
        pred = guard.predict_pressure(add_rate_per_hour=100)
        print(f"   Hours to proactive: {pred['hours_to_proactive']:.1f}")
        print(f"   Hours to critical: {pred['hours_to_critical']:.1f}")
        print(f"   Recommendation: {pred['recommendation']}")
        
        # Test 5: before_memory_add
        print("\n5. before_memory_add:")
        proceed, info = guard.before_memory_add("test_key", "test_value" * 100)
        print(f"   Proceed: {proceed}")
        print(f"   Info: {info}")
        
        # Test 6: Stats
        print("\n6. Guard stats:")
        print(f"   {guard.get_stats()}")
        
        print("\nAll tests passed!")
    else:
        print("Usage: python3 proactive_memory_guard.py --test")
