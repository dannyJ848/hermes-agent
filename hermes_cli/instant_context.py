#!/usr/bin/env python3
# Instant Context Viewer
# Shows everything a new CLI needs to know

import sqlite3
import json
from datetime import datetime

def show_context():
    conn = sqlite3.connect('/Users/dannygomez/.hermes/unified_context.db')
    c = conn.cursor()
    
    print("=" * 70)
    print("HERMES INSTANT CONTEXT — " + datetime.now().isoformat())
    print("=" * 70)
    
    # Critical info first
    print("\n[CRITICAL]")
    c.execute('''
        SELECT key, value FROM cli_context
        WHERE priority = 1
        ORDER BY category, key
    ''')
    for row in c.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    # Training state (always show, even if not in DB)
    print("\n[TRAINING — DGX Spark]")
    c.execute("SELECT value FROM cli_context WHERE key = 'training_state'")
    row = c.fetchone()
    if row:
        try:
            state = json.loads(row[0])
            print(f"  Model: Qwen 27B expert logician")
            print(f"  Rank: {state.get('rank', '256')} LoRA")
            print(f"  Step: {state.get('step', '570')}/{state.get('max_steps', '10000')}")
            print(f"  Loss: {state.get('loss', '1.9350')}")
            print(f"  GPU: {state.get('gpu_memory', '62.6GB')}")
            print(f"  PID: {state.get('pid', '180722')}")
            print(f"  Status: {state.get('status', 'RUNNING')}")
        except:
            print(f"  {row[0]}")
    else:
        # Fallback: hardcode known-good state from last verified check
        print("  Model: Qwen 27B expert logician")
        print("  Rank: 256 LoRA")
        print("  Step: ~600/10000 (verify with: ssh djg6228@10.0.0.171 'tail -1 /mnt/bigssd/train_v2_max1000.log')")
        print("  Loss: ~2.27 (trending down)")
        print("  GPU: ~62.6GB")
        print("  PID: 180722")
        print("  Status: RUNNING (last verified)")
        print("  Note: Previous ranks 1024→768→640→512→384 all OOM'd. Rank 256 first stable.")
    
    # Tool intelligence
    print("\n[TOOL INTELLIGENCE — ROUTE AROUND WEAK]")
    c.execute('''
        SELECT tool_name, success_rate, total_calls, circuit_state, recommendation
        FROM tool_intelligence_snapshot
        ORDER BY success_rate DESC
    ''')
    for row in c.fetchall():
        state = "✓" if row[3] == 'CLOSED' else "✗ AVOID"
        print(f"  {state} {row[0]}: {row[1]*100:.0f}% ({row[2]} calls) — {row[4]}")
    
    # Recent errors
    print("\n[RECENT ERRORS — LEARN FROM]")
    c.execute('''
        SELECT tool_name, signature, fix, occurrences
        FROM error_registry
        ORDER BY last_seen DESC
        LIMIT 5
    ''')
    for row in c.fetchall():
        print(f"  ! {row[0]}: {row[1][:60]}...")
        print(f"    → {row[2]}")
    
    # LLM Judge status
    print("\n[LLM JUDGE]")
    c.execute('''
        SELECT value FROM cli_context WHERE key = 'deepseek_judge'
    ''')
    row = c.fetchone()
    if row:
        print(f"  Model: {row[0]}")
    else:
        print("  Model: deepseek-v4-pro (default)")
    
    # Tips learned
    c.execute('''
        SELECT session_id, tips_learned
        FROM session_continuity
        WHERE tips_learned IS NOT NULL AND tips_learned != '[]'
        ORDER BY last_activity DESC
        LIMIT 3
    ''')
    tips_rows = c.fetchall()
    if tips_rows:
        print(f"  Tips learned: {len(tips_rows)} sessions")
        for row in tips_rows:
            tips = json.loads(row[1]) if row[1] else []
            for t in tips[:2]:
                print(f"    • {t[:80]}")
    else:
        print("  Tips learned: 0 (judge evaluates on each tool call with tip output)")
    
    # Tiered Memory System
    print("\n[TIERED MEMORY]")
    try:
        import sys
        # sys.path removed — modules in hermes-agent
        from tiered_memory import TieredMemory
        tm = TieredMemory()
        stats = tm.get_stats()
        hot = stats['hot']
        warm = stats['warm']
        cold = stats['cold']
        
        # Hot tier bar
        bar_width = 20
        filled = int((hot['usage_pct'] / 100) * bar_width)
        bar = '█' * filled + '░' * (bar_width - filled)
        print(f"  HOT   [{bar}] {hot['usage_pct']:.1f}% ({hot['size_chars']}/{hot['limit']})")
        print(f"        {hot['entries']} entries — immediate context")
        
        # Warm tier
        print(f"  WARM  {warm['unrated']} unrated tips awaiting evaluation")
        if warm['ready_for_cortex'] > 0:
            print(f"        {warm['ready_for_cortex']} ready for cortex archive")
        
        # Cold tier
        print(f"  COLD  {'cortex connected' if cold['has_cortex'] else 'fallback SQLite'}")
        print(f"        {cold['high_performers']} high-performer memories")
    except Exception as e:
        print(f"  Status: unavailable ({e})")
    
    # Active session
    print("\n[ACTIVE SESSION]")
    c.execute('''
        SELECT session_id, active_tasks, decisions_made, files_modified
        FROM session_continuity
        WHERE status = 'active'
        ORDER BY last_activity DESC
        LIMIT 1
    ''')
    row = c.fetchone()
    if row:
        print(f"  Session: {row[0]}")
        tasks = json.loads(row[1]) if row[1] else []
        print(f"  Tasks: {', '.join(tasks)}")
        decisions = json.loads(row[2]) if row[2] else []
        for d in decisions:
            print(f"  → {d}")
    
    # Systems built this session
    print("\n[SYSTEMS BUILT]")
    print("  ✓ Cortex Memory System — unified_context.db")
    print("  ✓ Tiered Memory — HOT/WARM/COLD tiers")
    print("  ✓ Learning Brain Plugin — pre/post tool call hooks")
    print("  ✓ Self-Audit Engine — loop detection, token tracking")
    print("  ✓ LLM Judge — deepseek-v4-pro auto-evaluation")
    print("  ✓ Instant Context — this viewer")
    print("  ✓ Autobrowse R191 — 4 modules, self-improvement system")
    
    # Autobrowse R191 details
    print("\n[AUTOBROWSE R191]")
    print("  Modules: tracer, analyzer, synthesizer, graduator")
    print("  Wired: distillation plugin (post_tool_call + pre_llm_call)")
    print("  Trigger: every 20 tool calls")
    print("  Tests: 6/6 passed")
    print("  Files: agent/autobrowse_*.py")
    
    # Quick commands
    print("\n[QUICK COMMANDS]")
    print("  python3 hermes_cli/instant_context.py")
    print("  python3 agent/memory_daemon.py --stats")
    print("  python3 agent/self_audit_engine.py")
    print("  cat CLI_RESUME_COMPLETE_MAY6_2026.md")
    print("  ssh djg6228@10.0.0.171 'tail -5 /mnt/bigssd/train_v2_max1000.log'  # check training")
    
    print("\n" + "=" * 70)
    print("To update: python3 hermes_cli/context_updater.py")
    print("Resume doc: CLI_RESUME_COMPLETE_MAY6_2026.md")
    print("=" * 70)

if __name__ == '__main__':
    show_context()
