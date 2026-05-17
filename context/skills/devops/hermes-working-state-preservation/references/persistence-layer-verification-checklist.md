# Persistence Layer Verification Checklist

## Purpose

After updating any Hermes context file (MEMORY.md, SOUL.md, USER.md, MASTER.md, AGENTS.md), verify that ALL persistence layers are consistent and reflect the same system state. This prevents drift where git repo, memory files, and skills disagree about configuration.

## The Rule

> When distilling session state across persistence layers, verify each layer independently: git status, memory files, skills, SOUL.md, MASTER.md, and all context files. Don't assume one success means all succeeded.

## Verification Protocol

### Step 1: Git Repo

```bash
cd ~/hermes-agent
git log --oneline -3
```

Verify:
- [ ] Latest commit reflects the update
- [ ] Working tree is clean (`git status` shows nothing uncommitted)
- [ ] On correct branch

### Step 2: Context Files

```bash
ls -la ~/.hermes/{MEMORY,SOUL,USER,MASTER,AGENTS}.md 2>/dev/null
```

Verify:
- [ ] All expected files exist
- [ ] Timestamps match the update time
- [ ] File sizes are non-zero

### Step 3: Memory Provider

```bash
hermes memory status
```

Verify:
- [ ] Provider name matches config (e.g., `yantrikdb`)
- [ ] Provider reports as active/available
- [ ] Memory count is reasonable (not 0, not corrupted)

### Step 4: Skills

```bash
hermes skills list | tail -3
```

Verify:
- [ ] Skill count matches expected (e.g., 399)
- [ ] No unexpected disabled skills
- [ ] Builtin vs local ratio is reasonable

### Step 5: Plugins

```bash
hermes plugins list | grep -E "enabled|disabled"
```

Verify:
- [ ] Enabled plugin count matches expected
- [ ] Critical plugins (memory provider, cognitive-systems) are enabled
- [ ] No new unexpected disabled plugins

### Step 6: Cron

```bash
hermes cron list | head -5
```

Verify:
- [ ] Job count matches expected
- [ ] Gateway job is active (if applicable)
- [ ] No stale or failed jobs

### Step 7: Doctor

```bash
hermes doctor
```

Verify:
- [ ] Issue count is known/expected (not growing)
- [ ] No new critical issues
- [ ] Memory provider passes check

### Step 8: Cross-Reference

Spot-check 2-3 facts across files:

| Fact | MEMORY.md | SOUL.md | MASTER.md | Git Commit |
|------|-----------|---------|-----------|------------|
| Memory provider | yantrikdb | yantrikdb | yantrikdb | — |
| Skill count | 399 | 399 | 399 | — |
| Python version | 3.11.14 | 3.11.14 | 3.11.14 | — |
| Last commit | 375dcf681 | 375dcf681 | 375dcf681 | 375dcf681 |

If ANY cell disagrees, the layers are inconsistent. Fix before proceeding.

## When to Run

- After any `memory()` tool call that updates context files
- After any skill update that changes system behavior
- After any git commit that changes source code
- Before declaring a task "complete" when multiple files were touched
- After recovering from a crash, restart, or session loss

## Session Reference

- Date: 2026-05-17
- Trigger: User requested full persistence layer update after YantrikDB rebuild
- Files updated: MEMORY.md, SOUL.md, USER.md, MASTER.md (new), MASTER_DOC.md, orphan-alias skill
- Verification result: All layers consistent, 2 git commits made, doctor shows 3 optional issues
- Status: ✅ COMPLETED — all layers verified consistent
