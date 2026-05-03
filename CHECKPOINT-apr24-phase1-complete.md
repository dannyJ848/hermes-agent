# DGX Spark Checkpoint - Apr 24 2026 - Phase1 COMPLETE (PAUSED)

## STATUS: Phase1 Hidden States Generation COMPLETE — PAUSED before Phase2
- **10,000/10,000 samples generated** (100%)
- **Total size: 424GB**
- **Location:** /data/SpecForge/custom_dflash/hidden_states_full/
- **Completion time:** Apr 24 ~22:15 CDT
- **PAUSED AT:** Phase2 not yet started

## RESUME COMMAND:
```bash
# On DGX Spark:
ssh djg6228@10.0.0.171
cd /data/SpecForge/custom_dflash
python3 phase2_train_draft.py
```

## NEXT: Phase2 - Train Franken v8 Draft Model
- **Script:** /data/SpecForge/custom_dflash/phase2_train_draft.py
- **Config:** 25 grafts, 15.0M params, Muon optimizer
- **Input:** /data/SpecForge/custom_dflash/hidden_states_full/ (10,000 .pt files)
- **Output:** /data/models/Qwen3.6-27B-DFlash-Custom/
- **Target:** ~40 tok/s with DFlash speculative decoding

## FILES READY:
- phase2_train_draft.py (17KB, Apr 24 20:20)
- convert_dflash_v2.py (4.3KB, Apr 23 22:18)
- resume_phase1.py (for future resumes if needed)

## DISK STATUS:
- /dev/nvme0n1p2: 3.5T used / 3.7T total = 99% full
- 53G free (tight but enough for training)

## MODEL STATUS:
- vLLM serving qwen3.6-27b-uncensored on port 8000
- Base model: /data/models/Qwen3.6-27B-Uncensored
- DFlash draft: NOT YET TRAINED (Phase2 next)

## RESUME INSTRUCTION:
1. SSH to Spark: `ssh djg6228@10.0.0.171`
2. Run: `cd /data/SpecForge/custom_dflash && python3 phase2_train_draft.py`
3. Training will use all 10,000 hidden states to train the 15M param draft model
4. After training completes, run convert_dflash_v2.py to prepare for vLLM integration

## SESSION CONTEXT:
- Hermes v0.11.0
- Kimi K2.6 as main model
- DGX Spark: GB10/Blackwell SM121, 128GB unified memory
- All 6 training datasets on disk (~475GB)
- Phase1 took ~12 hours total (resumed from 9,713)
