# meta-harness-terminal-bench

*Researched: 2026-04-01 22:52 CDT*

# Meta-Harness — 76.4% on Terminal-Bench 2.0

**Source:** [stanford-iris-lab/meta-harness-tbench2-artifact](https://github.com/stanford-iris-lab/meta-harness-tbench2-artifact) (★438)

## Results
| Split  | N  | Score |
|--------|---:|------:|
| Easy   |  4 | 100.0 |
| Medium | 55 | 81.1 |
| Hard   | 30 | 64.7 |
| **All**| 89 | **76.4** |

## Key Innovation: Environment Bootstrapping

Before the agent loop starts, Meta-Harness gathers a snapshot of the sandbox environment:
- Working directory contents
- File listing
- Available languages/tools
- Package managers
- Available memory

This snapshot is injected into the initial prompt, **saving 2-5 early exploration turns** that agents normally spend on `ls`, `which python3`, etc.

## Method
- Built on top of KRAFTON AI's Terminus-KIRA agent + Harbor's Terminus-2 framework
- Uses Claude Opus 4.6
- 89 tasks × 5 trials
- 20 turns per attempt
- The agent scaffold was **discovered through automated harness evolution** (not hand-designed)

## Relevance to SOMA
1. **Environment bootstrapping**: SOMA agents should inject environment state (project structure, available tools, build status) into their initial context rather than discovering it each session
2. **Harness evolution**: The scaffold itself was evolved automatically — validates the GEPA/self-evolution approach
3. **Terminal-first**: Shows that terminal agents can achieve high reliability on complex tasks

## Usage
```bash
pip install harbor
export ANTHROPIC_API_KEY=***
harbor run \
  --agent-import-path agent:AgentHarness \
  -d terminal-bench@2.0 \
  -m anthropic/claude-opus-4-6 \
  -e runloop \
  -n 20 \
  --n-attempts 5
```


## Sources

- https://github.com/stanford-iris-lab/meta-harness-tbench2-artifact
