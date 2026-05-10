#!/usr/bin/env python3
"""
hermes_self_manager.py — Full self-management for context window death and seamless resume.

The loop:
1. Monitor context compressions (detect 5th compression)
2. Auto-checkpoint with full state
3. Distill into all context systems
4. Trigger new CLI + gateway restart
5. Auto-resume with full context upload

Usage:
  # Run as background watchdog:
  python3 ~/hermes-agent/agent/hermes_self_manager.py --watchdog
  
  # Or call when compression detected:
  python3 ~/hermes-agent/agent/hermes_self_manager.py --handoff
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path

# Paths
CEREBRUM_DB = Path.home() / ".hermes" / "cerebrum_memory.db"
CHECKPOINT_DIR = Path.home() / ".hermes" / "workspace" / "checkpoints"
HANDOFF_FILE = Path.home() / ".hermes" / "workspace" / "handoff_pending.json"
RESUME_SCRIPT = Path.home() / ".hermes" / "workspace" / "auto_resume.sh"
SELF_MANAGER_LOG = Path.home() / ".hermes" / "workspace" / "self_manager.log"

# Compression tracking
COMPRESSION_LOG = Path.home() / ".hermes" / "workspace" / "compression_log.jsonl"
COMPRESSION_THRESHOLD = 5

def _log(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with open(SELF_MANAGER_LOG, "a") as f:
        f.write(line + "\n")

def detect_compression_count():
    """Count compressions in current session."""
    if not COMPRESSION_LOG.exists():
        return 0
    
    # Count entries in last hour (current session)
    since = time.time() - 3600
    count = 0
    
    with open(COMPRESSION_LOG) as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get('timestamp', 0) > since:
                    count += 1
            except:
                pass
    
    return count

def log_compression():
    """Log a compression event."""
    entry = {
        "timestamp": time.time(),
        "event": "compression",
        "session_id": os.environ.get("HERMES_SESSION_ID", "unknown"),
    }
    with open(COMPRESSION_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")

def full_checkpoint(label: str = None):
    """Create comprehensive checkpoint with all state."""
    if not label:
        label = f"auto-handoff-{int(time.time())}"
    
    _log(f"Creating checkpoint: {label}")
    
    # Build context narrative
    context = build_full_context()
    
    # Save checkpoint file
    checkpoint_file = CHECKPOINT_DIR / f"{label}.json"
    checkpoint_data = {
        "label": label,
        "timestamp": time.time(),
        "context": context,
        "session_id": os.environ.get("HERMES_SESSION_ID", "unknown"),
    }
    
    checkpoint_file.write_text(json.dumps(checkpoint_data, indent=2, default=str))
    _log(f"Checkpoint saved: {checkpoint_file}")
    
    return checkpoint_file

def build_full_context():
    """Build comprehensive context from all systems."""
    context = {
        "timestamp": time.time(),
        "memory": {},
        "knowledge": {},
        "db_stats": {},
        "files_active": [],
        "tools_built": [],
        "next_steps": [],
    }
    
    # Read memory (from knowledge_search or direct)
    try:
        import sqlite3
        conn = sqlite3.connect(str(CEREBRUM_DB))
        c = conn.cursor()
        
        # Key stats
        for table in ['distilled_tips', 'rapid_learnings', 'tip_survival', 'prompt_fragments']:
            try:
                c.execute(f"SELECT COUNT(*) FROM {table}")
                context['db_stats'][table] = c.fetchone()[0]
            except:
                context['db_stats'][table] = 'N/A'
        
        # Recent learnings
        c.execute("""
            SELECT lesson, category, confidence, source
            FROM rapid_learnings
            ORDER BY id DESC LIMIT 10
        """)
        context['recent_learnings'] = [
            {'lesson': r[0], 'category': r[1], 'confidence': r[2], 'source': r[3]}
            for r in c.fetchall()
        ]
        
        conn.close()
    except Exception as e:
        context['db_error'] = str(e)
    
    # Active files (from subconscious)
    sub_dir = Path.home() / "hermes-agent"
    if sub_dir.exists():
        context['tools_built'] = [
            f.name for f in sub_dir.glob("hermes_*.py")
            if f.stat().st_mtime > time.time() - 86400  # Modified in last 24h
        ]
    
    # Knowledge docs
    kb_dir = Path.home() / ".hermes" / "knowledge"
    if kb_dir.exists():
        recent_docs = sorted(kb_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        context['knowledge']['recent_docs'] = [d.name for d in recent_docs[:5]]
    
    return context

def distill_all_context(checkpoint_file: Path):
    """Distill checkpoint into all context systems."""
    _log("Distilling into all context systems...")
    
    # 1. Save to knowledge base
    try:
        kb_file = Path.home() / ".hermes" / "knowledge" / f"session-handoff-{int(time.time())}.md"
        checkpoint_data = json.loads(checkpoint_file.read_text())
        
        kb_content = f"""# Session Handoff — {time.strftime('%Y-%m-%d %H:%M:%S')}

**Checkpoint:** `{checkpoint_file.name}`
**Session:** {checkpoint_data.get('session_id', 'unknown')}

## State Summary
- Distilled tips: {checkpoint_data['context']['db_stats'].get('distilled_tips', 'N/A')}
- Rapid learnings: {checkpoint_data['context']['db_stats'].get('rapid_learnings', 'N/A')}
- Tools built: {len(checkpoint_data['context'].get('tools_built', []))}

## Recent Tools Built
{chr(10).join(f'- `{t}`' for t in checkpoint_data['context'].get('tools_built', []))}

## Recent Learnings
{chr(10).join(f'- [{l["category"]}] {l["lesson"][:100]}... (conf={l["confidence"]:.2f})' for l in checkpoint_data['context'].get('recent_learnings', []))}

## Next Steps
Resume from checkpoint: `{checkpoint_file.stem}`
"""
        kb_file.write_text(kb_content)
        _log(f"Knowledge doc: {kb_file}")
    except Exception as e:
        _log(f"Knowledge save error: {e}")
    
    # 2. Update rapid learnings with handoff marker
    try:
        import sqlite3
        conn = sqlite3.connect(str(CEREBRUM_DB))
        c = conn.cursor()
        c.execute("""
            INSERT INTO rapid_learnings (lesson, category, confidence, source, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            f"Session handoff at compression. Checkpoint: {checkpoint_file.stem}. Resume with 'resume from checkpoint {checkpoint_file.stem}'",
            "meta",
            0.99,
            "self_manager",
            time.time()
        ))
        conn.commit()
        conn.close()
        _log("Rapid learning saved")
    except Exception as e:
        _log(f"Rapid learning error: {e}")
    
    # 3. Save handoff for CLI resume
    try:
        from hermes_cli_resume import save_handoff
        handoff_context = {
            'active_tasks': ['Resume from checkpoint', 'Continue enhancement cycles'],
            'files_modified': checkpoint_data['context'].get('tools_built', []),
            'next_steps': f"Resume from checkpoint {checkpoint_file.stem}",
            'notes': f"Auto-handoff at compression. All context distilled."
        }
        save_handoff(handoff_context, reason="compression_threshold")
        _log("Handoff saved for CLI resume")
    except Exception as e:
        _log(f"Handoff error: {e}")

def generate_resume_script(checkpoint_label: str):
    """Generate shell script for auto-resume."""
    script = f"""#!/bin/bash
# Auto-generated resume script for Hermes
# Checkpoint: {checkpoint_label}

echo "=== Hermes Auto-Resume ==="
echo "Checkpoint: {checkpoint_label}"
echo ""

# 1. Restart gateway (if needed)
echo "[1/3] Checking gateway..."
# hermes gateway status || hermes gateway restart

# 2. Start new Hermes session with context injection
echo "[2/3] Starting Hermes with context..."
echo "Tell the CLI:"
echo "  'Resume from checkpoint {checkpoint_label}'"
echo ""

# 3. Auto-upload context
echo "[3/3] Context ready for upload"
echo ""

echo "=== Resume Ready ==="
"""
    
    RESUME_SCRIPT.write_text(script)
    RESUME_SCRIPT.chmod(0o755)
    _log(f"Resume script: {RESUME_SCRIPT}")

def trigger_new_cli():
    """Trigger new terminal session with Hermes."""
    _log("Triggering new CLI session...")
    
    # This would use osascript or similar to open new terminal
    # For now, generate instructions
    _log("New CLI trigger: open terminal, run 'hermes'")
    _log("Then say: 'resume from checkpoint <label>'")

def full_handoff():
    """Execute complete handoff sequence."""
    _log("=" * 50)
    _log("SELF-MANAGER: FULL HANDOFF INITIATED")
    _log("=" * 50)
    
    # 1. Checkpoint
    label = f"auto-handoff-{int(time.time())}"
    checkpoint_file = full_checkpoint(label)
    
    # 2. Distill
    distill_all_context(checkpoint_file)
    
    # 3. Generate resume script
    generate_resume_script(label)
    
    # 4. Trigger new CLI
    trigger_new_cli()
    
    _log("=" * 50)
    _log(f"HANDOFF COMPLETE — Resume with: {label}")
    _log("=" * 50)
    
    return label

def watchdog_loop():
    """Background loop monitoring for compression threshold."""
    _log("Self-manager watchdog started")
    _log(f"Compression threshold: {COMPRESSION_THRESHOLD}")
    
    while True:
        count = detect_compression_count()
        
        if count >= COMPRESSION_THRESHOLD:
            _log(f"COMPRESSION THRESHOLD REACHED: {count}")
            full_handoff()
            # After handoff, exit or sleep long
            _log("Watchdog: handoff complete, sleeping 1 hour")
            time.sleep(3600)
        
        # Check every minute
        time.sleep(60)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--watchdog', action='store_true', help='Run background watchdog')
    parser.add_argument('--handoff', action='store_true', help='Execute immediate handoff')
    parser.add_argument('--status', action='store_true', help='Show compression count')
    args = parser.parse_args()
    
    if args.watchdog:
        watchdog_loop()
    elif args.handoff:
        label = full_handoff()
        print(f"\nHandoff complete: {label}")
    elif args.status:
        count = detect_compression_count()
        print(f"Compressions in current session: {count}/{COMPRESSION_THRESHOLD}")
    else:
        print("Usage:")
        print("  --watchdog  : Run background compression monitor")
        print("  --handoff   : Execute immediate full handoff")
        print("  --status    : Show current compression count")

if __name__ == "__main__":
    main()
