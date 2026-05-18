# Verified Schema vs. Flywheel Code — 2026-05-03

Direct inspection of `information_schema.columns` during live debugging session.

## cortex_eval_history (ACTUAL)

| column_name | data_type |
|-------------|-----------|
| id | integer |
| node_a_id | integer |
| node_b_id | integer |
| winner | character varying |
| judge_type | character varying |
| confidence | double precision |
| reasoning | text |
| cycle_id | uuid |
| created_at | timestamp with time zone |

**Flywheel code expects:** `round_id`, `node_id_a`, `node_id_b`, `winner_id`, `judge_id`, `judge_axis`, `margin`, `domain` — **none of these exist**.

## cortex_flywheel (ACTUAL)

| column_name | data_type |
|-------------|-----------|
| id | integer |
| cycle_id | uuid |
| cycle_type | character varying |
| status | character varying |
| pairs_evaluated | integer |
| tips_repaired | integer |
| tips_consolidated | integer |
| tips_normalized | integer |
| tips_extracted | integer |
| duration_ms | integer |
| metadata | jsonb |
| started_at | timestamp with time zone |
| completed_at | timestamp with time zone |

**Flywheel code expects:** `phase`, `items_processed`, `items_produced`, `metrics`, `error_message` — **none of these exist**.

## cortex_nodes (relevant subset)

| column_name | data_type |
|-------------|-----------|
| id | integer |
| uuid | uuid |
| node_type | character varying |
| text | text |
| domain | character varying |
| confidence | double precision |
| elo | double precision |
| elo_matches | integer |
| upvotes | integer |
| downvotes | integer |
| frequency | integer |
| is_active | boolean |
| is_research_extracted | boolean |
| embedding | USER-DEFINED |
| content_md5 | character varying |
| provenance | text |
| source_ids | jsonb |
| metadata | jsonb |
| created_at | timestamp with time zone |
| updated_at | timestamp with time zone |
| last_seen | timestamp with time zone |
| last_evaluated | timestamp with time zone |
| tip_type | character varying |
| condition | text |
| recommendation | text |
| rationale | text |
| tool_name | character varying |

## Key Takeaway

The flywheel source code in `~/subconscious/cortex_flywheel.py` and the `cortex_access.py` wrapper are both out of sync with the actual PostgreSQL schema. **Always verify via `information_schema.columns` before writing any query.** The documented schema in `cortex-flywheel-api-reconcile/SKILL.md` was also wrong and has been corrected.
