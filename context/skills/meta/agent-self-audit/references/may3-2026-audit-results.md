# May 3, 2026 Self-Audit Results — Full Session Transcript

## Session Context
User asked for a full self-audit of the learning apparatus after a Qwen 27B training session. The audit revealed the daemon had been offline for 10+ days and 76.6% of modules were orphaned.

## Live Metrics Captured

### Cortex Database
| Metric | Value |
|--------|-------|
| Total nodes | 66,310 |
| Tips (all time) | 6,971 |
| Active tips | 2,405 (34.5% survival) |
| Deactivated | 4,566 (65.5%) |
| Total edges | 369,260 |
| Evaluations | 203,045 |
| Flywheel cycles | 7,801 |

### Tip Quality
| Metric | Value |
|--------|-------|
| Avg Elo | 1,337 |
| Elo std | 341 |
| Elo range | 1,057 - 3,122 |
| Avg confidence | 0.55 (general domain) |
| Deep rated (10+ matches) | 4,991 (71.6%) |
| High quality (Elo≥1300, 10+ matches) | 474 (6.8%) |

### Domain Balance
| Domain | Tips | Avg Elo | Avg Conf | Quality |
|--------|------|---------|----------|---------|
| general | 2,181 | 1,295 | 0.55 | AVERAGE |
| reasoning | 54 | 1,903 | 0.89 | EXCELLENT |
| planning | 39 | 1,619 | 0.79 | GOOD |
| coding | 33 | 1,962 | 0.91 | EXCELLENT |
| agent_evaluation | 28 | 1,834 | 0.89 | EXCELLENT |
| memory | 21 | 1,401 | 0.82 | AVERAGE |
| training | 21 | 1,468 | 0.86 | AVERAGE |
| tool_use | 13 | 2,078 | 0.95 | EXCELLENT |
| meta | 11 | 1,380 | 0.83 | AVERAGE |
| agent_architecture | 4 | 1,422 | 0.82 | AVERAGE |

### Daemon Status
| Metric | Value |
|--------|-------|
| Process running | NO |
| Last flywheel cycle | Apr 22, 2026 21:02 (256 hours ago) |
| Log files | NONE |
| Tip queue | EMPTY |

### Module Wiring
| Metric | Value |
|--------|-------|
| Total .py files | 529 |
| Unique imports in plugin | 134 |
| Wired modules | 124 (23.4%) |
| Orphaned modules | 405 (76.6%) |

### Distillation Plugin
| Metric | Value |
|--------|-------|
| Plugin lines | 3,099 |
| Module imports | 163 |
| Injection hooks | 226 |
| R-rounds wired | 101 (R34-R270) |

### Hermes Repo
| Metric | Value |
|--------|-------|
| Current version | v0.11.0 (Apr 23, 2026) |
| Commits behind origin/main | 247 |
| Local commits ahead | 24 |
| Last local commit | May 1, 2026 (038ea76bc) |

### Skills Ecosystem
| Metric | Value |
|--------|-------|
| Total skills | 349 |
| Categories | 28 |
| Largest category | software-development (62) |

## Key Findings

1. **Daemon offline 10+ days** — continuous learning completely stopped
2. **405 orphaned modules** — 76.6% of built modules never wired into plugin
3. **Domain severely skewed** — 90.7% of active tips in "general" with low confidence
4. **Hermes 247 commits behind** — missing upstream fixes and features
5. **No recent benchmarks** — no testing_gym runs to prove tip effectiveness

## Tip Creation Timeline
```
Apr 12: +1,934 tips (burst)
Apr 13: +247 tips
Apr 14: +292 tips
Apr 15: +1,199 tips (burst)
Apr 16: +122 tips
Apr 17: +232 tips
Apr 18: +425 tips
Apr 19: +655 tips
Apr 20: +403 tips
Apr 21+: 0 tips (daemon dead)
```

## Action Items Generated
1. Restart cortex daemon
2. Bulk wire top 50 orphaned modules
3. Reclassify 500+ "general" tips
4. Update Hermes (git fetch && merge)
5. Run testing_gym benchmark suite

## Query Patterns Used

### Check daemon process
```bash
pgrep -f cortex_daemon
```

### Check flywheel cycles
```sql
SELECT COUNT(*), MAX(started_at) FROM cortex_flywheel;
```

### Check module wiring
```python
import re, os
with open(os.path.expanduser('~/.hermes/plugins/distillation/__init__.py')) as f:
    imports = set(re.findall(r'from\s+(\w+)\s+import', f.read()))
files = [f[:-3] for f in os.listdir('.') if f.endswith('.py')]
wired = [f for f in files if f in imports]
orphaned = [f for f in files if f not in imports]
```

### Check domain balance
```sql
SELECT domain, COUNT(*) as cnt, AVG(elo) as avg_elo
FROM cortex_nodes
WHERE node_type='tip' AND is_active=true
GROUP BY domain ORDER BY cnt DESC;
```

### Check Elo distribution
```sql
SELECT 
    percentile_cont(0.1) WITHIN GROUP (ORDER BY elo) as p10,
    percentile_cont(0.25) WITHIN GROUP (ORDER BY elo) as p25,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY elo) as p50,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY elo) as p75,
    percentile_cont(0.9) WITHIN GROUP (ORDER BY elo) as p90
FROM cortex_nodes WHERE node_type='tip' AND is_active=true;
```

## CortexDB API Notes
- `db.get_stats()` returns dict with: total_nodes, total_tips, active_tips, elo_avg, elo_min, elo_max, elo_std, domains, total_edges, total_evals
- `db.get_tip_quality_report()` returns dict with: tiers, unrated, needs_repair
- `db.dsn` is the connection string: `postgresql://hindsight:hindsight@localhost:5432/cortex`
- `db.search_text(query, limit)` for text search
- NO `db.conn` attribute — use psycopg2 directly if raw SQL needed

## Pitfalls Discovered During Audit
1. `CortexDB` has no `.conn` attribute — must use `psycopg2.connect(db.dsn)` for raw queries
2. `cortex_flywheel` table uses `started_at` not `created_at`
3. `RealDictCursor` returns dict-like objects — access via column name strings
4. Plugin import grep catches non-subconscious imports — must filter to `~/subconscious/*.py`
5. Daemon may have no log files — check `pgrep` not log presence
6. `~/.hermes/` git repo has no commits — the real repo is at `~/hermes-agent`
