#!/usr/bin/env python3
# Unified Context System Setup
# Creates centralized persistence for instant CLI context

import os
import sqlite3
import json
from datetime import datetime

print("=" * 70)
print("UNIFIED CONTEXT SYSTEM — SETUP")
print("=" * 70)

os.chdir('/Users/dannygomez/hermes-agent')

# Create unified context database
conn = sqlite3.connect('/Users/dannygomez/.hermes/unified_context.db')
c = conn.cursor()

# Master context table
c.execute('''
    CREATE TABLE IF NOT EXISTS cli_context (
        key TEXT PRIMARY KEY,
        category TEXT,
        value TEXT,
        priority INTEGER DEFAULT 5,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Tool intelligence snapshot
c.execute('''
    CREATE TABLE IF NOT EXISTS tool_intelligence_snapshot (
        tool_name TEXT PRIMARY KEY,
        success_rate REAL,
        total_calls INTEGER,
        avg_latency_ms REAL,
        circuit_state TEXT,
        last_failure TEXT,
        recommendation TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Session continuity
c.execute('''
    CREATE TABLE IF NOT EXISTS session_continuity (
        session_id TEXT PRIMARY KEY,
        start_time TIMESTAMP,
        last_activity TIMESTAMP,
        active_tasks TEXT,
        decisions_made TEXT,
        files_modified TEXT,
        status TEXT
    )
''')

# Error registry
c.execute('''
    CREATE TABLE IF NOT EXISTS error_registry (
        signature TEXT PRIMARY KEY,
        tool_name TEXT,
        root_cause TEXT,
        fix TEXT,
        occurrences INTEGER DEFAULT 1,
        first_seen TIMESTAMP,
        last_seen TIMESTAMP
    )
''')

conn.commit()

# Seed tool intelligence
tool_data = [
    ('cronjob', 0.13, 31, 250, 'OPEN', 'recent', 'Use terminal crontab or python schedule'),
    ('skill_manage', 0.51, 380, 300, 'OPEN', 'recent', 'Use write_file for SKILL.md'),
    ('patch', 0.59, 402, 1500, 'OPEN', 'recent', 'Verify uniqueness, use write_file fallback'),
    ('write_file', 0.87, 500, 150, 'CLOSED', None, 'Primary file tool'),
    ('execute_code', 0.93, 600, 800, 'CLOSED', 'SyntaxError', 'Use write_file for multi-line strings'),
    ('web_extract', 0.94, 200, 2000, 'CLOSED', None, 'Primary web tool'),
    ('browser_console', 0.95, 100, 300, 'CLOSED', None, 'Primary browser tool'),
    ('web_search', 0.96, 300, 500, 'CLOSED', None, 'Primary search tool'),
]

for tool, rate, calls, latency, state, last_fail, rec in tool_data:
    c.execute('''
        INSERT OR REPLACE INTO tool_intelligence_snapshot
        (tool_name, success_rate, total_calls, avg_latency_ms, circuit_state, last_failure, recommendation)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (tool, rate, calls, latency, state, last_fail, rec))

# Seed recent errors
errors = [
    ('unterminated string literal', 'execute_code', 'string_quoting', 'Escape quotes or use write_file'),
    ('IndentationError: unexpected indent', 'execute_code', 'code_formatting', 'Use write_file for multi-line code'),
    ('old_string and new_string are identical', 'patch', 'patch_logic', 'Verify old_string uniqueness'),
]

for sig, tool, cause, fix in errors:
    c.execute('''
        INSERT OR REPLACE INTO error_registry
        (signature, tool_name, root_cause, fix, occurrences, first_seen, last_seen)
        VALUES (?, ?, ?, ?, 1, datetime('now'), datetime('now'))
    ''', (sig, tool, cause, fix))

# Seed context entries
context_entries = [
    ('training_pid', 'training', '590094', 1),
    ('training_step', 'training', '0/4000', 1),
    ('training_status', 'training', 'running', 1),
    ('training_eta', 'training', '~33 hours', 2),
    ('branch', 'git', 'qwen27b-training-artifacts-may3-2026', 1),
    ('upstream_behind', 'git', '169 commits', 3),
    ('deepseek_judge', 'judge', 'deepseek-v4-pro active', 1),
    ('heuristic_alignment', 'judge', '85%', 2),
    ('cortex_tips', 'memory', '1900', 2),
    ('cortex_tables', 'memory', '88', 3),
    ('last_commit', 'git', '8974a9bbb', 2),
    ('cli_resume', 'docs', 'CLI_RESUME_MAY6_2026.md', 1),
]

for key, cat, val, pri in context_entries:
    c.execute('''
        INSERT OR REPLACE INTO cli_context (key, category, value, priority)
        VALUES (?, ?, ?, ?)
    ''', (key, cat, val, pri))

# Seed session continuity
session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
c.execute('''
    INSERT OR REPLACE INTO session_continuity
    (session_id, start_time, last_activity, active_tasks, decisions_made, files_modified, status)
    VALUES (?, datetime('now'), datetime('now'), ?, ?, ?, 'active')
''', (
    session_id,
    json.dumps(['Qwen 27B training restart', 'Hermes source enhancement', 'Self-improvement cycle']),
    json.dumps(['Use write_file over patch', 'Centralize subconscious', 'Build loop guard']),
    json.dumps(['hermes_cli/subconscious/', 'hermes_cli/hermes_brain.py', 'hermes_cli/loop_guard.py'])
))

conn.commit()

# Verify
c.execute("SELECT COUNT(*) FROM tool_intelligence_snapshot")
tool_count = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM error_registry")
error_count = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM cli_context")
ctx_count = c.fetchone()[0]

print(f"\n✓ tool_intelligence_snapshot: {tool_count} entries")
print(f"✓ error_registry: {error_count} entries")
print(f"✓ cli_context: {ctx_count} entries")

conn.close()

print("\n" + "=" * 70)
print("DATABASE READY: ~/.hermes/unified_context.db")
print("=" * 70)
