---
name: epistemic-memory-cleanup
description: Audit and purge speculative/ungrounded facts from cerebrum semantic memory. Restore epistemic quality to 95%+ grounded.
version: 2.0
created: 2026-04-05
trigger: User says "fix epistemic quality", "clean up memory", "too much speculation", or when semantic_facts grounded % drops below 80%.
---

# Epistemic Memory Cleanup

Periodic maintenance skill for purging model-generated speculation from the cerebrum knowledge base and enforcing trust ceilings.

## Phase 1: Audit Current State

```python
# Connect to cerebrum DB
import sqlite3
conn = sqlite3.connect(str(Path.home() / ".hermes" / "cerebrum_memory.db"))
c = conn.cursor()

# 1. Trust distribution
c.execute("""
    SELECT CASE
        WHEN trust >= 0.8 THEN 'grounded (0.8+)'
        WHEN trust >= 0.6 THEN 'likely (0.6-0.8)'
        WHEN trust >= 0.4 THEN 'uncertain (0.4-0.6)'
        ELSE 'speculative (<0.4)'
    END as tier, COUNT(*)
    FROM semantic_facts GROUP BY tier ORDER BY MIN(trust) DESC
""")

# 2. By provenance
c.execute("SELECT provenance, COUNT(*), AVG(trust) FROM semantic_facts GROUP BY provenance ORDER BY COUNT(*) DESC")

# 3. By category
c.execute("SELECT category, COUNT(*), AVG(trust) FROM semantic_facts GROUP BY category ORDER BY COUNT(*) DESC")

# 4. Count explicit speculation
c.execute("""SELECT COUNT(*) FROM semantic_facts
    WHERE content LIKE '%INTUITION%' OR content LIKE '%DREAM%'
    OR content LIKE '%HYPOTHESIS%' OR content LIKE '%USER UNDERSTANDING%'""")

# 5. Total
c.execute("SELECT COUNT(*) FROM semantic_facts")
```

## Phase 2: Identify and Delete Pollution

### Always-Delete Categories (model-generated speculation)

```python
# These categories are ALWAYS speculative — delete on sight
for cat in ['connection', 'synthesis', 'intuition']:
    c.execute('DELETE FROM semantic_facts WHERE category = ?', (cat,))

# Brain-generated "USER UNDERSTANDING" = hallucinations
c.execute("DELETE FROM semantic_facts WHERE content LIKE 'USER UNDERSTANDING%' AND provenance LIKE '%brain%'")

# All remaining brain-generated non-preference facts
c.execute("DELETE FROM semantic_facts WHERE provenance LIKE '%brain%' AND category != 'user_pref' AND trust < 0.5")

# Null provenance + low trust = no attribution = ungrounded
c.execute("DELETE FROM semantic_facts WHERE (provenance IS NULL OR provenance = '') AND trust < 0.5")

# Explicitly speculative content
c.execute("DELETE FROM semantic_facts WHERE content LIKE '%INTUITION%' AND trust < 0.5")
```

### Backup First

```python
import shutil
shutil.copy2(
    str(Path.home() / ".hermes" / "cerebrum_memory.db"),
    str(Path.home() / ".hermes" / "cerebrum_memory.db.pre_cleanup_backup")
)
```

## Phase 3: Boost Verified Facts

```python
# Sourced research WITH URLs -> 0.80
c.execute("""UPDATE semantic_facts SET trust = 0.80
    WHERE category IN ('project', 'medical', 'research')
    AND content LIKE '%http%'
    AND provenance = 'knowledge-migration' AND trust < 0.80""")

# Project facts with code references -> 0.75
c.execute("""UPDATE semantic_facts SET trust = 0.75
    WHERE category = 'project' AND provenance = 'knowledge-migration'
    AND (content LIKE '%.ts' OR content LIKE '%.py' OR content LIKE '%import%')
    AND trust < 0.75""")

# Episodic consolidation (verified experience) -> 0.90
c.execute("UPDATE semantic_facts SET trust = 0.90 WHERE provenance = 'episodic_consolidation' AND trust < 0.90")

# Memory migration (old grounded memory) -> 0.75
c.execute("UPDATE semantic_facts SET trust = 0.75 WHERE provenance IN ('memory-migration', 'profile-migration') AND trust < 0.75")

# User preferences -> 0.85
c.execute("UPDATE semantic_facts SET trust = 0.85 WHERE category = 'user_pref' AND trust < 0.85")

# Tool facts -> 0.75
c.execute("UPDATE semantic_facts SET trust = 0.75 WHERE category = 'tool' AND trust < 0.75")

# Honcho dialectic (operational knowledge) -> 0.75
c.execute("UPDATE semantic_facts SET trust = 0.75 WHERE provenance = 'honcho-migration' AND trust < 0.75")

# Medical facts -> 0.75
c.execute("UPDATE semantic_facts SET trust = 0.75 WHERE category = 'medical' AND trust < 0.75")

# Remaining knowledge-migration project facts -> 0.80
c.execute("UPDATE semantic_facts SET trust = 0.80 WHERE category = 'project' AND provenance = 'knowledge-migration' AND trust < 0.80")

conn.commit()
```

## Phase 4: Patch the Pollution Source

The brain (parallel_brain.py) has 3 INSERT paths that historically polluted semantic_facts. ALL should be REMOVED (not guarded — removed). Search for and remove:

1. **RESEARCH insights** — ~line 706-717 area. Model-generated research gets stored directly. Replace with: just return insights, don't store.
2. **CONNECTION facts** — in `synthesize()` method. Replace the entire loop with a comment explaining the epistemic policy.
3. **SYNTHESIS facts** — also in `synthesize()`. Same treatment.

The key principle: **Remove the INSERT statements, don't add guards.** Guards can be bypassed; removal can't.

After patching, verify:
```bash
cd ~/subconscious && python3 -c "
import ast
with open('parallel_brain.py') as f:
    ast.parse(f.read())
print('Syntax OK')
content = f.read()  # re-read
print('Remaining INSERT INTO semantic_facts:', content.count('INSERT INTO semantic_facts'))
"
# Should print: Syntax OK, Remaining INSERT INTO semantic_facts: 0
```

## Phase 5: Verify

```python
# Zero checks — all must be 0
c.execute("SELECT COUNT(*) FROM semantic_facts WHERE category IN ('connection', 'synthesis', 'intuition')")
blocklisted = c.fetchone()[0]  # MUST be 0

c.execute("SELECT COUNT(*) FROM semantic_facts WHERE trust < 0.5")
low_trust = c.fetchone()[0]  # MUST be 0

c.execute("SELECT COUNT(*) FROM semantic_facts WHERE provenance LIKE '%brain%'")
brain = c.fetchone()[0]  # MUST be 0

# Grounded check
c.execute("SELECT COUNT(*) FROM semantic_facts WHERE trust >= 0.6")
grounded = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM semantic_facts")
total = c.fetchone()[0]
pct = grounded / total * 100  # MUST be >= 95%
```

## Trust Hierarchy (Epistemic Policy)

| Source | Trust Ceiling | Why |
|--------|--------------|-----|
| episodic_consolidation | 0.90 | Verified experience |
| user_pref | 0.85 | Danny's actual words |
| knowledge-migration + URL | 0.80 | Sourced research |
| project (technical) | 0.80 | Code-verified knowledge |
| memory-migration | 0.75 | Old system, grounded |
| honcho-migration | 0.75 | Operational knowledge |
| knowledge-migration (no URL) | 0.70 | Research without sources |
| model-generate | 0.30 | Never store in semantic_facts |
| intuition/connection/synthesis | 0.00 | DELETE on sight |

## Pitfalls

1. **Don't trust trust scores blindly** — the brain assigned trust=0.24 to actual sourced research with URLs. Always cross-check content quality, not just the number.
2. **knowledge-migration without URLs isn't always bad** — some are legitimate internal knowledge. Check content before deleting.
3. **"USER UNDERSTANDING" facts are ALWAYS hallucinations** — the model has no ground truth about the user. Delete all of these.
4. **Backup before deleting** — use `.pre_cleanup_backup` suffix.
5. **Verify syntax after patching parallel_brain.py** — `ast.parse()` check, not the patch tool's built-in checker (it has phantom ES5 errors).
6. **The brain will try to re-pollute** — the patch must REMOVE the INSERT statements, not just add guard checks. Guards can be bypassed; removal can't.
7. **Use venv Python for testing** — system Python 3.8 will fail on 3.10+ syntax. Always use `/Users/dannygomez/hermes-agent/venv/bin/python3`.
8. **DB column names** — cerebrum uses `trust` (not `trust_score`), `provenance` (not `source`). Check PRAGMA table_info before querying.

## Cadence

Run when:
- User requests it
- Grounded % drops below 80% (check via cron or controller)
- After major brain architecture changes (new brain cycles may add new INSERT paths)
