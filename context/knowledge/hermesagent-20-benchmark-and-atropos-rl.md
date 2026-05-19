# HermesAgent-20-benchmark-and-atropos-rl

*Researched: 2026-04-17 21:10 CDT*

# HermesAgent-20 + Atropos: Agent-Specific Evaluation & RL Training

## HermesAgent-20 (stevibe/BenchLocal)
20 scenarios extracted from Hermes Agent source code, run against a REAL Hermes instance.
This is THE benchmark for evaluating whether a model can power the Hermes agent effectively.

### 20 Scenario Types
| Category | Scenarios | What It Tests |
|----------|-----------|---------------|
| Memory & Recall | HA-01 to HA-04 | memory_replace, near_capacity, reject_injection, session_recall |
| Code Execution | HA-05, HA-07 | fix_failing_test, execute_code_summary |
| Process Management | HA-06 | background_process_management |
| Browser | HA-08 | browser_export_csv |
| Skills | HA-09 to HA-12 | skill_create, skill_discover_apply, skill_patch, skill_supporting_file |
| Cron | HA-13 to HA-15 | cron_create, cron_update, cron_run_delivery |
| Messaging | HA-16 | send_message_target |
| Delegation | HA-17 | parallel_delegation |
| Approval/Retry | HA-18 to HA-20 | approval_gated_delete, retry_after_failure, clarify_ambiguous |

### Integration
- Requires BenchLocal desktop app (v0.2.0+) OR standalone verifier Docker container
- Verifier runs on port 4010, checks actual Hermes agent interactions
- Deterministic: same prompt → same expected outcome
- Can be used as GRPO reward signal for agent-specific RL training

## Atropos (NousResearch/atropos)
Official RL training framework for Hermes Agent. Uses GRPO with tool-context reward.

### Key Feature: ToolContext
Reward functions can access the EXACT sandbox the model used:
```python
async def compute_reward(self, item, result, ctx: ToolContext):
    test = ctx.terminal("pytest -v")
    if test["exit_code"] == 0:
        return 1.0
```

### Two-Phase Operation
- Phase 1 (OpenAI Server): Eval/SFT — server handles tool parsing
- Phase 2 (VLLM ManagedServer): Full RL — client-side Tool Call Parsers needed
  - Supports: hermes, qwen3_coder, deepseek_v3_1, mistral, llama3_json

### Available Benchmarks
| Benchmark | Tasks | Focus | Sandbox |
|-----------|-------|-------|---------|
| TerminalBench2 | 89 | Coding/Sysadmin (binary pass/fail) | Modal Docker |
| TBLite | 100 | Calibrated difficulty (2.6-8x faster TB2) | Modal Docker |
| YC-Bench | 9 | Long-horizon strategy (startup CEO sim) | Local |

### Training Pipeline for Qwen3.6
1. Run HermesAgent-20 on base Qwen3.6 → get weak areas
2. Create Atropos environment targeting weak scenarios
3. GRPO with ToolContext reward (binary pass/fail in sandbox)
4. Re-run HermesAgent-20 → measure improvement
5. Iterate

### Self-Evolution Pipeline (NousResearch/hermes-agent-self-evolution)
DSPy+GEPA optimizer that evolves skills, prompts, tool descriptions.
No GPU training — operates via API calls only.
Four tiers: Skill Files → Tool Descriptions → System Prompt → Code Evolution


## Sources

- https://github.com/stevibe/HermesAgent-20
- https://github.com/stevibe/BenchLocal
- https://hermes-agent.nousresearch.com/docs/developer-guide/environments
- https://github.com/NousResearch/atropos
- https://github.com/NousResearch/hermes-agent-self-evolution
