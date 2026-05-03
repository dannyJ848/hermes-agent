# MASTER BLUEPRINT: Qwen-Scope SAE Integration + Franken V8 Distillation
# Qwen 3.6-27B-Uncensored Training on DGX Spark (130GB GPU + 121GB RAM)
# Created: May 3, 2026 | Updated: May 3, 2026

================================================================================
GOAL
================================================================================

Integrate Qwen-Scope Sparse Autoencoders (SAEs) into Qwen 3.6-27B-Uncensored
BEFORE training it on the 25-graft Franken V8 teacher distillation dataset.

Make this as complete a fine-tuning as possible for Qwen 3.6-27B.

================================================================================
WHAT WAS ALREADY TRIED (14 FAILED CONFIGURATIONS)
================================================================================

All attempts were on DGX Spark: 130GB GPU + 121GB CPU RAM

| # | Approach | Optimizer | Result | Why It Failed |
|---|----------|-----------|--------|---------------|
| 1 | SGD + bf16 + grad_checkpointing | SGD (momentum=0) | Gradient explosion step 1 (norm=178) | bf16 range exceeded on 27B scale |
| 2 | SGD + SAEs (7 layers) | SGD (momentum=0) | Gradient explosion step 1 | Same root cause |
| 3 | SGD + SAEs (3 layers) | SGD (momentum=0) | Gradient explosion step 1 | Same root cause |
| 4 | SGD + Nesterov momentum | SGD (momentum=0.9) | Gradient explosion step 1 | Same root cause |
| 5 | SGD + adaptive grad clipping | SGD + clip | Gradient explosion step 1 | bf16 instability fundamental |
| 6 | SGD + warmup→momentum | SGD | Gradient explosion after warmup | Same root cause |
| 7 | AdamW on GPU | AdamW | OOM immediately | AdamW states ~108GB > 130GB GPU |
| 8 | DeepSpeed ZeRO-2 | AdamW + DS Z2 | OOM during optimizer init | States too large even sharded |
| 9 | DeepSpeed ZeRO-3 | AdamW + DS Z3 | Hangs during init, exit 255 | Writes 50GB+ swap then dies |
| 10 | bitsandbytes 8-bit AdamW | 8-bit AdamW | OOM killed CPU RAM | 8-bit states still too large for 121GB |
| 11 | FSDP2 single GPU | FSDP2 | Falls back to NO_SHARD | Single GPU = no actual sharding |
| 12 | CPU-offloaded AdamW (fp32) | CPU AdamW | OOM during setup (layer 43/64) | 108GB fp32 states > 121GB CPU RAM |
| 13 | CPU-offloaded SGD (bf16 momentum) | CPU SGD | System froze, swap thrashing | Model+states filled RAM, forward pass impossible |
| 14 | PagedAdamW8bit | 8-bit paged | System frozen, hard reboot required | Paging to CPU fails when CPU RAM full |

CRITICAL FINDING: Full parameter fine-tuning of Qwen 27B is NOT viable on single
130GB GPU + 121GB RAM. Period.

================================================================================
THE ANOMALY: train_sae_only.py
================================================================================

The script at /data/SpecForge/custom_dflash/train_sae_only.py reached step 165
with ~59GB GPU usage, BUT it has a CRITICAL BUG:

  optimizer = torch.optim.SGD(model.parameters(), lr=1e-5)

This optimizes ALL Qwen parameters, not just SAEs. It should have exploded at
step 1 like every other full fine-tuning attempt. That it reached step 165 is
UNEXPLAINED and the checkpoint may be unreliable.

DO NOT resume from sae_step_100.pt without investigation.

================================================================================
WHAT ACTUALLY WORKS
================================================================================

SAE-only training with FROZEN Qwen is the only viable path:

  model.eval()
  for param in model.parameters():
      param.requires_grad = False
  
  # Only SAE parameters are trainable
  sae_params = [...]  # If modifying SAE weights
  optimizer = torch.optim.AdamW(sae_params, lr=1e-5)

Verified working config (before bug discovery):
- Script: train_sae_only.py (NEEDS FIX — see above)
- SAE layers: [16, 32, 48]
- SAE weight: 0.05
- GPU: ~59GB / 130.7GB
- Loss: 1.3-3.2, SAELoss: ~0.20

================================================================================
HARDWARE CONSTRAINTS (DGX Spark)
================================================================================

- GPU: 130.7GB (NVIDIA GB10)
- CPU RAM: 121GB
- SSD: 8TB (/mnt/bigssd)
- CRITICAL: System becomes completely unresponsive when overloaded
- CRITICAL: No swap recovery — requires physical reboot
- CRITICAL: Never push to 100% RAM

Pre-flight checklist:
  free -h    # Confirm >40GB free RAM
  nvidia-smi # Confirm GPU idle

================================================================================
ASSETS & PATHS
================================================================================

Student Model:  /data/models/Qwen3.6-27B-Uncensored/
Teacher Model:  /data/models/FrankenV8-Final/final_model.pt
SAE Files:      /data/models/Qwen-Scope/ (64 files, 201GB)
Dataset:        /data/SpecForge/custom_dflash/hidden_states/ (44 samples)
Code Repo:      /data/SpecForge/custom_dflash/
Checkpoints:    /data/SpecForge/custom_dflash/checkpoints/
Logs:           /mnt/bigssd/*.log
Git:            Commit c35aba0

================================================================================
POTENTIAL PATHS FORWARD (NOT TESTED)
================================================================================

1. fp32 precision with 2+ GPUs (~200GB+ VRAM needed)
2. Multi-GPU DeepSpeed ZeRO-3 with NVMe offload
3. Gradient scaling with torch.cuda.amp.GradScaler
4. Mixed-precision training with loss scaling
5. Selective layer training (last N layers + embeddings)

================================================================================
NEXT CLI SESSION SHOULD:
================================================================================

1. Fix train_sae_only.py to ACTUALLY freeze Qwen parameters
2. Verify or discard sae_step_100.pt (may be corrupted by full fine-tuning)
3. Restart true SAE-only training from scratch or verified checkpoint
4. Consider whether SAE-only training is sufficient for the Franken V8 graft

================================================================================
REPO STATUS
================================================================================

Local commits (NOT pushed to GitHub — no SSH keys on DGX):
  a648ad2 — Final session update: train_full_ft.py modifications
  c35aba0 — Session checkpoint: attempts 7-14 failed, DGX rebooted
  e15106f — COMPLETE CHECKPOINT: all training scripts, SAE-only stable at step 165
  09722ad — Checkpoint: SAE-only stable, full fine-tuning abandoned

Remote: https://github.com/sgl-project/SpecForge.git
Push requires: GitHub token, SSH key, or manual push from credentialed machine

Untracked (data directories — do not commit):
  checkpoints/        — Training checkpoints
  hidden_states/      — Pre-computed hidden states
  hidden_states_full/ — Full hidden states
  teacher_outputs/    — Teacher model outputs

================================================================================
