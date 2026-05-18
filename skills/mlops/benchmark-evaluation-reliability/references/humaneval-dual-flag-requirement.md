# HumanEval Dual-Flag Requirement

## The Problem

HumanEval in lm-eval-harness is marked as an "unsafe" task because it executes generated code. This requires TWO separate safety mechanisms to be enabled simultaneously.

## The Two Required Flags

### 1. Environment Variable: `HF_ALLOW_CODE_EVAL=1`

Set before running lm_eval:
```bash
export HF_ALLOW_CODE_EVAL=1
```

This tells the HuggingFace datasets library that you acknowledge the risks of executing untrusted code.

### 2. CLI Flag: `--confirm_run_unsafe_code`

Pass to lm_eval command:
```bash
lm_eval --tasks humaneval --confirm_run_unsafe_code ...
```

This tells lm-eval-harness that you explicitly want to run the unsafe task.

## Failure Modes

### Only env var set (no CLI flag)
```
ValueError: Attempted to run task: humaneval which is marked as unsafe.
Set confirm_run_unsafe_code=True to run this task.
```

### Only CLI flag set (no env var)
```
################################################################################
#                                DISCLAIMER                                    #
# ...code execution disclaimer...                                              #
#                                                                              #
# Once you have read this disclaimer and taken appropriate precautions,        #
# set the environment variable HF_ALLOW_CODE_EVAL="1".                         #
################################################################################
ValueError: Attempted to run task: humaneval which is marked as unsafe.
```

### Neither set
Same as above — process exits before loading the model.

## Working Example

```bash
#!/bin/bash
cd /data/SpecForge/custom_dflash
source eval_venv/bin/activate
export HF_ALLOW_CODE_EVAL=1

lm_eval --model hf \
  --model_args pretrained=/data/SpecForge/custom_dflash/checkpoints/final_model_merged,dtype=bfloat16 \
  --tasks humaneval \
  --batch_size 1 \
  --output_path /data/SpecForge/custom_dflash/evaluation_results/humaneval \
  --device cuda \
  --confirm_run_unsafe_code \
  > /tmp/lm_eval_humaneval.log 2>&1
```

## Result Reference

- Model: Qwen 27B Expert Logician (merged, BF16)
- Hardware: DGX Spark (NVIDIA GB10)
- Runtime: ~44 minutes (164 examples)
- Result: pass@1 = 82.93% (± 2.95%)
- Generation config: max_new_tokens=512 (patched)
