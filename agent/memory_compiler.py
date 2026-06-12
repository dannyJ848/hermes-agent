#!/usr/bin/env python3
"""memory_compiler.py — Nightly cross-session memory compiler.

Reads memory/YYYY-MM-DD.md files, extracts decisions/lessons, and compiles
them into structured cerebrum_memory.db entries with semantic categorization.

Usage:
    python3 memory_compiler.py --compile        # Compile recent memories
    python3 memory_compiler.py --stats          # Show compiler stats
    python3 memory_compiler.py --dry-run        # Preview without writing
"""

import argparse
import json
import logging
import os
import re
import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("memory_compiler")

DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"
MEMORY_DIR = Path.home() / "memory"


class MemoryCompiler:
    """Compile daily memory notes into structured cerebrum entries."""
    
    def __init__(self, db_path: Path = DB_PATH, memory_dir: Path = MEMORY_DIR):
        self.db_path = db_path
        self.memory_dir = memory_dir
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Ensure compiled_memories table exists."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS compiled_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT,
                source_date TEXT,
                memory_type TEXT,  -- 'decision', 'lesson', 'fact', 'preference', 'error'
                category TEXT,
                content TEXT,
                confidence REAL DEFAULT 0.7,
                extracted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_file, content)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _find_memory_files(self, days_back: int = 7) -> list[Path]:
        """Find recent memory files."""
        if not self.memory_dir.exists():
            return []
        
        files = []
        cutoff = datetime.now() - timedelta(days=days_back)
        
        for f in self.memory_dir.glob("*.md"):
            # Parse date from filename (YYYY-MM-DD.md)
            try:
                date_str = f.stem
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                if file_date >= cutoff:
                    files.append(f)
            except:
                pass
        
        return sorted(files)
    
    def _extract_memories(self, content: str) -> list[dict]:
        """Extract structured memories from markdown content."""
        memories = []
        
        # Pattern 1: Decision markers ("Decided to...", "Decision:...")
        decision_patterns = [
            r'(?i)(?:decided?|decision)[\s:]+(.+?)(?:\n|$)',
            r'(?i)(?:chose|chosen|opted|selected)[\s:]+(.+?)(?:\n|$)',
            r'(?i)(?:resolved|resolution)[\s:]+(.+?)(?:\n|$)',
        ]
        for pattern in decision_patterns:
            for match in re.finditer(pattern, content):
                memories.append({
                    "type": "decision",
                    "content": match.group(1).strip(),
                    "category": self._categorize(match.group(1))
                })
        
        # Pattern 2: Lesson markers ("Lesson learned...", "Note:...")
        lesson_patterns = [
            r'(?i)(?:lesson learned?|learned|takeaway)[\s:]+(.+?)(?:\n|$)',
            r'(?i)(?:key insight|insight|realization)[\s:]+(.+?)(?:\n|$)',
            r'(?i)(?:important|critical)[\s:]+(.+?)(?:\n|$)',
        ]
        for pattern in lesson_patterns:
            for match in re.finditer(pattern, content):
                memories.append({
                    "type": "lesson",
                    "content": match.group(1).strip(),
                    "category": self._categorize(match.group(1))
                })
        
        # Pattern 3: Error markers ("Error:...", "Bug:...", "Fixed:...")
        error_patterns = [
            r'(?i)(?:error|bug|issue|problem|broke|broken)[\s:]+(.+?)(?:\n|$)',
            r'(?i)(?:fixed|fix|resolved|patch|workaround)[\s:]+(.+?)(?:\n|$)',
        ]
        for pattern in error_patterns:
            for match in re.finditer(pattern, content):
                memories.append({
                    "type": "error",
                    "content": match.group(1).strip(),
                    "category": self._categorize(match.group(1))
                })
        
        # Pattern 4: Preference markers ("User prefers...", "Preference:...")
        pref_patterns = [
            r'(?i)(?:user prefers?|prefers?|preference)[\s:]+(.+?)(?:\n|$)',
            r'(?i)(?:likes?|dislikes?|hates?|wants?)[\s:]+(.+?)(?:\n|$)',
        ]
        for pattern in pref_patterns:
            for match in re.finditer(pattern, content):
                memories.append({
                    "type": "preference",
                    "content": match.group(1).strip(),
                    "category": self._categorize(match.group(1))
                })
        
        # Pattern 5: Fact markers ("Fact:...", "Note that...")
        fact_patterns = [
            r'(?i)(?:fact|note that|remember that|be aware)[\s:]+(.+?)(?:\n|$)',
        ]
        for pattern in fact_patterns:
            for match in re.finditer(pattern, content):
                memories.append({
                    "type": "fact",
                    "content": match.group(1).strip(),
                    "category": self._categorize(match.group(1))
                })
        
        # Deduplicate by content
        seen = set()
        unique = []
        for m in memories:
            key = m["content"].lower()[:100]
            if key not in seen:
                seen.add(key)
                unique.append(m)
        
        return unique
    
    def _categorize(self, text: str) -> str:
        """Categorize memory content."""
        text_lower = text.lower()
        
        categories = {
            "technical": ["code", "script", "python", "sql", "database", "api", "error", "bug", "fix", "patch"],
            "workflow": ["process", "pipeline", "cron", "schedule", "automation", "script"],
            "infrastructure": ["server", "dgx", "macbook", "ssh", "deploy", "config", "setup"],
            "user": ["user", "preference", "likes", "dislikes", "wants", "prefers"],
            "cognitive": ["memory", "learning", "skill", "tip", "distill", "orchestrator"],
            "medical": ["clinic", "patient", "hipaa", "clinical", "medical", "exam"],
        }
        
        scores = {cat: sum(1 for kw in kws if kw in text_lower) for cat, kws in categories.items()}
        if not scores:
            return "general"
        best = max(scores.items(), key=lambda x: x[1])[0]
        return best if scores[best] > 0 else "general"
    
    def compile_memories(self, days_back: int = 7, dry_run: bool = False) -> dict:
        """Compile memories from recent files."""
        files = self._find_memory_files(days_back=days_back)
        logger.info(f"Found {len(files)} memory files to process")
        
        total_extracted = 0
        total_inserted = 0
        
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        
        for file_path in files:
            try:
                content = file_path.read_text()
                memories = self._extract_memories(content)
                total_extracted += len(memories)
                
                date_str = file_path.stem
                
                for mem in memories:
                    if dry_run:
                        continue
                    
                    try:
                        cur.execute("""
                            INSERT OR IGNORE INTO compiled_memories
                            (source_file, source_date, memory_type, category, content, confidence)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (str(file_path), date_str, mem["type"], mem["category"], mem["content"], 0.7))
                        if cur.rowcount > 0:
                            total_inserted += 1
                    except Exception as e:
                        logger.warning(f"Insert failed: {e}")
                
                logger.info(f"  {file_path.name}: {len(memories)} memories extracted")
                
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Compilation complete: {total_extracted} extracted, {total_inserted} inserted")
        return {"files_processed": len(files), "extracted": total_extracted, "inserted": total_inserted}
    
    def get_stats(self) -> dict:
        """Get compiler statistics."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM compiled_memories")
        total = cur.fetchone()[0]
        
        cur.execute("SELECT memory_type, COUNT(*) FROM compiled_memories GROUP BY memory_type")
        by_type = {row[0]: row[1] for row in cur.fetchall()}
        
        cur.execute("SELECT category, COUNT(*) FROM compiled_memories GROUP BY category")
        by_category = {row[0]: row[1] for row in cur.fetchall()}
        
        cur.execute("SELECT COUNT(DISTINCT source_date) FROM compiled_memories")
        days_covered = cur.fetchone()[0]
        
        conn.close()
        
        return {
            "total_compiled": total,
            "by_type": by_type,
            "by_category": by_category,
            "days_covered": days_covered
        }
    
    def get_recent_memories(self, memory_type: str = None, limit: int = 20) -> list[dict]:
        """Get recent compiled memories."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        
        if memory_type:
            cur.execute("""
                SELECT source_date, memory_type, category, content, confidence
                FROM compiled_memories
                WHERE memory_type = ?
                ORDER BY extracted_at DESC
                LIMIT ?
            """, (memory_type, limit))
        else:
            cur.execute("""
                SELECT source_date, memory_type, category, content, confidence
                FROM compiled_memories
                ORDER BY extracted_at DESC
                LIMIT ?
            """, (limit,))
        
        rows = cur.fetchall()
        conn.close()
        
        return [
            {
                "date": r[0], "type": r[1], "category": r[2],
                "content": r[3], "confidence": r[4]
            }
            for r in rows
        ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--compile", action="store_true", help="Compile memories")
    parser.add_argument("--stats", action="store_true", help="Show stats")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--days", type=int, default=7, help="Days back to process")
    parser.add_argument("--type", help="Filter by memory type")
    parser.add_argument("--recent", action="store_true", help="Show recent memories")
    args = parser.parse_args()
    
    compiler = MemoryCompiler()
    
    if args.compile:
        result = compiler.compile_memories(days_back=args.days, dry_run=args.dry_run)
        print(json.dumps(result, indent=2))
    
    elif args.recent:
        memories = compiler.get_recent_memories(memory_type=args.type, limit=20)
        for m in memories:
            print(f"[{m['date']}] {m['type']:10} | {m['category']:12} | {m['content'][:80]}...")
    
    else:
        stats = compiler.get_stats()
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
