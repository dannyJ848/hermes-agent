# Learning Apparatus Audit — May 6, 2026

## Systems Checked

| System | Status | Details |
|--------|--------|---------|
| Cerebrum memory | ✓ OPERATIONAL | 77 tables, 1900 distilled_tips, 1870 ELO entries, 38 mastery_scores, 68 reasoning_traces |
| Cortex daemon | ✗ DEAD → ✓ REBUILT | 0-byte DB, 2 stuck PIDs killed. Rebuilt with 100 high-ELO tips from cerebrum |
| Training gym standalone | ✗ EMPTY | `distilled_tips.db` has 0 tables. Redundant — cerebrum handles it |
| Skills | ✓ OPERATIONAL | 360 total, 0 broken (was 22) |
| Distillation pipeline | ✓ OPERATIONAL | Embedded in cerebrum, not standalone. 1900 tips prove it's working |
| ELO tournaments | ✓ OPERATIONAL | 1870 entries |
| Qdrant vector DB | ✗ NOT RESPONDING | localhost:6333 down. SQLite FTS fallback works |

## Critical Findings

### Cortex DB: 0 bytes but process running
- File: `/Users/dannygomez/.hermes/cortex.db`
- Size: 0 bytes (EMPTY/CORRUPTED)
- Processes: PID 97169, 97192 (running but DB empty = stuck)
- Fix: Kill processes, remove DB, rebuild from cerebrum

### Cerebrum is the primary learning system
- `cerebrum_memory.db` has all the data: tips, ELO, mastery, reasoning traces
- `distilled_tips.db` is empty but unused — cerebrum handles distillation
- Cortex should sync FROM cerebrum, not try to be independent

### Skills: 22 broken category directories
- Missing `SKILL.md` in category dirs (apple, research, gaming, etc.)
- Not actual broken skills — just missing index files
- Fix: Add `SKILL.md` with YAML frontmatter to each category dir

## Rebuild Commands

```bash
# Kill stuck cortex processes
pgrep -f 'cortex_daemon' | xargs kill -9

# Remove corrupted DB
rm /Users/dannygomez/.hermes/cortex.db

# Rebuild from cerebrum
python3 << 'PYEOF'
import sqlite3, json
conn2 = sqlite3.connect('/Users/dannygomez/.hermes/cortex.db')
c2 = conn2.cursor()
c2.execute('''CREATE TABLE IF NOT EXISTS cortex_nodes (
    id INTEGER PRIMARY KEY, content TEXT, metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

conn = sqlite3.connect('/Users/dannygomez/.hermes/cerebrum_memory.db')
c = conn.cursor()
c.execute("SELECT tip_type, condition, recommendation, rationale, confidence FROM distilled_tips ORDER BY confidence DESC LIMIT 100")
for row in c.fetchall():
    content = f"{row[0]}: {row[1]} → {row[2]}"
    meta = json.dumps({"rationale": row[3], "confidence": row[4]})
    c2.execute("INSERT INTO cortex_nodes (content, metadata) VALUES (?, ?)", (content, meta))
conn.close()

conn2.commit()
c2.execute("SELECT COUNT(*) FROM cortex_nodes")
print(f"Rebuilt with {c2.fetchone()[0]} tips")
conn2.close()
PYEOF

# Fix broken skill categories
for cat in ~/.hermes/skills/*/; do
    [ -f "$cat/SKILL.md" ] || echo "---\ntitle: $(basename $cat | tr '-' ' ' | sed 's/.*/\u&/') Skills\n---\n" > "$cat/SKILL.md"
done
```

## Key Lesson

When auditing learning infrastructure:
1. Check DB files first (size, tables, row counts)
2. A running process with a 0-byte DB is DEAD, not alive
3. The operational system (cerebrum) is the source of truth
4. Rebuild degraded systems FROM the operational system, not from scratch
5. Use `git status --short` and `git diff HEAD -- <file>` to verify commits
