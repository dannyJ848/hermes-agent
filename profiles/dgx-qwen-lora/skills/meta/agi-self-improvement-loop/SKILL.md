---
name: agi-self-improvement-loop
version: 1.0
created: 2026-04-07
description: Complete AGI self-improvement loop with research, distillation, knowledge graph, meta-monitoring, and self-play challenge generation.
---

# AGI Self-Improvement Loop

The complete autonomous self-improvement pipeline for Evey.

## Architecture

```
Research → Wiki → Distillation → Tips → Injection → Behavior → Measurement
   ↑                                                           │
   └───────── Meta-Loop ←──── Insights ←───────────────────────┘
```

## Components

### 1. Research Phase
- `web_research()` → find frontier papers
- `web_extract()` → extract content from URLs
- Save wiki pages to `~/wiki/concepts/<topic>.md`

### 2. Distillation Phase
```bash
cd ~/hermes-agent && venv/bin/python3 ~/subconscious/research_to_distillation.py
```
Converts wiki pages to distilled tips in `cerebrum_memory.db`.
Schema: tip_type, condition, recommendation, rationale, tool_name, domain, confidence, upvotes, downvotes.

### 3. Knowledge Graph
- `~/subconscious/kg_builder.py` — builds from semantic_facts + distilled_tips
- Tables: `kg_nodes` (206 nodes), `kg_edges` (535 edges) in `cerebrum_memory.db`
- Multi-hop retrieval via BFS with score decay (HippoRAG 2 inspired)
- Run: `venv/bin/python3 ~/subconscious/kg_builder.py`

### 4. Meta-Loop (Self-Monitoring)
```bash
cd ~/hermes-agent && venv/bin/python3 ~/subconscious/meta_loop.py
```
Measures tip health by type/domain, generates meta-insights.
Finds: survival rate, confidence drift, extraction quality.

### 5. Self-Play Challenge Generator
```bash
cd ~/hermes-agent && venv/bin/python3 ~/subconscious/self_play_challenges.py
```
Generates synthetic tool-use challenges targeting weak tools.
Saves to `~/.hermes/self_play_challenges.json`.

### 6. Tool Complexity Router
- `~/.hermes/tool_complexity_router.json`
- 65 tools classified: trivial (29), standard (19), complex (17)
- Inspired by Ares (arXiv:2603.07915) — route simple tools to fast models

### 7. AGI Cron (bd76c4443c53)
- Runs every 3 minutes with 6-phase cycle
- Skills: autonomous-continuous-execution, autonomous-curiosity
- Model: glm-5.1
- Phases: meta-loop → domain explore → distillation → KG update → capability check → cost check

## Key Files
| File | Purpose |
|------|---------|
| `~/wiki/concepts/*.md` | 40 wiki pages across 8 domains |
| `~/subconscious/research_to_distillation.py` | Wiki → tips bridge |
| `~/subconscious/meta_loop.py` | Self-monitoring loop |
| `~/subconscious/kg_builder.py` | Knowledge graph builder |
| `~/.hermes/cerebrum_memory.db` | Tips + KG storage |
| `~/.hermes/tool_complexity_router.json` | Tool complexity classification |
| `~/.hermes/self_play_challenges.json` | Generated practice tasks |

## Paper-to-Plugin Engineering Pattern

When a frontier paper describes a mechanism that maps to agent behavior, translate it into working code using this hook mapping:

```
PAPER MECHANISM              → PLUGIN HOOK         → WHAT IT DOES
─────────────────────────────────────────────────────────────────
Pre-execution prediction      → pre_tool_call       → Skip doomed calls, suggest alternatives
Post-execution feedback       → post_tool_call       → Update world model, track uncertainty
Context injection             → pre_llm_call         → Inject signals (uncertainty, tips, deferral)
API cost/latency tracking     → post_api_request     → Per-model analytics
```

### Process (5 steps):
1. Read paper, extract CORE MECHANISM (not abstract — the actual algorithm)
2. Map mechanism to existing hook points (see table above)
3. Create lightweight DB table for persistent state
4. Wire into existing plugin hooks (don't create new plugins)
5. Add to `register()` in plugin's `__init__.py` if new hooks needed

### Implemented AGI Enhancements (v2.1, Apr 7):

**SWIRL Tool Predictor** (world model):
- `~/subconscious/tool_predictor.db` — Beta(α,β) posterior per tool
- `_predict_tool_outcome()` returns expected success probability
- `_update_predictor()` updates posterior after each call
- Wired: post_tool_call (update), pre_llm_call (show prediction)

**AUQ Uncertainty Tracker** (dual-process confidence):
- `_uncertainty_state` dict tracks cumulative confidence per turn
- Multiplicative decay: each tool call multiplies by predicted success rate
- Triggers [HIGH UNCERTAINTY] signal when cumulative < 0.3 after 3+ calls
- Triggers [MULTIPLE FAILURES] when 2+ failures in 2+ calls
- Wired: post_tool_call (update), pre_llm_call (inject + reset)

**Polaris Experience Patches** (policy repair from failures):
- `_generate_experience_patch()` maps error patterns → behavioral rules
- 11 error pattern classes (timeout, 403, JSON, syntax, etc.)
- Auto-inserts as "recovery" tips with domain "agi-experience"
- Deduplication via fuzzy match on first 60 chars
- Wired: post_tool_call (generate on error), pre_llm_call (show recent patches)

**HILA Metacognitive Deferral** (when to ask user):
- `_check_metacognitive_deferral()` checks high-risk + low-success + destructive args
- Only triggers when tool has 5+ observations AND success < 70%
- Wired: pre_tool_call (return deferral warning)

### Key DB Tables Added:
| DB | Table | Purpose |
|----|-------|---------|
| `~/subconscious/tool_predictor.db` | `tool_priors` | Beta(α,β) per tool |
| `~/subconscious/tool_predictor.db` | `predictions` | Prediction vs actual history |
| `~/.hermes/cerebrum_memory.db` | `distilled_tips` (domain='agi-experience') | Auto-generated recovery rules |

## Current Stats (Apr 7, 2026)
- Wiki pages: 71 (was 40 — 31 new from paper-to-plugin work)
- Distilled tips: 170 (was 120 — 20 from new papers + auto-recovery patches growing)
- KG nodes: 206, edges: 535
- Domains covered: reasoning, agent-arch, memory, tool-learning, self-improvement, inference-opt, medical-AI, 3d-rendering, agent-security

## Key Research Papers Integrated
- GEA (arXiv:2602.04837) — Group-level agent evolution
- Hyperagents (arXiv:2603.19461) — Self-modifying meta-procedures
- Darwin Godel Machine (arXiv:2505.22954) — Agent archive evolution
- AgentArk (arXiv:2602.03955) — Multi-agent → single-agent distillation
- Ares (arXiv:2603.07915) — Adaptive reasoning effort
- HippoRAG 2 (arXiv:2502.14802) — KG + PPR memory
- Tool-R0 (arXiv:2602.21320) — Zero-data self-play tool learning
- Self-Evolving Agents Survey (arXiv:2507.21046) — Complete taxonomy
- Agentic Psychiatry (Nature 2026) — Danny's domain
- Agent Security (arXiv:2603.11619) — Five-layer security framework
- Polaris/Gödel Agent (arXiv:2603.23129) — Policy-level self-repair via experience abstraction → implemented as experience patches
- SWIRL (arXiv:2602.06130) — Self-improving world model with latent actions → implemented as tool outcome predictor
- Agentic UQ (arXiv:2601.15703) — Dual-process uncertainty for reliable agents → implemented as uncertainty tracker
- Recursive Language Models (arXiv:2512.24601) — Proactive context management via delegation → wiki entry (not yet coded)
- HILA (arXiv:2603.07972) — Metacognitive policy for human-agent deferral → implemented as deferral checker

## Pitfalls
- The distillation bridge saturates quickly — new wiki pages may not produce new tips if patterns already exist
- Tool_stats DB may be empty — self-play challenges use defaults
- KG extraction is regex-based and noisy — needs periodic cleaning
- The AGI cron runs every 3 min but each cycle costs tokens — monitor costs
