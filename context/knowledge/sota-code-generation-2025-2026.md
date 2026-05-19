# sota-code-generation-2025-2026

*Researched: 2026-04-05 18:09 CDT*

# SOTA AI Code Generation 2025-2026

## Key Paradigms

### 1. Self-Correcting Code Generation
- **Execute-Analyze-Correct** loop: Agent generates → runs → reads error → patches
- **Self-Reflection**: Feed ONLY the error trace (not original prompt) to a "debugger" mode
- **LATS (Language Agent Tree Search)**: Generate multiple fixes, evaluate with unit tests, Monte Carlo Tree Search for best path

### 2. Test-Driven Agent Coding
- **Reverse TDD**: Agent writes tests FIRST based on issue description, verifies they fail, then writes code until they pass
- **Fuzzing**: Use hypothesis/quickcheck to generate thousands of random inputs for edge case detection
- **Execution Sandboxing**: Docker containers for safe test execution

### 3. Multi-File Context Management
- **AST-Driven RAG**: Parse code into Abstract Syntax Trees, traverse to pull in exactly the right context
- **Repo-level Knowledge Graphs**: Dynamic graphs show which files import which — editing utils.py alerts to 14 dependents
- **Repo Bundling (repomix)**: Flatten whole repo into single XML/Markdown, filtering noise

### 4. Benchmarks
- **HumanEval is "solved"** (>95% by standard models)
- **SWE-bench Verified**: Gold standard. Top agents achieve 35-50% resolution (junior developer level)
- **SWE-bench Multimodal**: Newer variant

## Top 3 Systems

### OpenHands (All-Hands-AI/OpenHands)
- Sandboxed Docker architecture, multi-modal browsing
- Self-correcting loop via terminal output observation
- Strict action/observation space protocol

### SWE-agent (princeton-nlp/SWE-agent)
- **Agent-Computer Interface (ACI)**: Specialized bash commands (find_file, search_dir, edit_file)
- **History Condensation**: Periodic summarization to prevent context overflow
- Context management is key to multi-file success

### AutoCodeRover (nus-apr/auto-code-rover)
- **Spectrum-Based Fault Localization**: Code profiling tells AI exactly which lines crash
- **Strata Navigation**: Class definitions → method signatures → specific lines (hierarchical)
- **Test-Driven Patching**: Generate tests to validate hypotheses before final patch

## Relevance to Evey
- Our Iteration Engine already does Execute-Analyze-Correct
- **GAP**: No AST-Driven RAG — we use raw text search
- **GAP**: No repo-level knowledge graph
- **GAP**: No test-driven self-correction (we don't auto-generate tests)
- **ENHANCEMENT**: Adopt SWE-agent's "History Condensation" for our context management
- **ENHANCEMENT**: AutoCodeRover's strata navigation could enhance our code exploration


## Sources

- https://github.com/All-Hands-AI/OpenHands
- https://github.com/princeton-nlp/SWE-agent
- https://github.com/nus-apr/auto-code-rover
