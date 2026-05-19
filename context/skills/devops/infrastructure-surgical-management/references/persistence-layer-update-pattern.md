# Persistence Layer Update Pattern

## Purpose

When the user requests updating "all persistence layers" or "sync everything", this is a systematic protocol for ensuring all Hermes state files (MEMORY.md, SOUL.md, USER.md, MASTER.md, AGENTS.md) reflect the current system configuration, and that the git repo captures these changes.

## Trigger

- User says "update all persistence layers"
- User says "sync everything" or "make everything consistent"
- After major system changes (memory provider switch, plugin updates, skill mass-updates)
- After recovery from session loss or crash

## The Protocol

### Phase 1: Audit Current State

```bash
# Get system state
hermes doctor 2>&1 | grep -E "(Found|issue|memory|yantrik|skill|plugin)"
hermes skills list 2>&1 | tail -3
hermes plugins list 2>&1 | grep -E "enabled|disabled" | wc -l
hermes cron list 2>&1 | head -5
hermes memory status 2>&1 | head -5
```

Record:
- Memory provider name and status
- Skill count (builtin vs local)
- Plugin count (enabled vs disabled)
- Cron job count
- Doctor issue count and severity
- Git branch and last commit

### Phase 2: Update Each Context File

Update files in this order (dependencies flow downward):

1. **MEMORY.md** — Raw system state, counts, provider details, file paths
2. **SOUL.md** — Persona, learned behaviors, capabilities, constraints
3. **USER.md** — User preferences, environment details, constraints
4. **MASTER.md** (or MASTER_DOC.md) — Master reference, system topology
5. **AGENTS.md** — Agent behavior rules, red lines, conventions

For each file:
- Read current content
- Identify stale facts (old counts, old providers, old paths)
- Update with current audit results
- Add new learned behaviors from the session
- Remove outdated constraints that no longer apply

### Phase 3: Update Referenced Skills

Find skills that reference the old state and patch them:

```bash
# Find stale references
grep -rn "old_provider_name\|old_skill_count\|old_commit_hash" ~/.hermes/skills/ 2>/dev/null | head -20

# Update each found file
```

Common stale references:
- Old memory provider names (cerebrum → yantrikdb)
- Old skill counts (289 → 399)
- Old commit hashes
- Old profile names (soma-* aliases)
- Old Python versions

### Phase 4: Git Commit

```bash
cd ~/hermes-agent
git add -A
git status --short  # Verify what's staged
git commit -m "docs: Update all persistence layers for <date> state

Updated context files to reflect current system configuration:
- MEMORY.md: <key facts>
- SOUL.md: <key additions>
- USER.md: <key constraints>
- MASTER.md: <key references>
- Skills: <which skills updated>

System state:
- <N> skills (<builtin> builtin, <local> local)
- <N> plugins enabled, <N> disabled
- Memory: <provider> active
- Cron: <N> jobs

Refs: persistence-layer-update-<date>"
```

### Phase 5: Verification

Run the full verification checklist from `hermes-working-state-preservation/references/persistence-layer-verification-checklist.md`:

1. Git repo shows clean working tree, correct commit
2. All context files exist with matching timestamps
3. Memory provider matches config
4. Skill count matches across all files
5. Plugin count matches
6. Cron jobs active
7. Doctor issues are known/expected
8. Cross-reference 2-3 facts across all files — no disagreements

## Anti-Patterns

| Anti-Pattern | Why It's Wrong | Correct Approach |
|-------------|---------------|------------------|
| Update only MEMORY.md | SOUL.md and USER.md still reference old state | Update ALL files in dependency order |
| Assume git will auto-commit context files | ~/.hermes/*.md are usually gitignored | Explicitly add with `git add -f` or ensure they're tracked |
| Skip verification | Drift goes undetected until next session | Always run the 8-step verification |
| Update files but don't commit | Changes lost on next session | Commit immediately after updates |
| Only update counts, not learned behaviors | SOUL.md loses session insights | Add new learned behaviors to SOUL.md |

## Session Reference

- Date: 2026-05-17
- Trigger: User requested full persistence layer update after YantrikDB rebuild
- Files updated: MEMORY.md, SOUL.md, USER.md, MASTER.md (new), MASTER_DOC.md
- Skills updated: orphan-alias-cleanup (marked completed), yantrikdb-integration (marked completed)
- Git commits: 2 (YantrikDB fix + MASTER_DOC.md update)
- Verification: All layers consistent, doctor shows 3 optional issues
- Status: ✅ COMPLETED
