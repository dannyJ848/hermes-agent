# Persistence Update Workflow — After Major State Changes

## Context
User asked: "update all persistence layers and memory, master doc, skills, my github repo, soul md, and all other relevant context sources for the new cli"

## The Five-Layer Update Protocol

When Hermes state changes significantly (version update, bulk repo integration, config fix), update ALL persistence layers in this order:

### 1. SOUL.md — Learned Behaviors
Add new behavioral rules at the bottom of the `## Learned Behaviors` section:
```
- When [new pattern], [action]. (YYYY-MM-DD)
```

Examples from this session:
- When the YantrikDB ingest queue fills during bulk memory migration, use `record_batch()` with chunk sizes of 50-100 and call `think()` every 5 chunks to flush the queue. (2026-05-16)
- When smoke-testing integrated repos, verify skills load via `skill_view()`, plugins compile (`npm run typecheck`), and core APIs work (`record()`/`recall()`/`close()`). (2026-05-16)

### 2. MEMORY.md — Curated Long-Term Memory
Update sections:
- **Active Projects** — add new integrations, remove completed ones
- **Current State** — version numbers, counts, stale warnings
- **Key Lessons** — new pitfalls discovered

Example additions:
```markdown
## Hermes v0.13.0 (May 16 2026)
- 396 skills enabled (78 builtin, 318 local)
- 37 plugins enabled, 3 optional disabled
- Cron jobs stale since 2026-04-22
- 5 repos integrated and smoke-tested
```

### 3. Git Commit — Versioned History
```bash
git -C ~/.hermes add -A
git -C ~/.hermes commit -m "Update persistence: SOUL.md, MEMORY.md for [reason]"
```
Note: May include many files (15,030 in this session due to browser-profile cache).

### 4. Memory (Cortex) — Session-Spanning Facts
Replace or add entries in the active memory store:
```
Hermes v0.13.0 state (May 16 2026): 396 skills, 37 plugins, 5 repos integrated...
```
If memory is full (2,500 char limit), replace the least critical existing entry.

### 5. Session Checkpoint — Immediate Recovery
```bash
session_checkpoint(label="persistence-update-[date]", context="...", next_steps="...")
```
Saves to `~/.hermes/workspace/checkpoints/[label].json`

## Verification
After updating all layers, confirm:
- [ ] SOUL.md has new behaviors with dates
- [ ] MEMORY.md reflects current state
- [ ] Git commit succeeded
- [ ] Memory updated (check `memory` tool response)
- [ ] Checkpoint saved

## Pitfalls
- **Git commit includes browser cache:** The `browser-profile/` directory under `~/.hermes/` contains Chrome cache files that get added by `git add -A`. This bloats commits. Consider adding `browser-profile/` to `.gitignore`.
- **Memory full:** At 2,500 char limit, new entries fail. Replace oldest/least critical entry instead of adding.
- **Forgetting one layer:** Don't assume git commit covers everything — memory and checkpoints are separate systems.
