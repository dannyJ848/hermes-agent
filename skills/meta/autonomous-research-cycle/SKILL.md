---
name: autonomous-research-cycle
version: 1.0
description: "Lightweight 6-phase autonomous cycle for entropy reduction: active inference domain selection, self-monitoring, targeted research with saturation pivoting, distillation bridge, capability check, and KG stats. Designed for high-frequency cron execution (every 30s-3min) between heavy training gym rounds."
trigger: "When running as a scheduled cron job with the 6-phase entropy-reduction protocol."
---

# Autonomous Research Cycle (6-Phase Entropy Reduction)

A lightweight, continuous cycle that keeps the knowledge base growing by targeting undercovered domains, researching frontier advances, and attempting distillation — without the heavy build/test overhead of a full training gym round.

## When to Use
- High-frequency cron jobs (every 30 seconds to 3 minutes) when the user is away
- Between heavy `training-gym-continuous` rounds to prevent knowledge stagnation
- When module-building is blocked (context compressed, waiting for Danny, or build fatigue)
- Any time the agent has spare cycles and no urgent construction tasks

## Prerequisites
- `~/subconscious/domain_certainty.py` — active inference domain explorer
- `~/subconscious/meta_loop.py` — tip health self-monitor
- `~/subconscious/research_to_distillation.py` — wiki → tip bridge
- `~/subconscious/tool_planner.py` — capability benchmark
- `~/.hermes/cerebrum_memory.db` — knowledge graph (SQLite)
- `~/wiki/concepts/` — knowledge library directory

---

## Phase 1: Domain Certainty (Active Inference)

**Goal:** Identify the domain with highest explore_priority.

```bash
cd ~/hermes-agent && venv/bin/python3 ~/subconscious/domain_certainty.py
```

**Output:** Sorted table of domains with `explore_priority` scores. The top domain is the *suggested* target.

**CRITICAL:** Do NOT blindly research the top domain. Proceed to Phase 2 (saturation check).

---

## Phase 2: Domain Saturation Check (Meta-Loop Preview)

**Goal:** Verify the top domain is actually undercovered on disk, not just in the DB.

### 2a. Filesystem saturation batch check
Check the top domain and 4-5 alternatives in one command:

```bash
for d in DOMAIN1 DOMAIN2 DOMAIN3 DOMAIN4 DOMAIN5; do
  pattern="${d//[-_]/.*}"
  count=$(ls ~/wiki/concepts/ 2>/dev/null | grep -ci "$pattern")
  echo "$d: $count"
done
```

**Separator normalization (CRITICAL):** `domain_certainty.py` uses underscores (`agent_frameworks`) while wiki filenames almost always use hyphens (`agent-frameworks`). Normalize both to `.*` via `${d//[-_]/.*}`. Without this, domains with underscores will severely undercount.

### 2b. Recency check
A domain with 7 files total but 5 from today is MORE saturated than one with 10 files all from last month:

```bash
ls -lt ~/wiki/concepts/ | grep -i "<domain>" | head -5
```

### 2c. Pivot decision
- **If top domain < 3 files and none from today:** Research it.
- **If top domain is saturated:** Descend the explore_priority list and repeat 2a/2b.
- **If 5+ listed domains are all saturated:** Fall back to zero-tip SOMA-relevant batch check (see below).

**DB vs filesystem mismatch:** `domain_certainty.py` measures coverage from DB tips, not wiki files. A domain can show low DB coverage (e.g., `agi-experience`: 5 tips, 0.100 coverage) while having 70+ wiki files already saved. Always cross-reference with filesystem counts.

### Zero-Tip Domain Fallback
When `domain_certainty.py` only lists domains with ≥1 DB tip, many SOMA-relevant domains may have **0 tips** and never appear in the explore_priority list. If listed domains are all saturated, run:

```bash
for d in medical-terminology bilingual spanish anatomy 3d-anatomy cross-section soma fhir hl7 dicom medical-ai clinical-copilot hipaa medical-content medical-encyclopedia webgpu-mobile threejs-mobile mobile-rendering z-anatomy bodyparts3d mimic-iv glb ios wkwebview; do
  pattern="${d//[-_]/.*}"
  count=$(ls ~/wiki/concepts/ 2>/dev/null | grep -ci "$pattern")
  echo "$d: $count"
done
```

Pick the first result with 0-2 files and high SOMA relevance. In practice, expect to check 5-10 domains before finding a viable pivot.

### Extended Niche Technical Fallback
**Learned 2026-04-21:** Even the zero-tip fallback list can be fully saturated (all domains had 1+ files from today). When this happens, descend to **implementation-technique domains** — specific algorithms, data formats, shader techniques, and rendering pipelines that are SOMA-relevant but too narrow to appear in broad domain lists. These often have higher direct integration value than generic domains.

Run a second fallback batch focused on technical implementation topics:

```bash
for d in subsurface-scattering clipping-plane stencil-buffer volume-rendering ray-marching mesh-decimation lod texture-compression draco basis-universal ktx2 webgpu-compute wgsl medical-vr ar-vr anatomy-quiz medical-education medical-simulation tissue-rendering procedural-anatomy; do
  pattern="${d//[-_]/.*}"
  count=$(ls ~/wiki/concepts/ 2>/dev/null | grep -ci "$pattern")
  echo "$d: $count"
done
```

**Why this works:** Domains like `clipping-plane` (0 files found) and `ray-marching` (0 files found) are foundational to SOMA's cross-section and volume-rendering features, yet never appear in `domain_certainty.py` because they have zero DB tips. Researching them produces immediately actionable integration proposals.

**Do not give up after the first fallback.** The extended list frequently surfaces productive targets when broader domains are exhausted.

---

## Phase 3: Targeted Research (Entropy)

**Goal:** Research the viable domain identified in Phase 2 and save a wiki page.

### 3a. Iterative query reformulation
Narrow technical subdomains (e.g., `cross-section rendering`, `WKWebView memory limits`) often fail with broad queries. Reformulate progressively:

1. Start broad: `"interactive 3D anatomy cross-section rendering WebGPU"`
2. Add technical terms: `"clipping plane"`, `"section plane"`, `"medical visualization"`
3. Add recency or source filters: `"2025"`, `"2026"`, `"GitHub"`
4. Try 3-5 distinct query angles before concluding the topic is uncovered

### 3b. Extraction and synthesis
Use `web_search` + `web_extract` on 2-4 sources. Expect extraction failures:
- Reddit: blocked by scraper policy
- Large PDFs/dissertations: timeout or raw binary
- Dynamic sites/app stores: JavaScript-rendered, empty extraction
- Conference blogs/podcasts: narrative and very long, summarization truncates technical detail

**Documentation-site timeout pitfall (learned 2026-04-21):** Three.js documentation pages (e.g., `threejs.org/docs/pages/ClippingGroup.html`) are massive (>100KB) and almost always trigger extraction timeouts or return truncated navigation menus instead of content. For Three.js topics, rely on `web_search` snippets, example pages (`threejs.org/examples/...`), discourse threads, GitHub issues, and StackOverflow — these extract far more reliably than the official docs.

**Sparse-source synthesis fallback:** When extractions fail but search snippets, titles, and descriptions contain enough signals, synthesize a wiki page anyway:
- Combine fragments with existing domain knowledge
- Explicitly mark confidence of each claim (`Observation:` vs `Confirmed:`)
- The value is connecting fragmented signals into an actionable integration proposal, not finding a single authoritative source

### 3c. Save wiki page
Write to `~/wiki/concepts/<domain>-<topic>-<year>.md` with this structure:

```markdown
# Topic Title

**Date:** YYYY-MM-DD
**Domain:** domain-name
**Confidence:** Observation | Confirmed
**SOMA Impact:** High | Medium | Low

## Why This Matters for SOMA
[Specific relevance to the project]

## Key Findings
[Technical content]

## Sources
1. Source name (URL)

**Pivoted from:** `original-domain` (N files, saturated) → `target-domain` (M files, high relevance)
```

---

## Phase 4: Research → Distillation

**Goal:** Attempt to convert the new wiki page into distilled tips.

```bash
cd ~/hermes-agent && venv/bin/python3 ~/subconscious/research_to_distillation.py
```

**Expected outcomes:**
- **Success:** Reports `tips_created: N` where N > 0
- **Rejection:** `"Research tip seeding disabled — tips must be operational"` with `tips_created: 0`

**Handling rejection:** This is a known pipeline limitation (operational validation threshold may be too strict for cross-domain insights). Do NOT force additional research to "fix" it. Log the rejection and continue. Tips can be manually inserted later if needed.

**Meta-loop empty output:** `meta_loop.py` may also return empty results (`Tip Types: (empty), Domains: (empty), Meta-Insights (0)`). This indicates no recent tip data to analyze or a DB schema issue. Do not block the cycle — log the empty result and continue to research.

---

## Phase 5: Capability Check

**Goal:** Benchmark current tool-planning capability.

```bash
cd ~/hermes-agent && venv/bin/python3 ~/subconscious/tool_planner.py "debug a complex agent system"
```

**Report the plan recommendation and estimated success score.** This provides a longitudinal capability baseline across cycles.

---

## Phase 6: Knowledge Graph Stats

**Goal:** Snapshot system state for trend tracking.

```bash
cd ~/hermes-agent && venv/bin/python3 -c "
import sqlite3; from pathlib import Path
db = sqlite3.connect(str(Path.home() / '.hermes' / 'cerebrum_memory.db'), timeout=5)
nodes = db.execute('SELECT COUNT(*) FROM kg_nodes').fetchone()[0]
edges = db.execute('SELECT COUNT(*) FROM kg_edges').fetchone()[0]
tips = db.execute('SELECT COUNT(*) FROM distilled_tips WHERE confidence >= 0.6').fetchone()[0]
print(f'KG: {nodes} nodes, {edges} edges, {tips} high-conf tips')
db.close()
"
```

---

## End-of-Cycle Summary

Output exactly 3 lines:

```
Domain certainty: [highest explore domain] (saturated/ok, pivoted to [target] if applicable)
Meta-loop: [tip health status or "empty output — known pipeline limitation, continuing"]
System: [N nodes, M edges, K high-conf tips]
```

---

## Anti-Patterns

1. **Do NOT schedule new cron jobs** during this cycle.
2. **Do NOT restart the gateway** during this cycle.
3. **Do NOT blindly research the top domain** from `domain_certainty.py` without checking filesystem saturation.
4. **Do NOT abandon a viable domain** just because sources are fragmented. A synthesis from weak signals + domain knowledge is often more actionable than a perfectly sourced page on a saturated domain.
5. **Do NOT get stuck in infinite pivot loops.** If 10+ domains are checked and all saturated, accept that today's cycle may produce no new research and output the summary anyway.

---

## Integration with Other Skills

- **autonomous-curiosity:** Provides the 7 activity categories and selection algorithm that inform which domains to prioritize during the zero-tip fallback.
- **training-gym-continuous:** The heavy build/test cycle. Run this lightweight research cycle BETWEEN training gym rounds to keep knowledge growing.
- **research-to-distillation:** Covers the wiki→tips pipeline in depth. Refer to it for manual tip insertion fallbacks and deep repo mining.
- **daily-intelligence-scan:** External ecosystem monitoring (GitHub, arXiv trending). Complementary to this cycle's focused domain-deep-dive approach.

## Reference Files
- See `training-gym-continuous/references/autobrowse-debugging.md` for debugging silent autobrowse trace failures (May 2026)

---

## Hardware Separation Rule (CRITICAL)

**Self-improvement infrastructure runs on the MacBook Pro (Apple Silicon).**
**DGX Spark is ONLY for Qwen 27B training.**

Never confuse the two systems:
- LLM judge (Elo tournaments): DeepSeek v4 pro via Z.AI coding API → MacBook
- Cortex DB, autobrowse, training gym daemon → MacBook
- vLLM serving, model merge, evaluation → DGX Spark (post-training only)

User gets angry when these systems are confused. Always verify which machine a command targets before executing.
