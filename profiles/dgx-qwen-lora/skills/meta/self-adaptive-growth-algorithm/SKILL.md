---
name: self-adaptive-growth-algorithm
version: 1.0
created: 2026-04-02
description: Self-adaptive algorithm for exponential agent growth. Inspired by FSRS (spaced repetition), GEPA (genetic prompt evolution), and Phantom (self-evolution). The agent teaches itself new tools, analyzes programs, designs algorithms, and compounds knowledge over time.
tags: [self-improvement, growth, algorithm, spaced-repetition, evolution, meta]
---

# Self-Adaptive Growth Algorithm (SAGA)

## Philosophy
The agent is a lifelong learner that compounds knowledge exponentially. Every session builds on all previous sessions. The algorithm combines:
- **FSRS-inspired memory**: Track stability/difficulty/retrievability of every learned tool/concept
- **GEPA-inspired evolution**: Read full execution traces, reflect, mutate approaches
- **Phantom-inspired validation**: 5 gates before any self-modification
- **Meta-Harness bootstrapping**: Scan environment before every task

## Core Algorithm

### Phase 1: DISCOVER (Continuous)
Every session and cron run:
1. Scan GitHub trending (daily), arXiv new papers, HackerNews top
2. For each discovery, compute RELEVANCE score:
   ```
   RELEVANCE = (novelty * 0.25) + (soma_utility * 0.30) + (community * 0.20) + (integrability * 0.25)
   ```
   - novelty: 0-25 (does something new?)
   - soma_utility: 0-30 (helps underserved medical communities?)
   - community: 0-20 (stars, activity, maintenance)
   - integrability: 0-25 (can Hermes/SOMA use it directly?)

2b. If RELEVANCE >= 75: add to SKILL_BACKLOG with priority
2c. If RELEVANCE >= 90: create skill immediately

### Phase 2: LEARN (Per-Skill)
For each tool/concept in backlog:
1. **Read**: Extract docs, README, API reference (web_extract)
2. **Deconstruct**: Break into components (install, core API, patterns, pitfalls)
3. **Practice**: Write minimal working example in terminal
4. **Document**: Create SKILL.md with YAML frontmatter + structured content
5. **Score**: Rate learning quality 0-10, log in knowledge base

### Phase 3: RETAIN (FSRS-Based)
Each learned skill has memory state (DSR):
- **D**ifficulty: How hard was it to learn? (initial: 5.0, range 1-10)
- **S**tability: Days until retention drops to 90% (initial: 1.0)
- **R**etrievability: Current recall probability (decays daily)

```python
# Simplified FSRS for skill retention
def compute_review(skill, days_since_last_review):
    R = (1 + days_since_last_review / (9 * skill.stability)) ** -1
    
    if R < 0.85:  # Below 85% recall threshold
        return "REVIEW"  # Re-read the skill, practice again
    return "SKIP"  # Still fresh, move on

def update_after_review(skill, quality):  # quality: 0-5
    if quality >= 3:
        skill.stability *= (1 + 0.5 * (quality - 2))  # Stabilize
    else:
        skill.stability *= 0.5  # Forgetting occurred
        skill.difficulty = min(10, skill.difficulty + 0.5)
```

### Phase 4: APPLY (Real Tasks)
When a real task arrives:
1. Search knowledge base for relevant skills
2. Load top 3 most relevant skills
3. Apply with adaptation -- patch skill if gaps found
4. Record outcome (success/failure/partial)
5. Update skill's quality score and DSR values

### Phase 5: EVOLVE (Constitution-Based)
Every 10 sessions, full evolution cycle:
1. **Observe**: Review all skill usage patterns
2. **Consolidate**: Merge overlapping skills, prune dead ones
3. **Mutate**: Improve top-used skills based on execution traces
4. **Validate**: Run 5 gates:
   - Constitution: Does change violate core safety/honesty?
   - Regression: Does it break previously working patterns?
   - Size: Is the skill getting bloated? (max 500 lines)
   - Drift: Has the skill drifted from its purpose?
   - Safety: Could this harm the user or patients?
5. **Deploy**: Patch skill, update knowledge base
6. **Rollback**: If quality degrades within 3 uses, revert

## Exponential Growth Mechanism

### Compounding Knowledge Graph
```
KNOWLEDGE_NODES = {}  # tool/concept -> {learned, practiced, applied, quality}

# Each learned tool unlocks N adjacent tools:
def get_adjacent(tool):
    ADJACENCY = {
        "Three.js": ["React Three Fiber", "GLSL shaders", "WebGL", "Blender Python"],
        "Whisper": ["faster-whisper", "WhisperSpeech", "Bark", "FFmpeg"],
        "BioMCP": ["Healthcare MCP", "FHIR", "DICOM", "OpenFDA"],
        "Ghidra": ["radare2", "Binary Ninja", "capstone", "frida"],
        "Python AST": ["pylint", "mypy", "Cython", "ctypes"],
        # ... auto-extended as new tools are learned
    }
    return ADJACENCY.get(tool, [])
```

### Growth Curve
- Week 1-2: Foundation (10 skills) - core tools
- Week 3-4: Expansion (25 skills) - adjacent domains
- Week 5-8: Deepening (50 skills) - mastery within domains
- Week 9-12: Synthesis (80+ skills) - cross-domain combinations
- Week 13+: Compound (100+) - creating novel combinations

## Reverse Engineering Pipeline

### For any application/program:
1. **Identify**: What type? (Electron, Tauri, native, web, mobile)
2. **Unpack**: Extract source/assets
   - Electron: `asar extract app.asar app/`
   - Tauri: Extract from binary with resource section tools
   - Web: Browser dev tools, webpack bundle analyzer
   - Native: Ghidra/radare2 disassembly
3. **Map**: Generate dependency graph, identify entry points
4. **Analyze**: Read core algorithm files, trace data flow
5. **Reconstruct**: Rebuild key components from understanding
6. **Improve**: Apply learned patterns to create enhanced version

### Algorithm Analysis Template
For any algorithm (like Anki's SM-2/FSRS):
1. Extract pseudocode from source/docs
2. Identify inputs, outputs, state variables
3. Map to mathematical model (e.g., FSRS = DSR memory model)
4. Reproduce in Python with tests
5. Benchmark against original
6. Identify improvement opportunities
7. Design enhanced version with justification

## Session Integration
At start of every session:
1. Check DSR scores for all skills
2. Review any skills with R < 0.85
3. Check skill backlog for new tools to learn
4. Apply one adjacent tool discovery
5. Record all activity to knowledge base

## Cron Schedule
- **Every session**: Discover + Retain
- **Daily 09:00**: Jack of All Trades scan (discover)
- **Daily 15:00**: Skill review cycle (retain)
- **Daily 03:00**: Dojo analysis (evolve)
- **Weekly**: Full evolution cycle with validation gates

## Measurements
Track these KPIs per week:
- New skills created
- Skills reviewed/practiced
- Skills applied to real tasks
- Average quality score across all skills
- Time from discovery to skill creation
- Cross-domain synthesis events (using 2+ skills together)
