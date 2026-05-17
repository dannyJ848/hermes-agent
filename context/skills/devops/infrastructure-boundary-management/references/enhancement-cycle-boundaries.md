# Enhancement Cycle Boundaries

## What Runs Where During Enhancement Cycles

### MacBook ONLY (Hermes Self-Improvement)

| Task | Why MacBook | Never On DGX |
|------|-------------|--------------|
| Auto-skill generation from knowledge docs | File system access to ~/.hermes/skills/ | DGX has no Hermes install |
| Adversarial tip validation | DeepSeek API calls (cloud LLM) | Wastes GPU for API calls |
| Prompt fragment Elo tournaments | SQLite DB ops, API calls | No GPU benefit |
| Health daemon updates | Cron on MacBook | DGX is training-only |
| Plugin wiring/activation | Hermes CLI runs on MacBook | DGX has no Hermes CLI |
| Database schema updates | ~/.hermes/*.db files local | DGX doesn't share filesystem |

### DGX ONLY (Qwen Training)

| Task | Why DGX | Never On MacBook |
|------|---------|------------------|
| LoRA fine-tuning | Requires 130GB GPU | MacBook has no GPU |
| vLLM model serving | GPU inference | MacBook deleted all local inference |
| Training data push | Large file transfer to DGX | MacBook can't serve models |

### Cross-System Tasks

| Task | MacBook Action | DGX Action |
|------|----------------|------------|
| Training status check | SSH to DGX, parse log | Process runs on DGX |
| Push training data | rsync ~/qwen-training-data/ to DGX | Receive and load |
| Deploy trained model | Initiate vLLM setup via SSH | Run vLLM serve |

## Session Example: Enhancement Cycle 5

**What happened:**
1. Generated skills (MacBook) ✓
2. Adversarial batch with deepseek-chat (MacBook API calls) ✓
3. Prompt fragment updates (MacBook SQLite) ✓
4. Health daemon patch (MacBook cron) ✓
5. Plugin wiring prep (MacBook checks) ✓

**What was NOT done:**
- No model training commands
- No GPU utilization checks
- No DGX file modifications

**Interruption handled correctly:**
- User said "ignore everything related to soma"
- Immediately dropped soma skill generation
- Continued with remaining cycle 5 tasks
- No debate, no completion of interrupted work
