#!/usr/bin/env python3
"""
memory_cortex_bridge.py — Auto-offload bridge from Hermes memory to CortexDB.

Triggered when memory tool approaches 2,500 char limit.
Flow:
  1. Detect memory pressure (>2,400 chars or >95%)
  2. Score entries by: priority (low first), age (old first), access count (low first)
  3. Select bottom N entries for offload
  4. Insert into CortexDB memory_units table
  5. Remove from active MEMORY.md to free space
  6. Log action for audit

Usage:
    from memory_cortex_bridge import MemoryCortexBridge
    bridge = MemoryCortexBridge()
    freed = bridge.offload_if_needed()  # Returns chars freed or 0

Wiring:
    - Call from pre_tool_call hook before every tool call
    - Or call from memory tool before add/replace operations
"""

import os
import re
import sys
import time
import hashlib
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------

HERMES_HOME = Path.home() / ".hermes"
MEMORY_PATH = HERMES_HOME / "memories" / "MEMORY.md"
CEREBRUM_DB = HERMES_HOME / "cerebrum_memory.db"
SUBCONSCIOUS = Path.home() / "hermes-agent"

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

MEMORY_LIMIT = 2500
MEMORY_PRESSURE_THRESHOLD = 2400  # 96% — start offloading
OFFLOAD_BATCH_SIZE = 3  # Move 3 entries at a time
MIN_ENTRY_AGE_HOURS = 1  # Don't offload entries younger than 1 hour

# ---------------------------------------------------------------------------
# CORTEXDB BRIDGE
# ---------------------------------------------------------------------------

class CortexDBBridge:
    """Minimal CortexDB interface for memory offloading."""
    
    def __init__(self):
        self._has_cortex = False
        self._db = None
        self._init()
    
    def _init(self):
        """Try CortexDB first, fall back to cerebrum SQLite."""
        try:
            sys.path.insert(0, str(SUBCONSCIOUS))
            from cortex_access import CortexDB as RealCortexDB
            self._db = RealCortexDB()
            self._has_cortex = True
        except Exception:
            self._has_cortex = False
            self._ensure_fallback()
    
    def _ensure_fallback(self):
        """Use cerebrum db with memory_units table as fallback."""
        CEREBRUM_DB.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(CEREBRUM_DB)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_units (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    content_hash TEXT UNIQUE,
                    source TEXT DEFAULT 'memory_offload',
                    category TEXT DEFAULT 'procedural',
                    trust REAL DEFAULT 0.85,
                    salience REAL DEFAULT 0.7,
                    access_count INTEGER DEFAULT 1,
                    created_at REAL,
                    last_accessed REAL,
                    entities TEXT,
                    tags TEXT,
                    session_id TEXT DEFAULT 'bridge',
                    offloaded_at REAL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_hash 
                ON memory_units(content_hash)
            """)
    
    def store(self, content: str, tags: List[str] = None) -> int:
        """Store memory content. Returns row/node id."""
        h = hashlib.md5(content.encode('utf-8')).hexdigest()
        now = time.time()
        
        if self._has_cortex:
            try:
                return self._db.insert_node(
                    text=content,
                    node_type="memory",
                    domain="general",
                    confidence=0.85,
                    provenance="memory_cortex_bridge",
                    metadata={
                        "tags": tags or [],
                        "offloaded_at": now,
                        "source": "memory_tool"
                    }
                )
            except Exception:
                pass  # Fall through to fallback
        
        # Fallback: cerebrum SQLite
        with sqlite3.connect(str(CEREBRUM_DB)) as conn:
            try:
                cur = conn.execute("""
                    INSERT INTO memory_units
                    (content, content_hash, tags, created_at, last_accessed, offloaded_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (content[:2000], h, ",".join(tags or []), now, now, now))
                conn.commit()
                return cur.lastrowid
            except sqlite3.IntegrityError:
                # Duplicate hash — already stored
                cur = conn.execute(
                    "SELECT id FROM memory_units WHERE content_hash = ?", (h,)
                )
                row = cur.fetchone()
                return row[0] if row else 0
    
    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Search offloaded memories."""
        if self._has_cortex:
            try:
                return self._db.search_text(query, node_type="memory", limit=limit)
            except Exception:
                pass
        
        with sqlite3.connect(str(CEREBRUM_DB)) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("""
                SELECT * FROM memory_units 
                WHERE content LIKE ?
                ORDER BY last_accessed DESC, salience DESC
                LIMIT ?
            """, (f'%{query}%', limit))
            return [dict(row) for row in cur.fetchall()]


# ---------------------------------------------------------------------------
# MEMORY PARSER
# ---------------------------------------------------------------------------

class MemoryParser:
    """Parse MEMORY.md into scored entries."""
    
    @staticmethod
    def parse() -> List[Dict]:
        """Parse MEMORY.md into structured entries with scores."""
        if not MEMORY_PATH.exists():
            return []
        
        content = MEMORY_PATH.read_text(encoding='utf-8')
        entries = []
        
        # Split by § delimiter
        raw_entries = [e.strip() for e in content.split('§') if e.strip()]
        
        for idx, raw in enumerate(raw_entries):
            entry = {
                'index': idx,
                'raw_text': raw,
                'char_count': len(raw),
                'priority': 5,  # Default
                'age_hours': 999,  # Default old
                'access_count': 0,
                'score': 0,
            }
            
            # Extract priority markers
            if '§' in raw[:10]:
                # Header line might have metadata
                pass
            
            # Check for date markers to estimate age
            date_patterns = [
                r'(\d{4})-(\d{2})-(\d{2})',
                r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}',
            ]
            for pattern in date_patterns:
                match = re.search(pattern, raw)
                if match:
                    try:
                        if '-' in match.group(0):
                            year, month, day = match.groups()
                            entry_date = datetime(int(year), int(month), int(day))
                            entry['age_hours'] = max(0, (datetime.now() - entry_date).total_seconds() / 3600)
                    except Exception:
                        pass
            
            # Detect priority from content
            priority_markers = {
                'CRITICAL': 10, 'IMPORTANT': 8, 'PREFER': 7,
                'HATES': 9, 'VALUES': 8, 'DEMANDS': 9,
            }
            for marker, prio in priority_markers.items():
                if marker in raw.upper():
                    entry['priority'] = max(entry['priority'], prio)
            
            # Calculate composite score (LOWER = more offloadable)
            # Weight: priority * -2 + age_hours * 0.5 + access_count * -1
            entry['score'] = (
                entry['priority'] * -2 +
                entry['age_hours'] * 0.5 +
                entry['access_count'] * -1
            )
            
            entries.append(entry)
        
        return entries
    
    @staticmethod
    def remove_entries(indices_to_remove: List[int]) -> int:
        """Remove entries by index from MEMORY.md. Returns chars freed."""
        if not MEMORY_PATH.exists():
            return 0
        
        content = MEMORY_PATH.read_text(encoding='utf-8')
        raw_entries = [e.strip() for e in content.split('§') if e.strip()]
        
        # Sort indices descending to remove from end first
        indices_to_remove = sorted(set(indices_to_remove), reverse=True)
        
        freed = 0
        for idx in indices_to_remove:
            if 0 <= idx < len(raw_entries):
                freed += len(raw_entries[idx]) + 3  # +3 for §\n delimiters
                raw_entries.pop(idx)
        
        # Rebuild file
        new_content = '§\n' + '\n§\n'.join(raw_entries) + '\n§\n'
        MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        MEMORY_PATH.write_text(new_content, encoding='utf-8')
        
        return freed


# ---------------------------------------------------------------------------
# MAIN BRIDGE
# ---------------------------------------------------------------------------

class MemoryCortexBridge:
    """Auto-offload bridge: Hermes memory → CortexDB."""
    
    def __init__(self):
        self.cortex = CortexDBBridge()
        self.parser = MemoryParser()
        self._last_check = 0
        self._check_interval = 60  # Seconds between checks
    
    def get_memory_size(self) -> int:
        """Current memory character count."""
        if not MEMORY_PATH.exists():
            return 0
        return len(MEMORY_PATH.read_text(encoding='utf-8'))
    
    def is_pressure(self) -> bool:
        """Check if memory is under pressure."""
        return self.get_memory_size() >= MEMORY_PRESSURE_THRESHOLD
    
    def offload_if_needed(self, force: bool = False) -> Dict:
        """
        Main entry point. Check pressure and offload if needed.
        Returns action summary.
        """
        now = time.time()
        if not force and (now - self._last_check) < self._check_interval:
            return {"status": "skipped", "reason": "cooldown", "seconds_since_check": int(now - self._last_check)}
        
        self._last_check = now
        
        current_size = self.get_memory_size()
        
        if current_size < MEMORY_PRESSURE_THRESHOLD and not force:
            return {
                "status": "ok",
                "memory_size": current_size,
                "threshold": MEMORY_PRESSURE_THRESHOLD,
                "pressure_pct": round(current_size / MEMORY_LIMIT * 100, 1),
            }
        
        # Parse and score entries
        entries = self.parser.parse()
        if not entries:
            return {"status": "error", "reason": "no_entries_found"}
        
        # Sort by score ascending (most offloadable first)
        entries.sort(key=lambda e: e['score'])
        
        # Select candidates
        candidates = []
        for entry in entries:
            if entry['age_hours'] < MIN_ENTRY_AGE_HOURS:
                continue  # Too fresh
            candidates.append(entry)
            if len(candidates) >= OFFLOAD_BATCH_SIZE:
                break
        
        if not candidates:
            return {"status": "warning", "reason": "no_candidates", "entries_parsed": len(entries)}
        
        # Offload each candidate
        offloaded = []
        indices_to_remove = []
        
        for candidate in candidates:
            try:
                node_id = self.cortex.store(
                    candidate['raw_text'],
                    tags=['memory_offload', f'priority_{candidate["priority"]}']
                )
                if node_id:
                    offloaded.append({
                        'index': candidate['index'],
                        'chars': candidate['char_count'],
                        'node_id': node_id,
                        'preview': candidate['raw_text'][:80] + '...',
                    })
                    indices_to_remove.append(candidate['index'])
            except Exception as e:
                pass  # Skip failed offloads
        
        if not offloaded:
            return {"status": "error", "reason": "offload_failed", "candidates": len(candidates)}
        
        # Remove from memory
        freed = self.parser.remove_entries(indices_to_remove)
        new_size = self.get_memory_size()
        
        return {
            "status": "offloaded",
            "entries_moved": len(offloaded),
            "chars_freed": freed,
            "memory_before": current_size,
            "memory_after": new_size,
            "pressure_pct": round(new_size / MEMORY_LIMIT * 100, 1),
            "details": offloaded,
        }
    
    def search_offloaded(self, query: str, limit: int = 5) -> List[Dict]:
        """Search memories that were offloaded to cortex."""
        return self.cortex.search(query, limit=limit)
    
    def get_stats(self) -> Dict:
        """Get current memory and offload stats."""
        current_size = self.get_memory_size()
        
        # Count offloaded memories
        offloaded_count = 0
        try:
            with sqlite3.connect(str(CEREBRUM_DB)) as conn:
                cur = conn.execute("SELECT COUNT(*) FROM memory_units")
                offloaded_count = cur.fetchone()[0]
        except Exception:
            pass
        
        return {
            "memory_size": current_size,
            "memory_limit": MEMORY_LIMIT,
            "pressure_threshold": MEMORY_PRESSURE_THRESHOLD,
            "pressure_pct": round(current_size / MEMORY_LIMIT * 100, 1),
            "is_pressure": current_size >= MEMORY_PRESSURE_THRESHOLD,
            "offloaded_count": offloaded_count,
            "has_cortex": self.cortex._has_cortex,
        }


# ---------------------------------------------------------------------------
# HOOK INTEGRATION
# ---------------------------------------------------------------------------

def pre_tool_call_hook(agent_state: Dict) -> Dict:
    """
    Hook to call before every tool call.
    Checks memory pressure and offloads if needed.
    
    Usage in agent loop:
        from memory_cortex_bridge import pre_tool_call_hook
        agent_state = pre_tool_call_hook(agent_state)
    """
    bridge = MemoryCortexBridge()
    result = bridge.offload_if_needed()
    
    if result.get('status') == 'offloaded':
        # Add to agent state for logging
        agent_state['_memory_offload'] = result
    
    return agent_state


def memory_add_hook(key: str, value: str, priority: int = 5) -> bool:
    """
    Hook to call before memory.add() operations.
    Ensures space is available before adding.
    
    Usage:
        from memory_cortex_bridge import memory_add_hook
        if memory_add_hook("new_key", "new_value"):
            memory.add("new_key", "new_value")
    """
    bridge = MemoryCortexBridge()
    
    # Check if adding this would push us over
    projected = bridge.get_memory_size() + len(key) + len(value) + 50
    
    if projected >= MEMORY_PRESSURE_THRESHOLD:
        # Offload first
        result = bridge.offload_if_needed(force=True)
        if result.get('status') != 'offloaded':
            return False  # Couldn't make room
    
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Memory-Cortex Bridge')
    parser.add_argument('--check', action='store_true', help='Check pressure and offload if needed')
    parser.add_argument('--stats', action='store_true', help='Show current stats')
    parser.add_argument('--search', type=str, help='Search offloaded memories')
    parser.add_argument('--force', action='store_true', help='Force offload regardless of cooldown')
    
    args = parser.parse_args()
    
    bridge = MemoryCortexBridge()
    
    if args.stats:
        print(json.dumps(bridge.get_stats(), indent=2))
    elif args.search:
        results = bridge.search_offloaded(args.search)
        print(json.dumps(results, indent=2))
    elif args.check or args.force:
        result = bridge.offload_if_needed(force=args.force)
        print(json.dumps(result, indent=2))
    else:
        # Default: check and offload if needed
        result = bridge.offload_if_needed()
        print(json.dumps(result, indent=2))