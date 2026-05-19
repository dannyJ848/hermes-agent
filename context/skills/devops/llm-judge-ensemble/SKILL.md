---
name: llm-judge-ensemble
version: 3.0
created: 2026-04-15
updated: 2026-04-16
description: Two-tier evaluation system — free heuristic (~85% LLM alignment) as workhorse + paid LLM ensemble for weekly calibration. 3 judges from 3 providers.
---

# LLM Judge Ensemble + Heuristic Calibration

## Architecture (Cost-Sustainable)

```
┌─────────────────────────────────────────────────┐
│                  EVAL SYSTEM                     │
│                                                  │
│  Every 2h: heuristic_judge (FREE, 200K+ evals)  │
│      ↓ ~85% alignment                             │
│  Weekly:  LLM ensemble ($0.25/mo calibration)   │
│      ↓ checks heuristic drift                    │
│  On-demand: full_audit_sweep (manual only)       │
└─────────────────────────────────────────────────┘
```

**Heuristic = 99% of evals (free, forever)**
- Runs every 2h via flywheel cron
- ~85% alignment with LLM (validated Apr 16, iteratively calibrated)
- 200K historical evals

**LLM judges = calibration only (1%, ~$0.25/month)**
- Weekly cron: 20 pairs x 3 judges = ~$0.06/week
- If heuristic disagree rate > 40%, recalibrate heuristic weights
- Full audit: manual only, ~$9 for complete pass

## Heuristic Judge Details

File: `~/subconscious/cortex_flywheel.py` → `heuristic_judge()`

### Signals (in order of weight)

| Signal | Formula | Range | Purpose |
|--------|---------|-------|---------|
| Confidence | `(conf - 0.5) * 2` | 0-1 | Quality filter |
| Elo | `1.2 / (1 + exp(-(elo-1800)/200))` | 0-1.2 | Track record |
| Frequency | `min(freq/10, 1)` | 0-1 | Validation count |
| Text quality | `length + specificity + IF-THEN` | 0-1.5 | Actionability |
| Domain | `0.3 if not general` | 0-0.3 | Specificity bonus |
| IF-THEN structure | `0.3 if both / 0.15 if IF only` | 0-0.4 | Actionability (strong diff signal) |
| Actionability | `tools(0.3 ea)+backticks(0.2 ea)-vagueness(0.2)` | -0.6-1.5 | Concrete specifics |

### Tie Threshold

`if abs(diff) < 0.02: return tie` — was 0.1 (too many ties vs LLM)

### Calibration History

| Date | Change | Alignment |
|------|--------|-----------|
| Apr 16 original | tie=0.1, 5 signals, no Elo/IF-THEN | 38% (5/8 ties) |
| Apr 16 + IF-THEN | added 0.3/0.15 bonus | 50% (ties→hard disagrees) |
| Apr 16 + Elo | sigmoid(1.5), tie=0.05 | 75% |
| Apr 16 + actionability | tools+backticks+vagueness, Elo=1.2, tie=0.02 | **~85%** |

### Known Failure Modes (~15% gap)

Heuristic disagrees with LLM when:
- High-Elo tip has less actionable content than low-Elo tip (Elo overrides quality)
- Both tips have similar structural signals (all IF-THEN, same domain)
- Tips are semantically different but score similarly on structural axes
**Possible fixes**: embedding cosine similarity tiebreaker, per-domain Elo normalization

## LLM Judge Details

File: `~/subconscious/llm_judge.py`

### Current Judges (3 providers)

| # | Model | Provider | Route | Cost/1M in/out | Latency |
|---|-------|----------|-------|-----------------|---------|
| 1 | `deepseek-v4-pro` | DeepSeek (direct) | `_call_llm()` | $0.109/$0.218 | 2-3s |

**Note:** DeepSeek V4 Pro is the SOLE LLM judge as of May 2026. The previous ensemble (MiniMax + Gemini + GPT-4.1-mini) was consolidated to DeepSeek V4 Pro for cost efficiency ($0.109/$0.218 per 1M tokens with 75% discount until 2026-05-31). Configured in `~/.hermes/config.yaml` provider `deepseek` with model `deepseek-v4-pro`.

**File location:** `~/subconscious/llm_judge.py`

### DeepSeek V4 Pro Integration (May 2026)

DeepSeek V4 Pro is the default and only model for the judge system:

```python
# In ~/subconscious/llm_judge.py:
class LLMJudge:
    def __init__(self, api_key=None, model="deepseek-v4-pro", base_url="https://api.deepseek.com"):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.total_cost = 0.0
        self.total_calls = 0
        self.failed_calls = 0
        
        # Cost per 1M tokens (input, output) — 75% discount until 2026/05/31
        self.cost_map = {
            "deepseek-v4-pro": (0.109, 0.218),
        }
```

**API call pattern:**
```python
from llm_judge import LLMJudge
j = LLMJudge()
# Compare two tips
r = j.compare_tips('Tip A: always test code', 'Tip B: never test code')
print(r['winner'])  # 'a', 'b', or 't'
print(r['confidence'])  # 0.0-1.0
print(r['reasoning'])  # explanation
# Cost tracking
print(f"${j.total_cost:.4f} spent, {j.total_calls} calls, {j.failed_calls} failures")
```

**CRITICAL: DeepSeek V4 Pro vs deepseek-chat for structured output**

`deepseek-v4-pro` is a **reasoning model**. When using `response_format={"type": "json_object"}`:
- `content` field is **EMPTY** (`""`)
- `reasoning_content` contains chain-of-thought prose, NOT JSON
- The model **never outputs structured JSON** in either field

`deepseek-chat` (non-reasoning) works correctly:
- `content` contains valid JSON
- `reasoning_content` is absent
- `response_format={"type": "json_object"}` functions as expected

**Routing rule:**
| Task | Model | Why |
|------|-------|-----|
| Open-ended comparison, reasoning | `deepseek-v4-pro` | Better reasoning quality |
| Structured JSON output | `deepseek-chat` | Actually returns parseable JSON |

```python
# WRONG — returns empty content + prose reasoning
judge = LLMJudge(model="deepseek-v4-pro")
result = judge._call_llm(messages, response_format={"type": "json_object"})
# result = "" (empty)

# CORRECT — use deepseek-chat for JSON
judge = LLMJudge(model="deepseek-chat")
result = judge._call_llm(messages, response_format={"type": "json_object"})
# result = '{"robustness": 80, "verdict": "STRONG", ...}'
```

The `_call_llm()` method's fallback to `reasoning_content` does NOT help with V4 Pro — the reasoning is prose analysis, not JSON. This was confirmed in session 2026-05-09 where 5 consecutive calls with `response_format` all returned empty content.

**Verification:**
```bash
cd ~/subconscious && python3 -c "from llm_judge import LLMJudge; j = LLMJudge(); print('judge ok:', j.model)"
# Expected: judge ok: deepseek-v4-pro
```

### API Keys

- **MiniMax**: env var `MINIMAX_API_KEY` in `.env` (starts with `sk-cp-...`). Uses Bearer auth.
- **OpenRouter**: config.yaml at `auxiliary.approval.api_key`
- OpenRouter requires credit — $10 minimum top-up. Monitor balance.

### Routing Rules

- `minimax-paid` in JUDGE_MODELS → routes to `_call_minimax()` (direct API)
- `minimax-paid` must NOT be in FAST_MODELS — `_call_model()` sends to OpenRouter which returns 400
- All other models route through OpenRouter via `_call_model()`

## Function Signatures

```python
# Single LLM judge (DeepSeek V4 Pro)
from llm_judge import LLMJudge
j = LLMJudge()

# Compare two tips
r = j.compare_tips(tip_a, tip_b)  # tip_a/b can be strings or dicts
# Returns: {winner: 'a'|'b'|'t', confidence: 0.0-1.0, reasoning: str, dimensions: {...}}

# Evaluate single tip for quality issues
r = j.evaluate_single(tip: dict) -> dict
# Returns: {score: 0-1, issues: [...], confidence: 0.0-1.0}

# Cost tracking
j.total_cost   # cumulative $ spent
j.total_calls  # successful calls
j.failed_calls # failed calls
j.get_cost_report()  # detailed breakdown
```

**Note:** The old `call_ensemble_judge()` and `call_llm_judge()` functions from the multi-provider era are deprecated. Use `LLMJudge.compare_tips()` directly.

## Eval History

All eval results (heuristic + LLM) recorded to `cortex_eval_history`:

```sql
SELECT judge_id, COUNT(*) FROM cortex_eval_history GROUP BY judge_id;
-- heuristic_v1: 200K+, llm: growing, full_audit: growing
```

Columns: id, round_id, node_id_a, node_id_b, winner_id, judge_id, judge_axis, margin, domain, created_at

## Calibration Test Procedure

To re-validate heuristic alignment after any changes:

```python
import sys, os, random
sys.path.insert(0, '$HOME/hermes-agent')
sys.path.insert(0, '$HOME/subconscious')
from dotenv import load_dotenv
load_dotenv()  # loads from .env

from cortex_access import cortex_cursor
from cortex_flywheel import heuristic_judge
from llm_judge import _call_model, JUDGE_PROMPT

with cortex_cursor(commit=False) as cur:
    cur.execute("""
        SELECT id, text, elo, domain, confidence 
        FROM cortex_nodes 
        WHERE node_type='tip' AND is_active=TRUE AND embedding IS NOT NULL
        ORDER BY RANDOM() LIMIT 20
    """)
    tips = [dict(r) for r in cur.fetchall()]

agree = disagree = tie_involved = 0
for i in range(10):
    a, b = random.sample(tips, 2)
    h = heuristic_judge(a, b)
    prompt = JUDGE_PROMPT.format(
        elo_a=a.get('elo', 1200), text_a=a.get('text', ''),
        elo_b=b.get('elo', 1200), text_b=b.get('text', '')
    )
    l_raw = _call_model("google/gemini-2.5-flash", prompt, timeout=15)
    l_winner = l_raw.get('winner', 'tie') if l_raw else 'tie'
    h_winner = h.get('winner', 'tie')
    
    if h_winner == l_winner: agree += 1
    elif h_winner == 'tie' or l_winner == 'tie': tie_involved += 1
    else: disagree += 1

print(f"Agree: {agree}/10 | Disagree: {disagree} | Ties: {tie_involved}")
print(f"Alignment: {agree*10}%")
```

**Threshold**: alignment < 60% means heuristic needs retuning. > 75% is healthy.


## Iterative Calibration Methodology

When tuning the heuristic against an LLM ground truth, follow this loop:

### 1. BASELINE (5 min)
- Run 10-20 pair alignment test against a cheap LLM (gemini-2.5-flash)
- Record agree/disagree/tie counts
- If tie rate > 30%: tie threshold is too wide
- If disagree rate > 40%: signals are wrong, not just weak

### 2. ADD-ONE-SIGNAL (per iteration)
- Add ONE new signal at a time
- Adding multiple signals simultaneously makes it impossible to diagnose which caused regression
- Re-run alignment test after each addition
- Watch for: new signal causing regression on a different axis

### 3. DISAGREEMENT DIAGNOSIS (the key step)
- When alignment drops or stalls, print FULL disagreement details:
  - Both tip texts, elo, confidence, domain
  - Which side heuristic picked vs LLM picked
  - Heuristic's score breakdown
- Look for PATTERNS: is heuristic always favoring higher Elo? Always favoring IF-THEN?
- The pattern tells you which existing signal is too strong/weak

### 4. WEIGHT TUNING
- If a signal dominates disagreements (e.g., Elo always wins but LLM disagrees):
  - Reduce its weight (don't remove — it has information value)
  - Add a competing signal that captures what the LLM is seeing
- If tie rate spikes: tighten tie threshold (halve it, test, repeat)
- If disagree rate spikes but ties are low: over-corrected, back off weight

### 5. CONVERGENCE CHECK
- Run 30-40 pair test for statistical reliability
- Compute Wilson confidence interval
- Stop when alignment > 80% AND 95% CI lower bound > 65%
- Further tuning has diminishing returns — remaining gap is where structural signals fundamentally can't capture semantic quality

### Common Pitfalls
- Don't add Elo too early — it masks other signal problems. Tune content signals first, then add Elo as stabilizer
- Regex-based signals are fragile — test on real tips with `re.findall()` before wiring. Over-broad regexes (numbers, paths) max out and stop discriminating
- Tie threshold is the most sensitive knob — 0.1 was way too wide, 0.02 works. Below 0.01 creates hard disagrees from noise
- Sample variance is real — 10-pair tests swing +/-20%. Always confirm with 30+ pairs
- Use a consistent LLM model for calibration. gemini-2.5-flash is the sweet spot (fast, cheap, reasonable)
## Cron Jobs

| Job | Schedule | Cost | Purpose |
|-----|----------|------|---------|
| cortex-flywheel-baseline | every 2h | $0 | Heuristic eval sweep (50 pairs) |
| cortex-quality-sweep | every 2h | $0 | Stats only |
| llm-calibrate-weekly | Sunday 3am | ~$0.06 | 20-pair LLM alignment check |

## Daemon Status (DISABLED)

`cortex_daemon.py` disabled as of Apr 16 (broken import path). All eval runs via cron jobs with standalone Python scripts. Do NOT restart without venv activation.

## Pitfalls

- ALWAYS test new judge models individually via `_call_model("model-name", prompt)` before wiring into ensemble
- `minimax-paid` must NOT be in FAST_MODELS — causes 400 errors on OpenRouter
- `heuristic_judge` returns `{winner, margin, reasoning}` — no `confidence` key
- MiniMax M2.7 has thinking chain — needs `max_tokens=800`, strip `</think>` content
- OpenRouter credit exhaustion causes ALL LLM evals to fail silently — check balance if alignment drops to 0%
- `call_ensemble_judge` with `num_judges=2` can timeout — use `num_judges=3` or accept partial results
- Hot-reload: `importlib.reload(cortex_flywheel)` after editing
- Costs: $10 OpenRouter credit = ~330 full-audit sweeps or 3,300 calibration runs
- Heuristic tie rate spikes if IF-THEN bonus cancels between similar-format tips — the Elo signal is the tiebreaker

## Content Coverage Audit (Prevent Navel-Gazing)

The distillation pipeline only captures what flows through plugin hooks. If all your sessions are about fixing your own infrastructure, all tips will be about self-improvement — and the system can't help the user with anything else.

**Audit quarterly (or before a user task):**
```python
with cortex_cursor(commit=False) as cur:
    cur.execute("SELECT domain, COUNT(*) as cnt FROM cortex_nodes WHERE node_type='tip' AND is_active=TRUE GROUP BY domain ORDER BY cnt DESC")
    for r in cur.fetchall():
        print(f"  {r['domain']}: {r['cnt']}")
```

**If any user-serving domain (tool_use, coding, etc.) is < 5% of tips:**
1. `session_search` for past sessions about that topic
2. Distill patterns into IF-THEN tips: `insert_node()` or direct SQL INSERT
3. Fix domain: `fn_normalize_domain()` trigger remaps unknown domains to "general" — add explicit mapping (e.g., "anki" → "tool_use")
4. Embed: `sentence_transformers` + UPDATE embedding column
5. Boost: set elo=2100, frequency=5, confidence=0.95 so new tips can compete in hybrid_search
6. Verify retrieval: cosine similarity search confirms tips surface for relevant queries

**Domain Trigger Gotcha:** Custom domains NOT in the 13 canonical list get forced to "general" by the `fn_normalize_domain()` trigger validation step. To add a new domain: (1) add CASE mapping in trigger, (2) add to the IN() canonical validation list, (3) `CREATE OR REPLACE FUNCTION fn_normalize_domain()`, (4) UPDATE existing squashed tips back to correct domain.
