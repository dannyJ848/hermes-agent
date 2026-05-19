# GRPO-execution-verified-training-pipeline

*Researched: 2026-04-17 20:47 CDT*

# GRPO Execution-Verified Training Pipeline for Qwen3.6-35B-A3B

## Core Insight
SFT teaches a model to SOUND smart. GRPO with execution verification teaches it to BE smart.
The key difference: GRPO rewards are objective and binary (code compiles, tests pass, proofs typecheck, math equals correct answer).
No LLM judge needed for the core reward signal.

## The 4-Layer Training Stack

### Layer 1: SFT Foundation (ALREADY BUILT — 7.93M examples)
- Teaches structure of reasoning (reflection, backtracking, verification patterns)
- Data mix: math 35%, code 20%, medical 15%, tool-calling 15%, STEM 15%
- Key: structure matters more than content (corrupting step content drops 3-4%, corrupting structure drops 12-14%)

### Layer 2: GRPO with Execution Verification (NEW — the force multiplier)
- Code: unit test pass/fail = reward (binary, objective, free)
- Math: correct numerical answer = reward
- Formal proof: Lean4 typechecker = reward (machine-verifiable logic)
- Logic puzzles: correct answer = reward
- Each prompt generates 8-16 reasoning paths, reward those that pass verification
- Uses VERL format (see sungyub/rstar-coder-verl for format reference)

### Layer 3: Agentic Coding Traces (NEW — teaches debugging loop)
- Model writes code → runs → reads error → fixes → passes
- This is the "street smart" of coding: knowing what to do when things break
- Datasets: Code-Feedback (68K), CodeAct (78K), SWE-bench train

### Layer 4: Self-play (FUTURE — compounding improvement)
- Model generates its own problems and verifies solutions against execution
- Creates infinite training loop with zero human data

## Critical Datasets for Execution-Verified Training

| Dataset | Examples | Reward Type | Format | Notes |
|---------|----------|-------------|--------|-------|
| rStar-Coder-VERL | 386K | Test case pass/fail | VERL | Ready for RL training, test cases included |
| rStar-Coder (original) | 580K | Test case pass/fail | Parquet | Long-reasoning solutions |
| Code-Feedback | 68K | Execution feedback | Multi-turn | Write-run-fix coding traces |
| Eurus-2-RL-Data | 482K | Test case pass/fail | VERL | Math + coding, outcome verifiers |
| APPS | 10K | Test suite pass/fail | JSON | Code generation benchmark with tests |
| CodeContests-O | ? | Feedback-driven tests | Parquet | Enhanced CodeContests with generated test cases |
| LeanDojo | 91K | Lean4 typechecker | Parquet | Theorem proving with proof checker |
| Lean4-Mathlib | 193K | Lean4 typechecker | Parquet | Formal proofs from Mathlib4 |
| CodeAct | 78K | Tool execution | Parquet | Code-as-action agent traces |
| SWE-bench | 2K | Test pass/fail | JSON | Real GitHub issue fixing |

## Key Papers

1. **Execution-Grounded Credit Assignment for GRPO** (arXiv:2603.16158, accepted ICLR 2026)
   - GRPO-style updates suffer from coarse credit assignment in code
   - Solution: assign credit based on individual test case outcomes, not just overall pass/fail
   - Per-test-case rewards improve training convergence significantly

2. **DRA-GRPO** (arXiv:2505.09655)
   - GRPO needs diverse reasoning paths for mathematical reasoning
   - Generating diverse solution paths improves sample efficiency

3. **CodeRL+** (arXiv:2510.18471)
   - Execution semantics alignment into RLVR pipeline
   - Integrates compilation/execution feedback into reward model

4. **rStar-Coder** (arXiv:2505.21297, Microsoft)
   - 418K problems, 580K reasoning solutions
   - Test cases of varying difficulty for verification
   - Specifically designed for RL training with execution verification

## GRPO Training Architecture for DGX Spark

```
Qwen3.6-35B-A3B (BF16) on Spark (128GB unified)
  ↓
vLLM serves model for sampling (8-16 paths per prompt)
  ↓
Execution sandbox runs code/tests/proofs
  ↓
Reward: binary pass/fail per test case
  ↓
GRPO update: reinforce successful paths, suppress failures
  ↓
Repeat across ~1M+ prompts
```

### Hardware Considerations
- Spark has 128GB unified memory — can serve Qwen3.6 and run sandboxed code simultaneously
- vLLM with FP8 KV cache: 4-6 concurrent sessions
- Sandboxing: Docker container for code execution (security)
- GRPO needs ~50-100 gradient updates per epoch, each requiring N samples from current policy
- Estimated throughput: 1000 GRPO updates/day on single Spark

### VERL Format Reference
The rstar-coder-verl dataset uses VERL (Volcano Engine RL) format:
- `data_source`: problem origin
- `prompt`: list of chat messages (user query)
- `ability`: task type (code/math)
- `reward_model`: ground truth for verification (test cases, expected answers)
- `extra_info`: additional metadata

This format is directly compatible with TRL's GRPOTrainer.


## Sources

- https://arxiv.org/abs/2603.16158
- https://arxiv.org/abs/2505.09655
- https://huggingface.co/datasets/sungyub/rstar-coder-verl
- https://huggingface.co/datasets/microsoft/rStar-Coder
- https://huggingface.co/datasets/m-a-p/Code-Feedback
- https://huggingface.co/datasets/PRIME-RL/Eurus-2-RL-Data
- https://huggingface.co/datasets/tasksource/leandojo
