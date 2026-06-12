#!/usr/bin/env python3
"""whisper_injector.py — Inject subconscious whispers into system prompt.

Before each API call, selects 1-2 relevant tips by semantic similarity to
conversation context and injects them into the system prompt.

Usage:
    python3 whisper_injector.py --test          # Test injection
    python3 whisper_injector.py --query "text"  # Find relevant whispers
    python3 whisper_injector.py --stats         # Show injection stats
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
logger = logging.getLogger("whisper_injector")

DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"
MAX_WHISPERS = 2
WHISPER_PREFIX = "\n[ subconscious whisper ]\n"


class WhisperInjector:
    """Inject relevant subconscious whispers into prompts."""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
    
    def _get_all_tips(self) -> list[dict]:
        """Get all injectable tips from multiple sources."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        
        tips = []
        
        # 1. High-Elo promoted tips
        try:
            cur.execute("""
                SELECT d.id, d.tip_hash, d.topic, d.tip_text, d.priority, d.confidence, d.category
                FROM distilled_tips d
                JOIN elo_scores e ON d.id = e.tip_id
                WHERE e.promoted = 1
                ORDER BY e.elo DESC
                LIMIT 20
            """)
            for row in cur.fetchall():
                tips.append({
                    "id": row[0], "hash": row[1], "topic": row[2], "text": row[3],
                    "priority": row[4], "confidence": row[5], "category": row[6],
                    "source": "elo_promoted"
                })
        except:
            pass
        
        # 2. High-confidence distilled tips (fallback)
        if not tips:
            cur.execute("""
                SELECT id, tip_hash, topic, tip_text, priority, confidence, category
                FROM distilled_tips
                WHERE confidence >= 0.7
                ORDER BY priority DESC, confidence DESC
                LIMIT 20
            """)
            for row in cur.fetchall():
                tips.append({
                    "id": row[0], "hash": row[1], "topic": row[2], "text": row[3],
                    "priority": row[4], "confidence": row[5], "category": row[6],
                    "source": "distilled"
                })
        
        # 3. Compiled memories (recent lessons)
        try:
            cur.execute("""
                SELECT id, memory_type, category, content, confidence
                FROM compiled_memories
                WHERE memory_type IN ('lesson', 'decision', 'preference')
                ORDER BY extracted_at DESC
                LIMIT 10
            """)
            for row in cur.fetchall():
                tips.append({
                    "id": f"mem-{row[0]}", "hash": "", "topic": row[2],
                    "text": row[3], "priority": row[4], "confidence": row[4],
                    "category": row[2], "source": "compiled_memory"
                })
        except:
            pass
        
        conn.close()
        return tips
    
    def _score_relevance(self, tip: dict, context: str) -> float:
        """Score tip relevance to context using keyword overlap."""
        context_lower = context.lower()
        text_lower = tip.get("text", "").lower()
        topic_lower = tip.get("topic", "").lower()
        category_lower = tip.get("category", "").lower()
        
        score = 0.0
        
        # Extract keywords from context (simple approach)
        context_words = set(re.findall(r'\b[a-z]{4,}\b', context_lower))
        
        # Count overlaps
        tip_words = set(re.findall(r'\b[a-z]{4,}\b', text_lower + " " + topic_lower + " " + category_lower))
        overlap = context_words & tip_words
        
        score += len(overlap) * 0.3
        
        # Boost for exact topic match
        if topic_lower in context_lower or category_lower in context_lower:
            score += 1.0
        
        # Boost for high confidence/priority
        score += tip.get("confidence", 0.5) * 0.5
        score += tip.get("priority", 0.5) * 0.3
        
        # Source bonus
        if tip.get("source") == "elo_promoted":
            score += 0.5
        elif tip.get("source") == "compiled_memory":
            score += 0.3
        
        return score
    
    def select_whispers(self, context: str, max_whispers: int = MAX_WHISPERS) -> list[dict]:
        """Select most relevant whispers for context."""
        tips = self._get_all_tips()
        if not tips:
            return []
        
        # Score all tips
        scored = [(self._score_relevance(tip, context), tip) for tip in tips]
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Return top N above threshold
        threshold = 1.0
        selected = [tip for score, tip in scored[:max_whispers] if score > threshold]
        
        logger.info(f"Selected {len(selected)} whispers from {len(tips)} candidates")
        return selected
    
    def format_whispers(self, whispers: list[dict]) -> str:
        """Format whispers for injection into system prompt."""
        if not whispers:
            return ""
        
        lines = [WHISPER_PREFIX]
        for i, w in enumerate(whispers, 1):
            source_tag = f"[{w.get('source', 'tip')}]"
            lines.append(f"  {i}. {source_tag} {w['text'][:200]}")
        
        return "\n".join(lines)
    
    def inject(self, system_prompt: str, context: str) -> str:
        """Inject whispers into system prompt."""
        whispers = self.select_whispers(context)
        if not whispers:
            return system_prompt
        
        whisper_text = self.format_whispers(whispers)
        
        # Inject before the last section or at end
        # Look for a good insertion point
        insertion_markers = [
            "## Tools",
            "## External vs Internal",
            "## Red Lines",
            "## Memory",
        ]
        
        for marker in insertion_markers:
            if marker in system_prompt:
                # Insert before this marker
                idx = system_prompt.index(marker)
                return system_prompt[:idx] + whisper_text + "\n\n" + system_prompt[idx:]
        
        # Fallback: append at end
        return system_prompt + "\n" + whisper_text
    
    def get_stats(self) -> dict:
        """Get injection statistics."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        
        stats = {
            "distilled_tips": 0,
            "elo_promoted": 0,
            "compiled_memories": 0,
            "total_candidates": 0
        }
        
        try:
            cur.execute("SELECT COUNT(*) FROM distilled_tips")
            stats["distilled_tips"] = cur.fetchone()[0]
        except:
            pass
        
        try:
            cur.execute("SELECT COUNT(*) FROM elo_scores WHERE promoted = 1")
            stats["elo_promoted"] = cur.fetchone()[0]
        except:
            pass
        
        try:
            cur.execute("SELECT COUNT(*) FROM compiled_memories")
            stats["compiled_memories"] = cur.fetchone()[0]
        except:
            pass
        
        stats["total_candidates"] = stats["distilled_tips"] + stats["compiled_memories"]
        
        conn.close()
        return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Test injection")
    parser.add_argument("--query", help="Find relevant whispers for query")
    parser.add_argument("--stats", action="store_true", help="Show stats")
    parser.add_argument("--max", type=int, default=2, help="Max whispers")
    args = parser.parse_args()
    
    injector = WhisperInjector()
    
    if args.query:
        whispers = injector.select_whispers(args.query, max_whispers=args.max)
        print(f"Query: {args.query}")
        print(f"Found {len(whispers)} relevant whispers:")
        for w in whispers:
            print(f"  [{w.get('source', 'tip')}] {w['topic']}: {w['text'][:100]}...")
    
    elif args.test:
        test_prompt = "You are Hermes Agent...\n\n## Tools\nUse tools wisely.\n\n## Memory\nSave facts."
        test_context = "user wants to deploy a model to DGX with vLLM and needs to configure speculative decoding"
        
        result = injector.inject(test_prompt, test_context)
        print("=== INJECTED PROMPT ===")
        print(result)
        print("\n=== WHISPERS INJECTED ===")
        whispers = injector.select_whispers(test_context)
        for w in whispers:
            print(f"  [{w.get('source', 'tip')}] {w['topic']}: {w['text'][:100]}...")
    
    else:
        stats = injector.get_stats()
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
