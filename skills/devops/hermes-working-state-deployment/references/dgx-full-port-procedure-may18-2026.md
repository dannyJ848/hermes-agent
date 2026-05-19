# DGX Full Port Procedure (May 18, 2026)

## Context

Porting complete Hermes Agent monolithic apparatus from MacBook to DGX Spark. Includes source code, venv, config, .env, skills, and cognitive orchestrator verification.

## Prerequisites

- SSH access to DGX: `djg6228@spark-85e8.local`
- MacBook has working hermes-agent at `~/.hermes/`
- DGX has clone at `/data/SpecForge/hermes-agent`

## Procedure

### 1. Update DGX Source Code

```bash
ssh djg6228@spark-85e8.local
cd /data/SpecForge/hermes-agent
git fetch origin
git checkout main
git pull origin main
```

### 2. Create Python Virtual Environment

DGX uses Python 3.12.3 (externally managed). Must use venv:

```bash
cd /data/SpecForge/hermes-agent
python3 -m venv venv
venv/bin/pip install -e .
```

**Pitfall**: `pip install -e .` on system Python fails with `externally-managed-environment`. Always use venv.

### 3. Copy Config and Environment

```bash
# From MacBook
scp ~/.hermes/config.yaml djg6228@spark-85e8.local:~/.hermes/
scp ~/.hermes/.env djg6228@spark-85e8.local:~/.hermes/
```

### 4. Sync Skills

```bash
# On DGX
rm -rf ~/.hermes/skills/*
cp -r /data/SpecForge/hermes-agent/skills/* ~/.hermes/skills/
find ~/.hermes/skills/ -name "SKILL.md" -maxdepth 3 | wc -l
# Expected: ~385
```

### 5. Create Symlink

```bash
mkdir -p ~/.local/bin
ln -sf /data/SpecForge/hermes-agent/venv/bin/hermes ~/.local/bin/hermes
```

### 6. Verify Installation

```bash
hermes --version
# Expected: Hermes Agent v0.13.0

hermes doctor
# Expected: 50+ tools enabled, 380+ skills, Kimi API connected
```

## Cognitive Orchestrator Verification

The 20 subsystems in `cognitive_orchestrator.py` plus `iteration_engine.py` (separate) = 21 total learning systems.

Verify wiring in `run_agent.py`:
```bash
grep -n "cognitive_orchestrator" /data/SpecForge/hermes-agent/run_agent.py
# Expected: lines 2130, 10099, 10207, 15055
```

Verify all 20 subsystems present:
```bash
ls /data/SpecForge/hermes-agent/agent/{tiered_memory,error_learning,skill_effectiveness_tracker,brain,cortex_flywheel,distillation_bridge,self_audit_engine,training_gym,memory_cortex_bridge,subconscious_hook_wiring,autobrowse_tracer,adaptive_context_sculptor,predictive_tool_oracle,epistemic_trust_scorer,unified_intelligence_engine,predictive_failure_prevention,autonomous_experimentation,cross_domain_transfer,attention_context_prioritizer,self_evaluation_gate}.py
```

## Key Differences from MacBook

| Aspect | MacBook | DGX |
|--------|---------|-----|
| Python | 3.10 (via symlink) | 3.12.3 |
| Venv | Not used | Required |
| Entry point | `hermes` (system) | `venv/bin/hermes` |
| Tools | 27 (15 enabled) | ~50 (full evey suite) |
| Skills | 384 | 385 |
| Cognitive | Same code, different entry point | Same code, different entry point |

## SSH Quote Pitfall

When running Python scripts via SSH, avoid heredocs with nested quotes. Use `write_file` to create scripts locally, then `scp` to DGX:

```bash
# BAD: nested quotes break
cat > /tmp/test.py << 'EOF'
print("hello")
EOF

# GOOD: write locally, copy
scp /tmp/test.py djg6228@spark-85e8.local:/tmp/test.py
ssh djg6228@spark-85e8.local python3 /tmp/test.py
```

## Post-Port Checklist

- [ ] Git commit matches MacBook (`7f6281ca9` or later)
- [ ] `hermes --version` shows v0.13.0
- [ ] `hermes doctor` passes with < 5 issues
- [ ] Skills count ≥ 380
- [ ] Tools count ≥ 45
- [ ] Kimi/Moonshot API connected
- [ ] Cognitive orchestrator initializes (check logs)
- [ ] `run_agent.py` has cognitive references at expected lines
