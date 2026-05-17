# depro-test-driven-debugging-2026

*Researched: 2026-04-05 02:51 CDT*

# DePro: Test-Case-Driven Debugging with Iterative LLM Refinement (Mar 2026)

## Paper: arXiv 2603.19399

## Core Concept
DePro: a test-case-driven approach that corrects existing code rather than generating new solutions. Combines brute-force reference generation, stress testing, and iterative LLM-guided refinement.

## Key Findings
1. Test-case-driven debugging is more effective than regeneration
2. Iterative refinement (fix-test-fix cycle) consistently produces correct solutions
3. Stress testing (random input generation) helps find edge cases
4. Reduces debugging attempts significantly

## What We Already Have
- `iterative_fix` strategy in Fluid Reasoning ✓
- Error pattern detection (TS, PY, GIT, DOCKER, NETWORK) ✓
- Tool intelligence tracks success/failure per tool ✓

## What We're Missing
- **Test-case generation**: Automatically generate test inputs to verify fixes
- **Stress testing**: Random input generation for edge cases
- **Regression detection**: Detect when a fix breaks something else
- **Brute-force reference**: Generate a known-correct solution to compare against

## Action Items for DEVELOPMENT Domain
1. Add test-case generation to the iterative_fix strategy
2. Create a regression detection tool
3. Add stress testing for Python/TS code


## Sources

- https://arxiv.org/html/2603.19399v1
