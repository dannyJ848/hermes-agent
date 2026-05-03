# Hermes Memory Architecture — Fixed Apr 27, 2026

## What Was Broken

The context was bloating to 2.3MB before any user input, causing:
- "database is locked" SQLite errors
- "context size exceeded 2097152" Kimi API errors
- Complete inability to make tool calls

### Root Causes

| Issue | Before | After |
|-------|--------|-------|
| MEMORY.md | 47.6KB (98 entries) | 1.9KB (18 entries) |
| memory_char_limit | 50000 (config override) | 2500 |
| state.db | 860MB, 146K messages | 69KB, empty |
| Profile memories | 21KB+ each | ~2KB each |
| Memory provider | cerebrum (deprecated) | cortex |

## The Fix — 8 Steps

### 1. Config Fix
- **File**: `~/.hermes/config.yaml` + all profile configs
- **Change**: `memory_char_limit: 50000 → 2500`, `provider: cerebrum → cortex`

### 2. Memory Tool Patch
- **File**: `~/hermes-agent/tools/memory_tool.py`
- **Added**: `_truncate_to_limit()` method enforces char limits at `load_from_disk()` time
- **Effect**: If MEMORY.md exceeds 2500 chars, oldest entries are truncated (not silently injected)

### 3. Memory Slimming
- **Main MEMORY.md**: Reduced from 47.6KB to 1.9KB — kept only essential operational facts
- **Profile memories**: All reduced to < 2500 bytes
- **Backups**: Original saved to `~/.hermes/memory_backups/`

### 4. Cortex Migration
- **92 memory entries** migrated to `cortex_documents` table
  - 45 archived/obsolete (FlashKDA, 35B-A3B, EAGLE-3, etc.)
  - 47 current but non-critical (detailed technical notes)
- **Tags**: `memory_archive`, `dgx-spark`, `hermes`, `speculative-decoding`, etc.

### 5. Session Archiving
- **39 sessions** (2655 messages) archived from old state.db backup
- **Cron job**: `hermes-session-archiver` runs daily at 4 AM
- **Script**: `~/.hermes/scripts/archive_sessions.py`
- Archives sessions older than 7 days to `cortex_documents` with `doc_type='session_archive'`

### 6. State DB Cleanup
- Fresh state.db created from clean backup (Apr 23)
- All messages/sessions truncated
- WAL/shm lock files cleared
- Size: 860MB → 69KB

### 7. Adaptive Injection Verified
- The `build_adaptive_memory_block()` in `run_agent.py` was already active
- Now it filters ~2KB of memory instead of ~47KB
- Relevance scoring + budget enforcement works correctly

### 8. Verification
- API calls succeed without context errors
- Memory files under limit
- State DB small and responsive
- No "database is locked" errors

## New Memory Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  ACTIVE MEMORY (injected every turn)                         │
│  ───────────────────────────────                           │
│  MEMORY.md: ~2KB max (2500 char limit)                     │
│  USER.md: ~1.3KB max (1375 char limit)                   │
│  Profile memories: ~2KB each                               │
│                                                             │
│  Filtered by adaptive_injection.py:                        │
│  - Relevance scoring against current query                 │
│  - Budget enforcement (60% memory, 25% skills)            │
│  - Pressure-aware reduction when context is tight          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  CORTEX LONG-TERM STORAGE (retrieved on demand)              │
│  ─────────────────────────────────────────────              │
│  cortex_documents:                                         │
│  - 92 memory archives (tagged, searchable)                 │
│  - 39 session archives (full conversation history)         │
│                                                             │
│  Retrieved via:                                             │
│  - session_search for past conversations                   │
│  - Cortex query for specific facts                         │
│  - Not injected unless explicitly requested                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  SESSION STATE (ephemeral, auto-archived)                   │
│  ────────────────────────────────────────                   │
│  state.db: ~69KB (current session only)                    │
│  Auto-archived to cortex_documents after 7 days          │
│  by hermes-session-archiver cron job                       │
└─────────────────────────────────────────────────────────────┘
```

## Key Files

| File | Purpose |
|------|---------|
| `~/.hermes/memories/MEMORY.md` | Active agent memory (max 2500 chars) |
| `~/.hermes/memories/USER.md` | User profile (max 1375 chars) |
| `~/.hermes/config.yaml` | Memory limits + provider config |
| `~/hermes-agent/tools/memory_tool.py` | Memory tool with limit enforcement |
| `~/.hermes/scripts/archive_sessions.py` | Session archiver |
| `~/.hermes/memory_backups/` | Pre-fix backups |

## Maintenance

- **Daily**: `hermes-session-archiver` cron job archives old sessions
- **When memory fills up**: Use `memory` tool with `action: remove` to clear old entries
- **To retrieve archived facts**: Use `session_search` or query Cortex directly
- **If context bloat returns**: Check `memory_char_limit` hasn't been overridden

## Backup Locations

- Original 47KB MEMORY.md: `~/.hermes/memories/MEMORY.md.BACKUP_20260427_142910_47KB`
- Original 820MB state.db: `~/.hermes/state.db.BACKUP_20260427_142722_146K_messages`
- Profile backups: `~/.hermes/profiles/*/memories/MEMORY.md.BACKUP_*`
