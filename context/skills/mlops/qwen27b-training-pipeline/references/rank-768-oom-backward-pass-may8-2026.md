# Rank 768 OOM During Backward Pass — May 8, 2026

## Incident

Training with LoRA rank 768 on Qwen 27B was killed by OOM during the second batch's forward pass. No error in log — just cut off.

## Log Timeline

- 17:05: Training started, resumed from checkpoint_step_1500
- 17:06:00: Batch 0 — forward pass (6.5s), loss computed (23.7s), backward pass (14.2s)
- 17:06:45: Batch 1 — forward pass started...
- Then: Process killed (exit code 137 = SIGKILL)

## Memory Analysis

| Component | Rank 256 | Rank 768 |
|-----------|----------|----------|
| Trainable params | ~1.9B | ~3.8B |
| LoRA params (fp16) | ~3.8GB | ~7.6GB |
| Optimizer states (fp32) | ~7.6GB | ~15.2GB |
| Base model (bf16) | ~50GB | ~50GB |
| Activations (seq=512, batch=1) | ~6GB | ~6GB |
| SAEs (3 layers) | ~2GB | ~2GB |
| Teacher (CPU, cached) | ~0GB | ~0GB |
| **Total estimated** | **~69GB** | **~81GB** |
| GPU limit | 130GB | 130GB |
| Headroom | 61GB | 49GB |

At rank 768, total estimated memory is ~81GB. But during backward pass, activation gradients spike memory by 20-40% temporarily. That pushes peak to ~100-115GB — dangerously close to the limit.

## Why It Failed at Batch 1 (Not Batch 0)

Batch 0 succeeded because:
- Forward pass: activations allocated
- Backward pass: gradients computed, then freed
- Optimizer step: parameter updates applied

Batch 1 started forward pass while batch 0's optimizer state was still resident. The memory spike from new activations + existing optimizer states + gradient buffers exceeded the limit.

## Key Insight: Backward Pass Is the Memory Spike

Forward pass is predictable — activations scale with batch size and sequence length.
Backward pass is the killer — it needs:
- Forward activations (kept for gradient computation)
- Gradient buffers (same size as parameters)
- Temporary buffers for optimizer operations

All three coexist momentarily during backward.

## Diagnosis Pattern

When training dies with these symptoms:
1. Log ends mid-step with no error
2. Exit code 137 (SIGKILL)
3. Process was running, had loaded model successfully
4. dmesg shows "Killed process <pid> (python3)"

→ **OOM killer during backward pass.** Not a code bug. Not a deadlock. Pure memory exhaustion.

## Fix Options

**Option A: Reduce rank to 512**
- Trainable params: ~2.5B
- Optimizer states: ~10GB
- Total: ~75GB
- Headroom: 55GB — safe even with backward spikes

**Option B: Reduce grad accum from 4 to 2**
- Effective batch: 2 instead of 4
- Less activation memory per optimizer step
- But: fewer samples per step, slower convergence

**Option C: Enable gradient checkpointing**
- Trades compute for memory
- Saves ~20-30GB on 27B
- Already enabled in current config (use_reentrant=False)

**Option D: Reduce sequence length**
- seq=512 → seq=256
- Activations halved
- But may hurt quality

## What Actually Worked

User chose to try rank 512 after the rank 768 failure. Rank 512 has ~2.5B trainable params, ~10GB optimizer states, total ~75GB — comfortable headroom for backward spikes.

## Prevention Checklist Before Launching Higher Ranks

1. Calculate total memory: base_model + lora_params*2 + activations + saes + 20% backward_spike_buffer
2. If total > 100GB, reduce rank or batch size
3. If total > 110GB, don't launch — will OOM during backward
4. Monitor with `nvidia-smi` in a loop during first 10 steps
5. If memory climbs >100GB in first 5 steps, kill and reduce rank

## User Preference Signal

User said "it ready" after cycling DGX — means SSH responsive and ready for commands. Short phrases like "it ready" or "okay just cycled it" are status confirmations, not requests for analysis.
