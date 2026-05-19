# artist-reward-schema-design

*Researched: 2026-04-07 12:56 CDT*

# ARTIST 3-Component Reward for Hermes Distillation

## Schema Migration (cerebrum_memory.db)
```sql
ALTER TABLE distilled_tips ADD COLUMN reward_answer REAL DEFAULT 0.0;
ALTER TABLE distilled_tips ADD COLUMN reward_format REAL DEFAULT 0.0;
ALTER TABLE distilled_tips ADD COLUMN reward_execution REAL DEFAULT 0.0;
```

## Composite Score Formula
```
composite = 0.5 * reward_answer + 0.2 * reward_format + 0.3 * reward_execution
```

## Implementation Priority
- LOW — current single-axis confidence works for now
- MEDIUM — when distillation quality plateaus, add this
- HIGH — before any RL training of Hermes agent

## Source
- ARTIST paper (Microsoft Research, arXiv 2505.01441)
- Tool-R1 paper (Harbin IT, arXiv 2509.12867)


## Sources

- ~/.hermes/knowledge/artist-tool-r1-rl-agentic-reasoning-2025.md
