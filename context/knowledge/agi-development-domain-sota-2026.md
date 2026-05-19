# agi-development-domain-sota-2026

*Researched: 2026-04-05 22:22 CDT*

# AGI DEVELOPMENT Domain: SOTA Code Generation 2026

## Key Techniques to Integrate

### 1. AST-Based Repo Maps (Aider pattern)
- tree-sitter parsing for function signatures, class defs, imports
- Compressed "map" showing definitions not implementations
- Ranked by relevance (tag frequency, import distance)
- **We have this**: code_intelligence.py already does AST chunking

### 2. Agent-Computer Interface (SWE-Agent pattern)
- LLM-friendly shell environment with structured output
- Auto-lint after every edit
- Windowed file reading (100 lines at a time)
- **Gap**: Hermes patch tool is close but no auto-lint cycle

### 3. Multi-Model Architect (Aider pattern)
- Strong planner model + fast editor model
- Plan in natural language, edit as diffs
- **We have this**: delegate_task with different models

### 4. Repository-Level RAG (RepoGraph pattern)
- Dynamic AST + data/control flow graphs
- When reading a function, auto-inject callers/callees
- **Partial**: code_intelligence.py has AST but not flow graphs

### 5. Reverse TDD (Test-First Issue Resolution)
- Write failing test first, then fix the code
- Symptom vs Root-Cause distillation
- **Gap**: No automated test generation

### 6. Self-Healing Code Loop
- Generate → Execute → Observe Trace → Repair
- Backtracking when regressions detected
- **We have this**: patch tool + terminal for execution

### 7. Orchestrator-Worker Architecture
- Planner creates "Change Manifest" (list of files + changes)
- Worker agents apply diffs concurrently
- **We have this**: delegate_parallel + squad profiles

## Priority Improvements for Evey
1. Add tree-sitter flow graph to code_intelligence.py
2. Build auto-test generator (DePro-inspired)
3. Build "Change Manifest" planner for multi-file edits
4. Wire regression detection into patch cycle


## Sources

- research delegation: SWE-bench 2026 performers
- research delegation: autonomous coding frameworks
- research delegation: reasoning for code generation
