#!/usr/bin/env python3
"""Memory Auto-Pruner — integrated into distillation bridge.
Runs as part of bottom_up_store() to keep MEMORY under budget.
Also handles offload to Cerebrum semantic_facts for long-term storage.
"""
import sqlite3
import hashlib
import re
import os
import time
import json

MEM_PATH = os.path.expanduser("~/.hermes/memories/MEMORY.md")
CEREBRUM_DB = os.path.expanduser("~/.hermes/cerebrum_memory.db")
MAX_CHARS = 30000  # Target: keep MEMORY under 30K (well below 50K limit)
HONCHO_URL = "http://localhost:8000"

def offload_to_cerebrum(entry_text, topic_hint=""):
    """Store verbose entry as a semantic fact in cerebrum."""
    try:
        db = sqlite3.connect(CEREBRUM_DB, timeout=5)
        content_hash = hashlib.sha256(entry_text.encode()).hexdigest()[:16]
        
        # Check if already stored
        existing = db.execute(
            "SELECT id FROM semantic_facts WHERE content = ?",
            (entry_text[:2000],)
        ).fetchone()
        if existing:
            db.close()
            return True
        
        # Extract tags from content
        tags = []
        for match in re.findall(r'(?:Apr|Mar|Jun|Jan) 2026|~/hermes-agent/\w+|~/.hermes/plugins/\w+', entry_text):
            tags.append(match.replace(" ", "-"))
        
        db.execute("""
            INSERT INTO semantic_facts 
            (content, source, provenance, category, trust, salience, 
             access_count, consolidation_count, created_at, last_accessed, 
             last_consolidated, entities, tags, session_id)
            VALUES (?, 'memory_offload', 'auto_pruner', 'procedural', 
                    0.85, 0.7, 1, 0, ?, ?, 0, ?, ?, 'pruner')
        """, (
            entry_text[:2000],
            time.time(),
            time.time(),
            topic_hint[:100],
            json.dumps(tags[:5]),
        ))
        db.commit()
        db.close()
        return True
    except Exception as e:
        return False

def offload_to_honcho(entry_text, topic_hint=""):
    """Store in Honcho for unlimited semantic search."""
    try:
        import requests
        resp = requests.post(
            f"{HONCHO_URL}/v3/workspaces/hermes/peers/evey/messages",
            json={"content": entry_text[:4000], "metadata": {"type": "memory_offload", "topic": topic_hint}},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False  # Honcho down — not critical

def load_entries():
    with open(MEM_PATH, "r") as f:
        content = f.read()
    return [e.strip() for e in content.split("§") if e.strip()], len(content)

def save_entries(entries):
    output = "§\n" + "§\n".join(entries) + "\n§\n"
    with open(MEM_PATH, "w") as f:
        f.write(output)
    return len(output)

def prune(force=False):
    """Main pruning routine. Returns stats dict."""
    entries, total_chars = load_entries()
    
    if total_chars < MAX_CHARS and not force:
        return {"status": "under_budget", "chars": total_chars, "entries": len(entries)}
    
    original_count = len(entries)
    original_chars = total_chars
    offloaded = 0
    
    # --- Phase 1: Exact dedup ---
    seen = {}
    deduped = []
    for e in entries:
        key = e.strip().lower()
        if key not in seen:
            seen[key] = e
            deduped.append(e)
        else:
            offload_to_cerebrum(e)
            offloaded += 1
    entries = deduped
    
    # --- Phase 2: Near-dedup (same first 60 chars) ---
    prefix_map = {}
    order = []
    for e in entries:
        prefix = e[:60].strip().lower()
        if prefix in prefix_map:
            # Keep longer version
            if len(e) > len(prefix_map[prefix]):
                offload_to_cerebrum(prefix_map[prefix], prefix[:40])
                prefix_map[prefix] = e
            else:
                offload_to_cerebrum(e, prefix[:40])
                offloaded += 1
        else:
            prefix_map[prefix] = e
            order.append(prefix)
    entries = [prefix_map[p] for p in order]
    
    # --- Phase 3: Topic cluster merging ---
    clusters = [
        (["AGI CONTINUOUS", "ANTI-STOP", "AGI CONTINUOUS LOOP", "24/7 CONTINUOUS"], "agi-ops"),
        (["SESSION 20260405"], "session-transcript"),
        (["CHECKPOINT RESTORE BUG"], "checkpoint-bug"),
        (["CONTEXT RESERVOIR"], "context-reservoir"),
        (["RED TEAM HIPPOCAMPUS"], "red-team"),
        (["PII REDACTION"], "pii"),
        (["COGNITIVE ARCHITECTURE V5"], "cognitive-arch"),
        (["CHROME COOKIE"], "chrome-cookie"),
        (["X API VIA JXA"], "x-api"),
        (["WEB SCRAPING ESCALATION"], "web-scraping"),
        (["CONTEXT ROT"], "context-rot"),
        (["DISTILLATION BRIDGE"], "distillation"),
        (["EYES PLUGIN", "EYES ARCHITECTURE"], "eyes"),
        (["TOTAL ITERATIVE MASTERY", "FLUID REASONING"], "mastery"),
    ]
    
    for keywords, topic in clusters:
        matching = [(i, e) for i, e in enumerate(entries) 
                     if any(kw.upper() in e.upper() for kw in keywords)]
        if len(matching) <= 1:
            continue
        
        # Keep the LAST (most recent) entry, offload the rest
        keeper_idx = matching[-1][0]
        for i, e in matching[:-1]:
            offload_to_cerebrum(e, topic)
            offload_to_honcho(e, topic)
            offloaded += 1
        
        # Remove non-keepers
        entries = [e for i, e in enumerate(entries) if i == keeper_idx or i not in [m[0] for m in matching[:-1]]]
    
    # --- Phase 4: Compress verbose entries (>1500 chars) ---
    compressed_entries = []
    for e in entries:
        if len(e) > 1500:
            offload_to_cerebrum(e, e[:40])
            offload_to_honcho(e, e[:40])
            short = e[:900] + " [...offloaded to Cerebrum+Honcho]"
            compressed_entries.append(short)
            offloaded += 1
        else:
            compressed_entries.append(e)
    entries = compressed_entries
    
    # --- Phase 5: If still over budget, trim oldest/least-important ---
    _, current_chars = load_entries()  # Recalculate
    if current_chars > MAX_CHARS:
        # Score entries by recency and importance
        scored = []
        for e in entries:
            score = 0
            # Recent = higher score
            if "2026-04-05" in e or "2026-04-06" in e or "(Apr 2026)" in e:
                score += 3
            elif "2026-04-04" in e or "2026-04-03" in e:
                score += 2
            # Core infrastructure = higher score
            for kw in ["CEREBRUM", "BRAIN", "DISTILLATION", "RED TEAM", "OPSEC", "CORE PHILOSOPHY"]:
                if kw in e.upper():
                    score += 2
            # Session transcripts = low score (already offloaded)
            if "TRANSCRIPT" in e.upper():
                score -= 2
            scored.append((score, e))
        
        # Sort by score ascending (worst first) and trim
        scored.sort(key=lambda x: x[0])
        while current_chars > MAX_CHARS and scored:
            score, entry = scored.pop(0)
            if score < 2:  # Only remove low-value entries
                offload_to_cerebrum(entry, "budget-trim")
                entries.remove(entry)
                current_chars -= len(entry)
                offloaded += 1
    
    new_size = save_entries(entries)
    
    return {
        "status": "pruned",
        "original_entries": original_count,
        "original_chars": original_chars,
        "final_entries": len(entries),
        "final_chars": new_size,
        "offloaded": offloaded,
        "space_freed": original_chars - new_size,
        "pct_freed": (original_chars - new_size) / original_chars * 100,
    }

if __name__ == "__main__":
    result = prune(force=True)
    print(json.dumps(result, indent=2))
