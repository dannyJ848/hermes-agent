# YantrikDB SQLite IN Clause Limit — Reference

## Problem

`YantrikDB.recall()` internally generates SQL like:

```sql
SELECT rid, embedding FROM memories WHERE rid IN (?1, ?2, ?3, ..., ?N)
```

When the database has many records and `top_k` is large, the `IN` clause exceeds SQLite's maximum parameter count of **32,766 variables**.

## Error Message

```
RuntimeError: database error: variable number must be between ?1 and ?32766
in SELECT rid, embedding FROM memories WHERE rid IN (?1,?2,?3,...
```

## When It Happens

- Database has 25,000+ records
- `recall(query, top_k=2000)` is called
- The internal query tries to bind 29,000+ parameters
- SQLite rejects the query before execution

## Workaround

Use `top_k <= 500` for large databases:

```python
# Safe for databases with 30,000+ records
results = db.recall('query', namespace='cerebrum_tips', top_k=500)

# For counting all records in a namespace, use direct SQLite:
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM memories WHERE namespace = ?", ('cerebrum_tips',))
count = c.fetchone()[0]
conn.close()
```

## Verification

```python
from yantrikdb import YantrikDB

db = YantrikDB.with_default('~/.hermes/yantrikdb_copy.db')

# This works (small top_k)
result = db.recall('', namespace='cerebrum_tips', top_k=100)
print(f'Found {len(result)}')

# This fails on large databases (IN clause too long)
# result = db.recall('', namespace='cerebrum_tips', top_k=2000)
# → RuntimeError: variable number must be between ?1 and ?32766
```

## Related

- SQLite limits: https://www.sqlite.org/limits.html (Maximum Number Of Host Parameters In A Single SQL Statement)
- `yantrikdb-integration/SKILL.md` — Main skill
