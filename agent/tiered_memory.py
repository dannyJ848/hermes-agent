#!/usr/bin/env python3
"""
tiered_memory.py — Three-tier memory system with automatic overflow and promotion.

Tiers:
  HOT   ~/.hermes/memory.json          (2,500 char limit, immediate context)
  WARM  ~/.hermes/cerebrum_memory.db   (SQLite, distilled tips awaiting evaluation)
  COLD  cortex PostgreSQL/SQLite       (Full archive, Elo-rated, vector searchable)

Auto-flow:
  1. HOT hits 80% (2,000 chars) → distill oldest entries → WARM
  2. WARM accumulates 50+ tips → batch LLM judge eval → COLD with Elo 1200
  3. COLD tips with Elo > 1300 + high access → promote to HOT as "golden"
  4. HOT entries unused 30 days → demote to WARM

Usage:
from agent.tiered_memory import TieredMemory
    tm = TieredMemory()
    tm.add("User prefers surgical precision", priority=10)  # Goes to HOT
    tm.check_overflow()  # Auto-distills if needed
    stats = tm.get_stats()
"""

import json
import hashlib
import time
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------

HERMES_HOME = Path.home() / ".hermes"
HOT_PATH = HERMES_HOME / "memory.json"
WARM_PATH = HERMES_HOME / "cerebrum_memory.db"

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

HOT_LIMIT = 2500
HOT_THRESHOLD = int(HOT_LIMIT * 0.8)  # 2,000 chars — start offloading
HOT_UNUSED_DAYS = 30
WARM_BATCH_SIZE = 50  # Evaluate this many tips at once
ELO_PROMOTE_THRESHOLD = 1300
ELO_DEMOTE_THRESHOLD = 950


# ---------------------------------------------------------------------------
# HOT TIER — Fast JSON key-value store
# ---------------------------------------------------------------------------

class HotTier:
    """In-memory context window sized key-value store."""
    
    def __init__(self, path: Path = HOT_PATH):
        self.path = path
        self._data: Dict[str, Any] = {}
        self._load()
    
    def _load(self):
        if self.path.exists():
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = {}
        else:
            self._data = {}
    
    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
    
    def _size(self) -> int:
        """Approximate character count of all entries."""
        return len(json.dumps(self._data, ensure_ascii=False))
    
    def add(self, key: str, value: str, priority: int = 5,
            tags: Optional[List[str]] = None) -> bool:
        """Add entry. Returns False if at hard limit."""
        if self._size() >= HOT_LIMIT:
            return False
        
        self._data[key] = {
            "value": value,
            "priority": priority,
            "tags": tags or [],
            "created_at": time.time(),
            "last_accessed": time.time(),
            "access_count": 0,
        }
        self._save()
        return True
    
    def get(self, key: str) -> Optional[Dict]:
        """Get entry and bump access stats."""
        entry = self._data.get(key)
        if entry:
            entry["last_accessed"] = time.time()
            entry["access_count"] = entry.get("access_count", 0) + 1
            self._save()
        return entry
    
    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            self._save()
            return True
        return False
    
    def get_oldest_low_priority(self, n: int = 5) -> List[tuple]:
        """Get N oldest entries with lowest priority for offloading."""
        entries = [
            (k, v["created_at"], v.get("priority", 5), v.get("access_count", 0))
            for k, v in self._data.items()
        ]
        # Sort: low priority first, then oldest, then low access
        entries.sort(key=lambda x: (x[2], x[1], x[3]))
        return entries[:n]
    
    def get_stale(self, days: int = HOT_UNUSED_DAYS) -> List[str]:
        """Get keys not accessed in N days."""
        cutoff = time.time() - (days * 86400)
        return [
            k for k, v in self._data.items()
            if v.get("last_accessed", v["created_at"]) < cutoff
        ]
    
    def entries(self) -> Dict[str, Any]:
        return dict(self._data)
    
    def size(self) -> int:
        return self._size()
    
    def usage_pct(self) -> float:
        return (self._size() / HOT_LIMIT) * 100


# ---------------------------------------------------------------------------
# WARM TIER — SQLite staging for distilled tips
# ---------------------------------------------------------------------------

class WarmTier:
    """SQLite staging area: distilled tips awaiting LLM judge evaluation."""
    
    def __init__(self, path: Path = WARM_PATH):
        self.path = path
        self._ensure_schema()
    
    def _ensure_schema(self):
        with sqlite3.connect(str(self.path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS staging_tips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    content_hash TEXT UNIQUE,
                    source_key TEXT,           -- Original memory key
                    source_tier TEXT,          -- 'hot' or 'cerebrum'
                    priority INTEGER DEFAULT 5,
                    tags TEXT,                 -- JSON list
                    distilled_at REAL,         -- timestamp
                    evaluated BOOLEAN DEFAULT 0,
                    judge_score REAL,          -- LLM judge quality 0-1
                    judge_feedback TEXT,
                    sent_to_cortex BOOLEAN DEFAULT 0,
                    cortex_node_id INTEGER
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_staging_evaluated 
                ON staging_tips(evaluated, sent_to_cortex)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_staging_hash 
                ON staging_tips(content_hash)
            """)
    
    def _hash(self, text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def stage(self, content: str, source_key: str = "", source_tier: str = "hot",
              priority: int = 5, tags: Optional[List[str]] = None) -> int:
        """Stage a distilled tip. Returns row id."""
        h = self._hash(content)
        with sqlite3.connect(str(self.path)) as conn:
            cur = conn.execute("""
                INSERT OR IGNORE INTO staging_tips
                (content, content_hash, source_key, source_tier, priority, tags, distilled_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (content, h, source_key, source_tier, priority,
                  json.dumps(tags or []), time.time()))
            conn.commit()
            return cur.lastrowid or self._get_id_by_hash(h)
    
    def _get_id_by_hash(self, h: str) -> int:
        with sqlite3.connect(str(self.path)) as conn:
            cur = conn.execute("SELECT id FROM staging_tips WHERE content_hash = ?", (h,))
            row = cur.fetchone()
            return row[0] if row else 0
    
    def get_unrated(self, limit: int = 50) -> List[Dict]:
        """Get tips awaiting evaluation."""
        with sqlite3.connect(str(self.path)) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("""
                SELECT * FROM staging_tips 
                WHERE evaluated = 0 
                ORDER BY priority DESC, distilled_at ASC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cur.fetchall()]
    
    def mark_evaluated(self, tip_id: int, score: float, feedback: str = ""):
        with sqlite3.connect(str(self.path)) as conn:
            conn.execute("""
                UPDATE staging_tips 
                SET evaluated = 1, judge_score = ?, judge_feedback = ?
                WHERE id = ?
            """, (score, feedback, tip_id))
            conn.commit()
    
    def mark_sent_to_cortex(self, tip_id: int, cortex_node_id: int):
        with sqlite3.connect(str(self.path)) as conn:
            conn.execute("""
                UPDATE staging_tips 
                SET sent_to_cortex = 1, cortex_node_id = ?
                WHERE id = ?
            """, (cortex_node_id, tip_id))
            conn.commit()
    
    def count_unrated(self) -> int:
        with sqlite3.connect(str(self.path)) as conn:
            cur = conn.execute("SELECT COUNT(*) FROM staging_tips WHERE evaluated = 0")
            return cur.fetchone()[0]
    
    def count_ready_for_cortex(self) -> int:
        """Tips with judge_score >= 0.6 that haven't been sent."""
        with sqlite3.connect(str(self.path)) as conn:
            cur = conn.execute("""
                SELECT COUNT(*) FROM staging_tips 
                WHERE evaluated = 1 AND judge_score >= 0.6 AND sent_to_cortex = 0
            """)
            return cur.fetchone()[0]


# ---------------------------------------------------------------------------
# COLD TIER — Cortex PostgreSQL/SQLite archive
# ---------------------------------------------------------------------------

class ColdTier:
    """Cortex archive: Elo-rated, vector-searchable long-term memory."""
    
    def __init__(self):
        self._has_cortex = False
        self._db = None
        self._init_cortex()
    
    def _init_cortex(self):
        """Try to import cortex_access, fall back to local SQLite."""
        try:
            sys.path.insert(0, str(Path.home() / "hermes-agent"))
            from cortex_access import CortexDB
            self._db = CortexDB()
            self._has_cortex = True
        except Exception:
            # Fallback: use cerebrum db with archive table
            self._has_cortex = False
            self._fallback_path = WARM_PATH
            self._ensure_fallback_schema()
    
    def _ensure_fallback_schema(self):
        with sqlite3.connect(str(self._fallback_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS archive_nodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    node_type TEXT DEFAULT 'memory',
                    domain TEXT DEFAULT 'general',
                    confidence REAL DEFAULT 0.5,
                    elo REAL DEFAULT 1200.0,
                    elo_matches INTEGER DEFAULT 0,
                    source_tip_id INTEGER,
                    provenance TEXT,
                    metadata TEXT,
                    created_at REAL,
                    last_seen REAL,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
    
    def archive(self, text: str, source_tip_id: int = 0, 
                domain: str = "general", confidence: float = 0.5,
                provenance: str = "", metadata: Optional[Dict] = None) -> int:
        """Archive a tip to cold storage. Returns node id."""
        if self._has_cortex:
            return self._db.insert_node(
                text=text,
                node_type="memory",
                domain=domain,
                confidence=confidence,
                elo=1200.0,
                provenance=provenance,
                metadata=metadata or {}
            )
        else:
            with sqlite3.connect(str(self._fallback_path)) as conn:
                cur = conn.execute("""
                    INSERT INTO archive_nodes
                    (text, domain, confidence, elo, source_tip_id, provenance, metadata, created_at, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (text, domain, confidence, 1200.0, source_tip_id,
                      provenance, json.dumps(metadata or {}), time.time(), time.time()))
                conn.commit()
                return cur.lastrowid
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search archived memories."""
        if self._has_cortex:
            return self._db.search_text(query, node_type="memory", limit=limit)
        else:
            with sqlite3.connect(str(self._fallback_path)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute("""
                    SELECT * FROM archive_nodes 
                    WHERE is_active = 1 AND text LIKE ?
                    ORDER BY elo DESC, last_seen DESC
                    LIMIT ?
                """, (f'%{query}%', limit))
                return [dict(row) for row in cur.fetchall()]
    
    def get_high_performers(self, min_elo: int = ELO_PROMOTE_THRESHOLD,
                           limit: int = 10) -> List[Dict]:
        """Get memories worthy of promotion to hot tier."""
        if self._has_cortex:
            return self._db.get_tips_for_eval(domain=None, min_elo=min_elo, limit=limit)
        else:
            with sqlite3.connect(str(self._fallback_path)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute("""
                    SELECT * FROM archive_nodes 
                    WHERE is_active = 1 AND elo >= ?
                    ORDER BY elo DESC, last_seen DESC
                    LIMIT ?
                """, (min_elo, limit))
                return [dict(row) for row in cur.fetchall()]
    
    def update_elo(self, node_id: int, new_elo: float) -> bool:
        if self._has_cortex:
            return self._db.update_elo(node_id, new_elo)
        else:
            with sqlite3.connect(str(self._fallback_path)) as conn:
                conn.execute("""
                    UPDATE archive_nodes SET elo = ?, elo_matches = elo_matches + 1
                    WHERE id = ?
                """, (new_elo, node_id))
                conn.commit()
                return True
    
    def touch(self, node_id: int) -> bool:
        """Bump last_seen on access."""
        if self._has_cortex:
            return self._db.touch_node(node_id)
        else:
            with sqlite3.connect(str(self._fallback_path)) as conn:
                conn.execute("""
                    UPDATE archive_nodes SET last_seen = ?, frequency = frequency + 1
                    WHERE id = ?
                """, (time.time(), node_id))
                conn.commit()
                return True


# ---------------------------------------------------------------------------
# MASTER CONTROLLER
# ---------------------------------------------------------------------------

class TieredMemory:
    """Three-tier memory with automatic overflow, distillation, and promotion."""
    
    def __init__(self):
        self.hot = HotTier()
        self.warm = WarmTier()
        self.cold = ColdTier()
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def add(self, key: str, value: str, priority: int = 5,
            tags: Optional[List[str]] = None) -> bool:
        """Add to hot tier. Auto-offload if needed."""
        # Check if we're near threshold BEFORE adding
        new_entry_size = len(json.dumps({key: {"value": value, "priority": priority, "tags": tags or []}}, ensure_ascii=False))
        projected_size = self.hot.size() + new_entry_size
        
        # If projected would exceed threshold, make room first
        if projected_size >= HOT_THRESHOLD:
            self._offload_oldest(count=5)  # Aggressive offload
        
        # Try direct add first
        if self.hot.add(key, value, priority, tags):
            return True
        
        # Still at hard limit — emergency offload
        self._offload_oldest(count=10)
        return self.hot.add(key, value, priority, tags)
    
    def get(self, key: str) -> Optional[str]:
        """Get value from hot tier (with access tracking)."""
        entry = self.hot.get(key)
        if entry:
            return entry["value"]
        return None
    
    def check_overflow(self) -> Dict[str, Any]:
        """Check and handle overflow. Returns action summary."""
        actions = {"offloaded": 0, "distilled": 0, "promoted": 0, "demoted": 0}
        
        # 1. Hot overflow
        if self.hot.usage_pct() >= 80:
            actions["offloaded"] = self._offload_oldest(count=3)
        
        # 2. Warm batch evaluation trigger
        if self.warm.count_unrated() >= WARM_BATCH_SIZE:
            actions["distilled"] = self._evaluate_warm_batch()
        
        # 3. Promote golden rules from cold
        golden = self.cold.get_high_performers(min_elo=ELO_PROMOTE_THRESHOLD, limit=3)
        for node in golden:
            # Check not already in hot
            key = f"golden_{node.get('id', hashlib.md5(node['text'].encode()).hexdigest()[:8])}"
            if key not in self.hot.entries():
                self.hot.add(key, node["text"], priority=10, tags=["golden", "promoted"])
                actions["promoted"] += 1
                self.cold.touch(node.get("id", 0))
        
        # 4. Demote stale hot entries
        stale_keys = self.hot.get_stale(days=HOT_UNUSED_DAYS)
        for key in stale_keys[:3]:  # Batch max 3
            entry = self.hot.entries().get(key)
            if entry:
                self.warm.stage(
                    content=entry["value"],
                    source_key=key,
                    source_tier="hot",
                    priority=entry.get("priority", 5),
                    tags=entry.get("tags", [])
                )
                self.hot.delete(key)
                actions["demoted"] += 1
        
        return actions
    
    def get_stats(self) -> Dict[str, Any]:
        """Full system statistics."""
        return {
            "hot": {
                "entries": len(self.hot.entries()),
                "size_chars": self.hot.size(),
                "usage_pct": round(self.hot.usage_pct(), 1),
                "limit": HOT_LIMIT,
            },
            "warm": {
                "unrated": self.warm.count_unrated(),
                "ready_for_cortex": self.warm.count_ready_for_cortex(),
            },
            "cold": {
                "has_cortex": self.cold._has_cortex,
                "high_performers": len(self.cold.get_high_performers(limit=100)),
            },
        }
    
    # ========================================================================
    # INTERNAL FLOW
    # ========================================================================
    
    def _offload_oldest(self, count: int = 3) -> int:
        """Move oldest low-priority hot entries to warm tier."""
        offloaded = 0
        candidates = self.hot.get_oldest_low_priority(n=count)
        
        for key, created_at, priority, access_count in candidates:
            entry = self.hot.entries().get(key)
            if not entry:
                continue
            
            # Distill: raw memory → structured tip
            distilled = self._distill(entry["value"], key)
            
            self.warm.stage(
                content=distilled,
                source_key=key,
                source_tier="hot",
                priority=priority,
                tags=entry.get("tags", [])
            )
            self.hot.delete(key)
            offloaded += 1
        
        return offloaded
    
    def _distill(self, raw_text: str, source_key: str) -> str:
        """Distill raw memory into a structured tip."""
        # Simple heuristic distillation
        # In production, this calls an LLM to extract the core insight
        lines = raw_text.strip().split('\n')
        
        # If it's already concise, keep it
        if len(raw_text) < 200:
            return raw_text
        
        # Otherwise extract key facts
        key_facts = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Keep lines with strong signals
            if any(signal in line.lower() for signal in [
                'prefer', 'avoid', 'always', 'never', 'use ', 'don\'t',
                'critical', 'important', 'must', 'should', 'when ', 'if '
            ]):
                key_facts.append(line)
        
        if key_facts:
            return " | ".join(key_facts[:3])
        
        # Fallback: first sentence + last sentence
        return raw_text[:250] + "..." if len(raw_text) > 250 else raw_text
    
    def _evaluate_warm_batch(self) -> int:
        """Evaluate warm tips and send high-quality ones to cortex."""
        tips = self.warm.get_unrated(limit=WARM_BATCH_SIZE)
        sent = 0
        
        for tip in tips:
            # Heuristic scoring (in production: LLM judge)
            score = self._heuristic_score(tip["content"])
            
            self.warm.mark_evaluated(tip["id"], score)
            
            if score >= 0.6:
                # Send to cold tier
                node_id = self.cold.archive(
                    text=tip["content"],
                    source_tip_id=tip["id"],
                    domain="general",
                    confidence=score,
                    provenance=f"warm_tip:{tip['source_key']}",
                    metadata={"source_tier": tip["source_tier"], "priority": tip["priority"]}
                )
                self.warm.mark_sent_to_cortex(tip["id"], node_id)
                sent += 1
        
        return sent
    
    def _heuristic_score(self, text: str) -> float:
        """Quick heuristic quality score 0-1."""
        score = 0.5
        text_lower = text.lower()
        
        # Actionability bonus
        action_words = ['do', 'use', 'check', 'verify', 'run', 'try', 'ensure', 'avoid', 'prefer', 'when', 'if']
        action_count = sum(1 for w in action_words if w in text_lower)
        score += min(0.2, action_count * 0.03)
        
        # Specificity bonus
        word_count = len(text.split())
        if 10 <= word_count <= 100:
            score += 0.1
        elif word_count > 100:
            score -= 0.1  # Too verbose
        
        # Condition bonus (triggered tips are more useful)
        if text_lower.startswith(('when', 'if')):
            score += 0.1
        
        # Concrete detail bonus
        if any(char.isdigit() for char in text):
            score += 0.05
        
        return min(1.0, max(0.0, score))


# ---------------------------------------------------------------------------
# CLI / TEST
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    
    tm = TieredMemory()
    
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        print(json.dumps(tm.get_stats(), indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "check":
        actions = tm.check_overflow()
        print(json.dumps(actions, indent=2))
    else:
        # Demo: add some memories, trigger overflow
        print("TieredMemory demo:")
        print(f"Initial hot usage: {tm.hot.usage_pct():.1f}%")
        
        # Add test entries until near threshold
        for i in range(20):
            tm.add(f"test_{i}", f"Memory entry number {i} with some content about testing the tiered memory system. " * 5)
        
        print(f"After adds: {tm.hot.usage_pct():.1f}%")
        print(f"Hot entries: {len(tm.hot.entries())}")
        
        # Trigger overflow handling
        actions = tm.check_overflow()
        print(f"Overflow actions: {actions}")
        print(f"Final hot usage: {tm.hot.usage_pct():.1f}%")
        print(f"Warm unrated: {tm.warm.count_unrated()}")
        print(f"Stats: {json.dumps(tm.get_stats(), indent=2)}")
