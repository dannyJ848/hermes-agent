# evotool-blame-aware-tool-use-optimization

*Researched: 2026-04-04 23:34 CDT*

# EvoTool: Blame-Aware Tool-Use Policy Optimization

**Paper:** arxiv:2603.04900 (March 2026, University of Melbourne)
**Authors:** Shuo Yang, Soyeon Caren Han et al.

## Key Insight for Evey

Tool-use failures should be blamed on specific modules, not retried blindly. EvoTool decomposes tool-use into 4 stages and attributes failure to the exact stage that caused it.

## The 4 Modules of Tool-Use Policy

1. **Planner** — Decomposes the task into sub-goals and decides which tools to use
2. **Selector** — Chooses the specific tool from available options
3. **Caller** — Constructs the correct arguments and invokes the tool
4. **Synthesizer** — Integrates tool output into the response

## The 3 Mechanisms

### 1. Trajectory-Grounded Blame Attribution
When a tool call fails, don't retry identically. Instead:
- Trace the trajectory: which module made the decision that led to failure?
- Common blame patterns:
  - Planner error: Wrong sub-goal decomposition
  - Selector error: Right goal, wrong tool chosen
  - Caller error: Right tool, wrong arguments (shell escaping, missing params)
  - Synthesizer error: Right output, wrong interpretation

### 2. Feedback-Guided Targeted Mutation
Once blamed, only edit the failing module:
- Don't rewrite the entire approach
- Generate a natural-language critique of the specific module
- Mutate only that module's prompt/logic

### 3. Diversity-Aware Population Selection
Keep multiple candidate policies, preserve diverse approaches:
- Don't converge on a single strategy
- If Strategy A fails on task type X, Strategy B might work
- Maintain a population of 5+ candidate approaches

## Application to Evey's 10% Terminal Success Rate

The dominant failure pattern is **Caller errors** (shell escaping):
- **Blame:** The Planner and Selector are correct (I know I need terminal, I pick the right command conceptually), but the Caller fails at argument construction (f-string escaping, special characters)
- **Fix:** The Caller module needs different mutation — use heredoc Python scripts instead of inline shell
- **Population:** Maintain 2-3 calling strategies (inline shell, heredoc Python, execute_code) and select based on complexity

## Performance Claims
- Outperforms baselines by 5+ points on GPT-4.1 and Qwen3-8B
- Superior transferability across benchmarks
- Gradient-free (works with any LLM, no fine-tuning needed)

## Source
- Paper: https://arxiv.org/html/2603.04900v1
- Related repo: https://github.com/YoungDubbyDu/LLM-Agent-Optimization (survey companion)


## Sources

- https://arxiv.org/html/2603.04900v1
- https://github.com/YoungDubbyDu/LLM-Agent-Optimization
