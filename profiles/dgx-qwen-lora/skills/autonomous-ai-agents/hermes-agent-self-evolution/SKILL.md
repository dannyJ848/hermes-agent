---
name: hermes-agent-self-evolution
description: Evolutionary self-improvement for Hermes Agent using DSPy + GEPA. Auto-optimizes skills, prompts, and tool descriptions. No GPU required.
version: 1.0.0
metadata:
  hermes:
    tags: [evolution, optimization, dspy, gepa, self-improvement]
    related_skills: [autonomous-continuous-execution, hermes-dojo]
---

# Hermes Agent Self-Evolution

Uses DSPy + GEPA (Genetic-Pareto Prompt Evolution) to automatically evolve and optimize
Hermes Agent skills, tool descriptions, system prompts, and code.

No GPU training required. API calls only. ~$2-10 per optimization run.

## When to Use

- Nightly skill optimization cron
- User asks to improve/optimize a specific skill
- User wants to evolve prompts or tool descriptions
- Periodic self-improvement cycles

## Prerequisites

- Python 3.10+
- Repo cloned at /tmp/hermes-agent-self-evolution
- Hermes agent repo accessible

## Setup

```bash
cd /tmp/hermes-agent-self-evolution
pip install -e ".[dev]"
export HERMES_AGENT_REPO=~/.hermes/hermes-agent
```

## Usage

### Evolve a skill (synthetic eval data)
```bash
python -m evolution.skills.evolve_skill \
    --skill github-code-review \
    --iterations 10 \
    --eval-source synthetic
```

### Evolve using real session history
```bash
python -m evolution.skills.evolve_skill \
    --skill github-code-review \
    --iterations 10 \
    --eval-source sessiondb
```

## What It Optimizes

| Phase | Target | Engine | Status |
|-------|--------|--------|--------|
| Phase 1 | Skill files (SKILL.md) | DSPy + GEPA | Implemented |
| Phase 2 | Tool descriptions | DSPy + GEPA | Planned |
| Phase 3 | System prompt sections | DSPy + GEPA | Planned |
| Phase 4 | Tool implementation code | Darwinian Evolver | Planned |
| Phase 5 | Continuous improvement loop | Automated pipeline | Planned |

## Guardrails

1. Full test suite must pass 100%
2. Skills <= 15KB, tool descriptions <= 500 chars
3. No mid-conversation changes
4. Semantic preservation required
5. All changes through review

## Autobrowse Integration

- `autobrowse_tracer.py` — captures tool call traces
- `autobrowse_analyzer.py` — pattern detection
- `autobrowse_synthesizer.py` — tip generation
- `autobrowse_graduator.py` — Elo scoring

**CRITICAL: Hook Signature Compatibility**
Hermes core `invoke_hook` passes kwargs to plugin hooks. If the hook function signature doesn't accept `**kwargs`, Python raises TypeError which is silently swallowed by invoke_hook's try/except. The hook appears registered but NEVER FIRES.

Fix pattern: Always add `**kwargs` to hook signatures and make all params optional:
```python
# WRONG — will fail silently
def _on_post_tool_call(tool_name: str, args: dict, result: Any, status: str) -> dict:

# CORRECT — accepts whatever invoke_hook passes
def _on_post_tool_call(tool_name: str, args: dict, result: Any, status: str = "", error: str = "", **kwargs) -> dict:
```

The distillation plugin had this exact bug — `_on_post_tool_call` expected `status: str` but `invoke_hook` passed `task_id`, `session_id`, `tool_call_id`, `duration_ms`. All 4 hooks needed `**kwargs` added.

**CRITICAL: LLM Judge Model Selection for Structured Output**

`deepseek-v4-pro` (reasoning model) **cannot produce structured JSON**. Its `content` field is always empty; `reasoning_content` contains prose reasoning, not JSON. For adversarial validation, Elo tournaments, or any task requiring parseable JSON output, use `deepseek-chat` instead.

```python
# WRONG — returns empty content + prose reasoning
judge = LLMJudge(model="deepseek-v4-pro")
result = judge._call_llm(messages, response_format={"type": "json_object"})

# CORRECT — valid JSON in content
judge = LLMJudge(model="deepseek-chat")
result = judge._call_llm(messages, response_format={"type": "json_object"})
```

This was discovered during Cycle 4 adversarial batch testing — 5 consecutive failures before switching models. See `llm-judge-ensemble` skill for full details.

## Enhancement Cycle Methodology

When user says "keep enhancing" or "run enhancement cycles until you can't anymore":

### Phase 1: Audit (always start here)
1. Count subconscious modules — how many are orphaned (0 imports)?
2. Count custom tools — how many are registered vs invisible?
3. Count databases — which are empty ghosts?
4. Count plugins — which are enabled vs dormant?
5. Count tips — Elo-rated? Survival-tracked?

### Phase 2: Cleanup (surgical)
1. Archive orphaned modules to `~/subconscious/archive/`
2. Delete empty databases (<100KB, 0 rows)
3. Register high-value orphaned tools with `@register_tool`
4. Enable dormant plugins (`hermes plugins enable <name>`)

### Phase 3: Quality Systems
1. **Tip survival tracking** — `tip_survival` table with `opportunities` + `applications`
2. **Auto-prune** — mark tips with <30% survival after 100+ ops for review
3. **Adversarial validation** — red-team tips with DeepSeek V4 Pro judge
4. **Predictive routing** — route around weak tools based on historical success rates

### Phase 4: Advanced Cognition
1. **Project clustering** — `projects` + `session_project_map` tables
2. **Prompt fragment Elo** — A/B test system prompt components
3. **Error pattern prediction** — `error_patterns_predictive` table with prevention strategies
4. **Token efficiency tracking** — `token_efficiency` table with compression recommendations

### Phase 5: Self-Monitoring
1. **Health daemon** — cron job every 5 minutes checking tip health, tool degradation, DB size, error patterns. **CRITICAL: Add [OK] confirmations** — silent success is indistinguishable from failure.
2. **Rapid learning extraction** — extract lessons from every session into `rapid_learnings`
3. **Auto-skill pipeline** — queue high-quality knowledge docs for SKILL.md generation
4. **Enhancement effectiveness** — track each cycle's impact in `enhancement_effectiveness`

## The Build-vs-Wire Rule

**User preference (first-class signal):** The user gets angry when systems are built but not integrated. "What's the point of building anything if you're not wiring it in?"

**Rule:** Every new cognitive system must include BOTH:
1. **Construction** — the code, tables, files
2. **Integration** — hook calls, import bridges, or sidecar wiring that ensures it runs during normal operation

**Anti-pattern (never do this):**
```python
# WRONG — built but never called
def _on_post_tool_call(...):
    # ... existing code ...
    pass  # my_new_system sits here unused

# WRONG — imported but not invoked
if _COGNITIVE_INFRA_V2:
    from cognitive_infrastructure_v2 import get_credit_assigner
    # Never calls ca.record_injection() or ca.record_outcome()
```

**Correct pattern:**
```python
# CORRECT — imported AND invoked at the right lifecycle point
if _COGNITIVE_INFRA_V2:
    try:
        ca = get_credit_assigner()
        for tool_name, tip_ids in _injected_tips_this_turn.items():
            for tip_id in tip_ids:
                ca.record_injection(tool_name, tip_id)
    except Exception:
        pass
```

**Verification step:** After wiring, run a live tool call and check the database:
```bash
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT COUNT(*) FROM skill_rewards"
# Must be > 0 after a real tool call, not just test data
```

**Integration checklist for new cognitive systems:**
- [ ] Hook signature has `**kwargs` (see Hook Signature Compatibility above)
- [ ] System is imported at plugin load time
- [ ] System is called from the appropriate hook (pre_llm_call, post_tool_call, session_end)
- [ ] Database table receives live data within 3 tool calls of wiring
- [ ] No silent failures — exceptions caught but logged
- [ ] Fallback behavior works when system is disabled

### Health Daemon Anti-Pattern: Silent Success

The original daemon only printed when problems were found:
```python
# WRONG — user can't tell if checks ran or crashed
if weak_tips:
    print(f"[TIPS] Pruned {len(weak)} weak tips")
# If no weak tips: NO OUTPUT — did the check run?

# CORRECT — always report status
if weak_tips:
    print(f"[TIPS] Pruned {len(weak)} weak tips")
else:
    print("[TIPS] OK: no weak tips to prune")
```

Fixed output format:
```
=== Hermes Health Check 2026-05-09 13:04:01 ===
[TIPS] OK: no weak tips to prune
[TOOLS] OK: no degraded tools
[DB] OK: 14.3MB
[ERRORS] OK: no hot error patterns
=== Done ===
```

**Template:** See `scripts/health_daemon_template.py` for a copy-paste starter.

### Auto-Skill Pipeline

Convert high-quality knowledge docs into class-level skills:

```python
# 1. Score queued docs by size/completeness
# 2. Generate SKILL.md with standard frontmatter + structured body
# 3. Update auto_skill_pipeline status: pending → generated
# 4. Log to enhancement_effectiveness
```

**Quality scoring heuristics:**
- Doc size > 5KB = substantial content
- Contains tables/code blocks = structured
- Has "When to Use" / "Prerequisites" sections = skill-ready
- Recent (< 30 days) = relevant

**Generated skills from Cycle 4:**
- `hermes-apparatus-audit` — from apparatus audit doc (score 0.955)
- `cortex-flywheel-operation` — from flywheel blueprint (score 0.801)

### Known Weak Tools (route around)
| Tool | Success Rate | Issue | Alternative |
|------|-------------|-------|-------------|
| `cronjob` | 13% | id field confusion | `terminal` with crontab syntax |
| `delegate_parallel` | 33% | frequent failure (3x) | `delegate_task` sequential |
| `patch` | 94% | old_string mismatch | `write_file` for full replacement |

### Proven Tool Combos
- `web_search` → `web_extract` for research
- `execute_code` → `write_file` for bulk operations
- `read_file` → `patch` for surgical edits
- `search_files` → `read_file` for discovery

### Pipeline Smoke Test

To verify the full autobrowse pipeline is functional end-to-end:

```python
from autobrowse_tracer import AutobrowseTracer
from autobrowse_analyzer import AutobrowseAnalyzer
from autobrowse_synthesizer import AutobrowseSynthesizer
from autobrowse_graduator import AutobrowseGraduator

t = AutobrowseTracer(session_id='test')
t.set_task_context('test task')

# Record 3+ identical calls to trigger redundant_loop detection
for i in range(3):
    t.record_call(tool_name='web_search', model_used='kimi-for-coding',
        input_data={'query': 'same'}, output_data={'results': i},
        execution_time_ms=100, status='success', input_tokens=10, output_tokens=20)

a = AutobrowseAnalyzer()
patterns = a.analyze_traces(t.traces)  # Expect 1+ patterns

s = AutobrowseSynthesizer()
tips = s.generate_tips(patterns)  # Expect 1+ tips

# Note: duplicate key errors on tip insert are NORMAL if tips already exist
# The MD5 unique constraint prevents duplicates — this is expected behavior

g = AutobrowseGraduator()
for tip in tips:
    g.record_application(tip['condition'][:40], success=True)
```

**Expected outputs:**
- `patterns`: 1+ (redundant_loop, suboptimal_model, token_waste, failure_cluster, tool_mismatch)
- `tips`: 1+ dicts with keys: `tip_type`, `condition`, `recommendation`, `domain`, `confidence`
- `strategy.md`: Updated with new observations (check file size grows)
- Duplicate key errors from `CortexDB.insert_node`: **Expected and harmless** — means tip deduplication is working

**Module method names (check before calling):**
- Tracer: `record_call()` (not `record_tool_call()`)
- Analyzer: `analyze_traces()` (not `analyze_recent_traces()`)
- Synthesizer: `generate_tips()` (not `synthesize_from_patterns()`)
- Graduator: `record_application(tip_id, success)` (not `evaluate_tip()`)

## Cron Setup

```bash
# Nightly at 2 AM, evolve top 3 weakest skills
hermes cron create --name "skill-evolution" --schedule "0 2 * * *" \
  --prompt "Run self-evolution on the 3 weakest skills. cd /tmp/hermes-agent-self-evolution && ..."
```

## References
- `references/enhancement-cycle-methodology.md` — Full audit-to-cleanup-to-quality pipeline
- `references/tool-intelligence-patterns.md` — Weak tools, proven combos, error patterns, schema migrations
- `references/deepseek-api-structured-output.md` — v4-pro vs chat for JSON tasks
- `references/novel-enhancement-architecture.md` — 5 integrated cognitive systems pattern
- `references/macbook-playwright-setup.md` — Playwright version mismatch fix, local file serving, headless WebGL limits
- `references/threejs-headless-compatibility.md` — Material compatibility matrix for browser_vision with 3D scenes
- `scripts/health_daemon_template.py` — Copy-paste starter for health checks with [OK] confirmations
