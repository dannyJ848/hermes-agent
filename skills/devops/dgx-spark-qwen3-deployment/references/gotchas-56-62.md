# DGX Spark Gotchas 56-62 (Pipeline Audit, Apr 18 2026)

56. **Orchestrator-to-training script CLI arg name mismatches silently ignored.**
    When an orchestrator calls a training script with --lora-r and --lora-alpha,
    but the training script accepts --rank and --alpha, the unknown args are
    silently dropped. Training uses WRONG defaults (e.g., profile rank=64
    instead of orchestrator's rank=8 for Restore SFT). FIX: Add alias
    entries in the case statement. Always audit that orchestrator arg names
    match training script arg names exactly.

57. **Shell override vars not injected into Python heredocs.** When a training
    script uses a cat-heredoc to generate a Python script, shell variables
    like RANK/LR/EPOCHS expand fine (unquoted heredoc). But --batch-size and
    --gradient-accum stored in override vars don't automatically reach Python.
    FIX: Export env vars before the python3 call, then read them in Python
    with os.environ.get(). CRITICAL: The Python ternary must be correct —
    do NOT chain ternaries that Python parses differently than intended.

58. **GRPO target_modules must match SFT target_modules.** If SFT trains
    all 8 modules (q,k,v,o,gate_proj,gate,up,down) but GRPO only trains 5
    (q,k,v,o,gate_proj), the MoE router and FFN layers trained by SFT
    are unlearned during GRPO — the router degrades. FIX: Copy the exact
    same target_modules list from SFT to GRPO's LoraConfig.

59. **Orchestrator must pass --base-model to GRPO.** Without it, GRPO uses
    its internal default which points to the ORIGINAL pre-abliteration model.
    On round 2+, GRPO should train on SUPER_MODEL (latest merged output) or
    ABLATE_MODEL. FIX: Add --base-model to the GRPO call with fallback logic.

60. **Python heredoc micro_batch/grad_accum must respect overrides properly.**
    Default logic (micro_batch smaller for long seq) should NOT be overridden
    by env vars incorrectly. Correct: wrap default in str() for the env var
    fallback. Wrong: chaining ternaries with ambiguous Python operator
    precedence.

61. **Merge/quantize Python blocks in orchestrator need UMA fix too.** The UMA
    double-allocation OOM (gotcha 49) affects ANY from_pretrained call, not
    just training. The merge phase loads the base model + LoRA adapter, and
    the FP8 quantization phase loads the BF16 model. All model-loading
    Python blocks in the orchestrator need the uma_eager_load import.

62. **Multi-pass pipeline audit methodology for shell orchestrators.** Audit
    in this order: (1) File integrity, (2) Arg name matching between
    orchestrator and called scripts, (3) Shell var-to-Python heredoc
    injection, (4) vLLM serve config consistency across ALL locations,
    (5) Feature coverage per-script, (6) Hyperparameter consistency,
    (7) Model path flow across phases, (8) Error handling and fallbacks.
    Use execute_code with Python string replacement instead of the patch
    tool for complex multiline edits — patch has high failure rate on
    heredocs and multi-line replacements.
