# Learning Apparatus Enhancements — May 6, 2026

## Session Context

During a comprehensive audit of the learning apparatus, 6 new tracking tables were created in `cerebrum_memory.db` to improve tip quality, tool routing, and cross-domain learning.

## New Tables Created

### 1. elo_k_factor — Adaptive ELO Rating

**Purpose:** Faster tip stabilization for new tips.

**Schema:**
```sql
CREATE TABLE elo_k_factor (
    tip_id INTEGER PRIMARY KEY,
    matches_played INTEGER DEFAULT 0,
    current_k REAL DEFAULT 40.0,
    FOREIGN KEY (tip_id) REFERENCES tip_elo(tip_id)
);
```

**Rule:** K=40 for first 10 matches, K=20 after. Applied to all 1870 existing tips.

**Benefit:** New tips reach stable ELO 2x faster. Bad tips get identified and demoted quickly.

### 2. tool_mastery — Per-Tool Skill Tracking

**Purpose:** Route tasks to tools based on proven mastery, not just availability.

**Schema:**
```sql
CREATE TABLE tool_mastery (
    tool_name TEXT PRIMARY KEY,
    tips_count INTEGER DEFAULT 0,
    avg_elo REAL DEFAULT 1500,
    success_rate REAL DEFAULT 0.5,
    last_used TIMESTAMP,
    mastery_level TEXT DEFAULT 'novice'
);
```

**Seeded with:** 167 tools from existing distilled_tips.

**Benefit:** When multiple tools could handle a task, pick the one with highest `avg_elo` and `success_rate`.

### 3. recovery_tips — Failure-to-Success Pipeline

**Purpose:** Learn from mistakes by linking error patterns to recovery strategies.

**Schema:**
```sql
CREATE TABLE recovery_tips (
    id INTEGER PRIMARY KEY,
    error_pattern_id INTEGER,
    recovery_tip_id INTEGER,
    recovery_success_rate REAL DEFAULT 0.0,
    applications INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Usage:** When an error_occurrence is followed by successful recovery, record which tip was used. Over time, build a "error → fix" mapping.

### 4. domain_transfers — Cross-Domain Pattern Recognition

**Purpose:** Track when tips from one domain succeed in another.

**Schema:**
```sql
CREATE TABLE domain_transfers (
    id INTEGER PRIMARY KEY,
    tip_id INTEGER,
    source_domain TEXT,
    target_domain TEXT,
    transfer_successes INTEGER DEFAULT 0,
    transfer_attempts INTEGER DEFAULT 0,
    transfer_score REAL DEFAULT 0.0,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Example transfer:** "GUI visual grounding techniques → 3D anatomy interaction" (discovered April 7, 2026).

**Benefit:** Cross-pollinate insights. A tip about raycasting precision in game dev might improve medical 3D viewer click targeting.

### 5. compression_quality — Session Context Optimization

**Purpose:** Track whether context compression helps or hurts outcomes.

**Schema:**
```sql
CREATE TABLE compression_quality (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    original_tokens INTEGER,
    compressed_tokens INTEGER,
    compression_ratio REAL,
    outcome_score REAL,
    tool_success_rate REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Usage:** When LCM compression reduces token usage, record whether the compressed session still achieves the goal. Over time, learn optimal compression thresholds.

### 6. tip_velocity — Learning Rate Monitor

**Purpose:** Track daily tip creation rate to monitor learning speed.

**Schema:**
```sql
CREATE TABLE tip_velocity (
    id INTEGER PRIMARY KEY,
    date TEXT UNIQUE,
    tips_created INTEGER DEFAULT 0,
    tips_distilled INTEGER DEFAULT 0,
    avg_elo_new REAL DEFAULT 1500
);
```

**Backfilled:** 14 days of history from existing `distilled_tips.created_at`.

**Benefit:** Detect learning slowdowns. If velocity drops, investigate whether the distillation pipeline is stuck or the session context is too repetitive.

## Implementation Pattern

All tables were created using `execute_code` with sqlite3 (93% success tool) rather than `skill_manage` (49% success). This is the recommended pattern for database schema changes:

```python
import sqlite3
conn = sqlite3.connect('/Users/dannygomez/.hermes/cerebrum_memory.db')
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS new_table (...)")
conn.commit()
conn.close()
```

## Verification

```bash
sqlite3 /Users/dannygomez/.hermes/cerebrum_memory.db ".tables" | grep -E "elo_k_factor|tool_mastery|recovery_tips|domain_transfers|compression_quality|tip_velocity"
```

Expected output: all 6 table names.
