# Cognitive Orchestrator Integration Pattern

## Problem

The iteration engine (7 systems) auto-initializes in `run_agent.py`, but the **cognitive orchestrator (20 subsystems)** does NOT. On fresh deployments or machines where the source hasn't been patched, only the iteration engine runs.

## Detection

Check if the orchestrator is already integrated:
```bash
grep -n 'cognitive_orchestrator\|CognitiveOrchestrator' /path/to/hermes-agent/run_agent.py
```

Empty output = not integrated. Only iteration engine runs.

## Integration Pattern

### Step 1: Find the Anchor Point

Locate the iteration engine initialization block:
```bash
grep -n 'Iteration engine ready' /path/to/hermes-agent/run_agent.py
```

### Step 2: Insert Orchestrator Initialization

Add immediately after the iteration engine's `except` block closes:

```python
        # ── Cognitive Orchestrator: 20-subsystem enhancement suite ────────
        try:
            from agent.cognitive_orchestrator import get_orchestrator
            self.cognitive_orchestrator = get_orchestrator()
            subsystem_status = self.cognitive_orchestrator.initialize(self)
            active_count = sum(1 for v in subsystem_status.values() if v == "active")
            total_count = len(subsystem_status)
            print(f"────────────────────────────────────────")
            print(f"🧠 Cognitive orchestrator ready: {active_count}/{total_count} subsystems active")
            for name, status in subsystem_status.items():
                icon = "✓" if status == "active" else "✗"
                print(f"   {icon} {name}")
            print(f"────────────────────────────────────────")
        except Exception as _co_err:
            logger.warning("Cognitive orchestrator init failed: %s", _co_err)
            self.cognitive_orchestrator = None
```

### Step 3: Verify the Patch

```bash
# Check syntax
python3 -m py_compile /path/to/hermes-agent/run_agent.py

# Check for the new code
grep -A 5 'Cognitive Orchestrator' /path/to/hermes-agent/run_agent.py
```

## Pitfalls

### Quote Stripping via SSH

When patching over SSH, NEVER use heredocs for Python code:
```bash
# WRONG — quotes get stripped
ssh host "cat > /tmp/patch.py << 'EOF'
print(f"hello")  # Becomes: print(fhello)
EOF"
```

**Correct approach:** Write the script locally with `write_file`, then copy to remote:
```bash
# Local: write_file creates the patch script
# Then: scp /tmp/patch.py host:/tmp/patch.py
# Then: ssh host "python3 /tmp/patch.py"
```

### Line Number Drift

The iteration engine block moves between Hermes versions. Always search for the anchor text rather than hardcoding line numbers.

### Missing cognitive_orchestrator.py

If `from agent.cognitive_orchestrator import get_orchestrator` fails with `ModuleNotFoundError`, the orchestrator source file is missing. Check:
```bash
ls -la /path/to/hermes-agent/agent/cognitive_orchestrator.py
```

If missing, sync from the source-of-truth machine (usually MacBook).

## Subsystem List

The cognitive orchestrator initializes these 20 subsystems:

1. Error Recovery Tree
2. LLM Judge
3. Self-Audit Engine
4. Context Quality Guard
5. Tool Misuse Prevention
6. Autobrowse Tracer
7. Agent Loop Optimizer
8. Cognitive Orchestrator (meta)
9. Subconscious Loop
10. Cortex Flywheel
11. Knowledge Compiler
12. Epistemic Trust Scoring
13. Tiered Memory System
14. Brain Cycle
15. Middleware Reasoning Chain
16. Session Immortality
17. Hindsight/Cerebrum Sync
18. Distillation Pipeline
19. Research-to-Distillation
20. Training Gym
21. Tool-Grounded Cognition

## Verification

After patching and restarting Hermes:
```bash
# Check logs for orchestrator initialization
grep 'Cognitive orchestrator ready' /var/log/hermes/gateway.log

# Expected output:
# 🧠 Cognitive orchestrator ready: 20/20 subsystems active
#    ✓ error_recovery_tree
#    ✓ llm_judge
#    ...
```

## Session Reference

- **Date:** May 15 2026
- **Context:** DGX Spark deployment revealed iteration engine (7 systems) loaded but cognitive orchestrator (20 systems) did not auto-initialize
- **Fix:** Patched `run_agent.py` to explicitly initialize `CognitiveOrchestrator` after iteration engine
- **Lesson:** The orchestrator is a newer system that requires explicit integration; it does not auto-load like the iteration engine
