# System-to-Workload Mapping

## MacBook Pro (Apple Silicon)

**Purpose:** Hermes Agent self-improvement, cognitive infrastructure, tip distillation

**What lives here:**
- `~/.hermes/plugins/distillation/__init__.py` — Distillation plugin with autobrowse hooks
- `~/subconscious/` — All autobrowse modules (tracer, analyzer, synthesizer, graduator)
- `~/subconscious/llm_judge.py` — LLM judge for Elo tournaments
- `~/subconscious/strategy.md` — Compounding strategy document
- `~/.hermes/cerebrum_memory.db` — Cortex DB (13K+ nodes, 388K edges)
- `~/.hermes/config.yaml` — Provider config (deepseek-v4-pro)

**What NEVER lives here:**
- Model training (GPU insufficient)
- vLLM serving (no GPU)
- Local inference servers (user deleted all: llama.cpp, phi3, 8B, embedding)

## DGX Spark (130GB GPU)

**Purpose:** Qwen 27B training and deployment ONLY

**What lives here:**
- `/data/SpecForge/custom_dflash/train_lora_sae_teacher_v1.py` — Training script
- `/mnt/bigssd/train_r256_final.log` — Training log
- `/data/SpecForge/custom_dflash/MASTER_DOC.md` — Training state documentation
- `/data/SpecForge/custom_dflash/instant_context.py` — Context helper
- `merge_model.sh`, `evaluate_model.py`, `deploy_hermes_qwen.sh` — Post-training pipeline

**What NEVER lives here:**
- Autobrowse pipeline (no Hermes agent installed)
- Elo tournaments (no judge infrastructure)
- Tip distillation (no cortex DB)

## SSH Bridge

MacBook can SSH to DGX for status checks and file sync. The SSH config is managed by NVIDIA Sync:
```bash
# Config location (not standard ~/.ssh/config)
# Host: spark-85e8.local
# User: djg6228
# Key: /Users/dannygomez/Library/Application Support/NVIDIA/Sync/config/nvsync.key

ssh djg6228@spark-85e8.local
```

**Pitfall:** Do NOT assume `dgx` or `192.168.1.100` as the hostname. Always check `~/.ssh/config` and any `Include` directives for the actual host.

**Training status check workflow:**
```bash
# 1. Verify process is running
ssh spark-85e8.local 'ps aux | grep train_lora_sae_teacher'

# 2. Read latest log entries (log path is dynamic, check /proc/PID/fd/)
ssh spark-85e8.local 'tail -20 /mnt/bigssd/train_r256_final.log'

# 3. Parse step progress
ssh spark-85e8.local 'grep "Step [0-9]*/10000" /mnt/bigssd/train_r256_final.log | tail -5'
```

Training log format: `Step X/Y | Loss: N (CE:N D:N SAE:N) | W:(N,N,N) | LR: N | GPU: NGB`
Steps logged every 20s with "Skipping log for step N" for intermediate batches.

But only run DGX-appropriate commands through that SSH session.

## Cost Structure

| System | Cost Driver | Rate |
|--------|------------|------|
| MacBook | DeepSeek API (judge) | $0.109/$0.218 per 1M tokens (75% discount until 2026-05-31) |
| DGX | Electricity + amortized hardware | N/A (user-owned) |

## History of Boundary Violations

1. **2026-04-07**: Confused DGX Spark with MacBook for self-improvement infra — user angry
2. **2026-04-07**: Confused Z.AI coding API with DeepSeek API for LLM judge — user angry
3. **2026-04-07**: Suggested local inference servers after user deleted them — user angry
4. **2026-05-09**: Autobrowse pipeline fixed on MacBook (correct), but initial confusion about where it runs — user corrected
5. **2026-05-09**: Tried `ssh dgx` and `ssh 192.168.1.100` before finding correct host `spark-85e8.local` — SSH config discovery needed

## Rule

**When the user says "this runs on X, NOT Y", that is a permanent constraint. Never violate it.**
