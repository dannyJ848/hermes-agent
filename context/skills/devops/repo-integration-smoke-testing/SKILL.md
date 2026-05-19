---
name: repo-integration-smoke-testing
description: Systematic smoke-testing workflow for verifying that integrated third-party skill/plugin repositories are actually functional after installation. Use after bulk skill/plugin ingestion (HermesHub, Superpowers, Obsidian, etc.) or when user asks "test them" or "are they working".
trigger: When user asks to test, verify, smoke-test, or check if integrated repos/skills/plugins are working after installation.
category: devops
---

# Repo Integration Smoke Testing

After bulk-ingesting skills and plugins from community repos, verify they actually work — not just that files exist on disk.

## When to Use

- After `git clone` + copy of multiple skill/plugin repos
- When user says "test them", "smoke test", "are they working"
- After Hermes version update that might break skill compatibility
- Before declaring integration complete

## The Three-Layer Verification Protocol

### Layer 1: Skill Discovery (File System)

Verify skills are in the right place and Hermes sees them:

```bash
# Count skills by source prefix
ls ~/.hermes/skills | grep "^hermeshub" | wc -l   # hermeshub skills
ls ~/.hermes/skills | grep "^superpowers" | wc -l  # superpowers skills
ls ~/.hermes/skills | grep "^obsidian" | wc -l     # obsidian skills

# Verify Hermes registry sees them
hermes skills list | grep -E "hermeshub|superpowers|obsidian" | wc -l
```

**Pass criteria:** File count matches registry count, all show `enabled`.

### Layer 2: Skill Content Loading (Runtime)

Pick representative skills from each repo and load them:

```bash
# Test skill_view() on 1-2 skills per repo
hermes skill view api-builder           # hermeshub
hermes skill view brainstorming         # superpowers
hermes skill view defuddle             # obsidian
```

**Pass criteria:** `skill_view()` returns full SKILL.md content without errors, `readiness_status: available`.

### Layer 3: Plugin Build + API Test (Execution)

For TypeScript/Python plugins, verify they compile and core APIs work:

```bash
# TypeScript plugin: typecheck
cd ~/.hermes/plugins/paperclip-adapter && npm run typecheck
# Pass: exits 0, no type errors

# Python plugin: runtime test
PYTHONPATH=src python3 -c "
from yantrikdb import YantrikDB
db = YantrikDB.with_default('/tmp/test_yantrik.db')
db.record('test memory', importance=0.5)
result = db.recall('test', top_k=1)
assert len(result) == 1, 'recall failed'
db.close()
print('YantrikDB OK')
"
# Pass: prints "YantrikDB OK", no exceptions
```

### Layer 3b: Hermes Plugin Registry Verification

**Critical:** A plugin can pass Layer 3 (Python import works, APIs functional) but still not be registered as a Hermes plugin. Verify registration:

```bash
# Check if Hermes sees the plugin
hermes plugins list | grep -E "yantrikdb|paperclip"
# Fail: no output means the plugin exists on disk but isn't registered

# Check plugin directory vs registry count
ls ~/.hermes/plugins/ | wc -l          # 46 plugin directories
hermes plugins list | grep "^│" | wc -l  # 268 registered plugins
# If directory count >> registry count for your repos, registration failed
```

**Registration failure causes:**
- Missing `plugin.yaml` or malformed plugin manifest
- Plugin not in Hermes' plugin search path
- Python version mismatch (plugin requires Python 3.11, Hermes runs 3.9)
- Missing `__init__.py` or entry point not discoverable
- Plugin dependencies not installed in Hermes' environment

**Fix:** Check `~/.hermes/logs/plugin-loader.log` or run `hermes plugins list --debug` for registration errors.

## The Smoke Test Report

After testing, produce a summary table:

| Repo | Component | Test | Result |
|------|-----------|------|--------|
| hermeshub | api-builder skill | skill_view() | ✅ OK |
| hermeshub | scrapling skill | skill_view() | ✅ OK |
| superpowers | brainstorming skill | skill_view() | ✅ OK |
| obsidian | defuddle skill | skill_view() | ✅ OK |
| paperclip-adapter | Plugin | npm run typecheck | ✅ Pass |
| yantrikdb | Plugin | record/recall/close | ✅ OK |

**All repos verified functional.**

## Anti-Patterns

- **Only checking file existence:** `ls ~/.hermes/skills/` is not enough — a skill with malformed YAML frontmatter won't load
- **Skipping plugin build step:** TypeScript plugins with `dist/` missing will fail at runtime even if files exist
- **Not testing recall after record:** YantrikDB's async queue means `record()` may succeed but `recall()` returns nothing until `think()` flushes
- **Assuming directory presence = plugin registration:** A plugin in `~/.hermes/plugins/yantrikdb/` may import fine via `PYTHONPATH=src python3 -c "import yantrikdb"` but still not appear in `hermes plugins list`. Always verify Layer 3b (registry check).
- **Testing all skills individually:** For 50+ skills, spot-check 1-2 per repo — full enumeration is unnecessary

## Related

- `hermes-working-state-preservation` — Capture working state after successful integration
- `yantrikdb-integration` — Deep dive on YantrikDB queue management and migration patterns
- `hermes-hub-integration-pattern` (in working-state-preservation references) — Bulk ingestion protocol

## References

- `references/session-2026-05-16-smoke-test-commands.md` — Exact commands and results from the 5-repo smoke test session
- `references/session-2026-05-17-yantrikdb-migration-findings.md` — YantrikDB ingest queue bug, `record_batch()` signature, SQLite parameter limit, and plugin registration gap discovered during cerebrum→YantrikDB migration
- `references/persistence-update-workflow.md` — Five-layer protocol for updating SOUL.md, MEMORY.md, git, memory, and checkpoints after major state changes
