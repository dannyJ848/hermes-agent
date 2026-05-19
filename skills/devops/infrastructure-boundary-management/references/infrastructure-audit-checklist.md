# Infrastructure Audit Checklist

Run this before any action that touches hardware or systems.

## Pre-Action Checklist

- [ ] Which system should this run on? (MacBook / DGX / VPS)
- [ ] Does this task match that system's defined purpose?
- [ ] Am I using the correct API/provider for this system?
- [ ] Have I confirmed SSH access if needed?
- [ ] Will this action confuse the boundary between systems?

## Quick Reference

| Task | System | Provider/API | Path |
|------|--------|-------------|------|
| Qwen training | DGX | N/A (local GPU) | /data/SpecForge/custom_dflash/ |
| Training log check | DGX (via SSH) | N/A | /mnt/bigssd/train_r256_final.log |
| Autobrowse pipeline | MacBook | N/A (local plugin) | ~/.hermes/plugins/distillation/ |
| Elo tournament | MacBook | DeepSeek API | ~/subconscious/llm_judge.py |
| Tip distillation | MacBook | DeepSeek API | ~/.hermes/plugins/distillation/ |
| Strategy update | MacBook | N/A (local file) | ~/subconscious/strategy.md |
| Model evaluation | DGX | N/A (local GPU) | evaluate_model.py |
| Model deployment | DGX | vLLM (local) | deploy_hermes_qwen.sh |

## Failure Modes

- **Cross-system execution**: Running MacBook code on DGX or vice versa
- **Wrong provider**: Using Z.AI coding API instead of DeepSeek API for judge
- **Local inference resurrection**: User deleted all local inference servers — never suggest recreating them
- **SSH confusion**: Forgetting which system you're SSH'd into and running wrong commands
