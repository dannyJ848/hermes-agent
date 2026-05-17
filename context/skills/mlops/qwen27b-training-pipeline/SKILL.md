---
name: qwen27b-training-pipeline
title: Qwen 27B Expert Logician Training Pipeline
description: Maximum-quality LoRA + SAE + teacher distillation pipeline for Qwen 27B on DGX Spark (130GB GPU)
version: 1.3.0
created: 2026-05-04
updated: 2026-05-14
---

# Qwen 27B Expert Logician Training Pipeline

## Context
Train Qwen 27B as expert logician on DGX Spark (130GB GPU, 128GB RAM). Full fine-tuning impossible (needs 192GB+). Maximum quality achievable via advanced LoRA + SAE + teacher distillation.

## User Preferences (Embedded)

### No Cron Jobs for Automation Triggers (May 14, 2026)
The user explicitly rejects cron jobs as unreliable for triggering training or any automated pipeline steps. When building automation around the training pipeline:

- **DO NOT use cron jobs** for periodic checks, triggers, or scheduling
- **DO use:** Systemd services, manual triggers, in-process polling, or event-driven hooks
- **For auto-training trigger:** Use filesystem watcher or manual invocation instead of cron
- **For session export:** Run on-demand or via in-process scheduler, not cron

**Rationale:** Cron jobs are considered unreliable due to silent failures, environment isolation issues, and lack of observability. The user prefers explicit, observable automation mechanisms.

**Correct pattern:**
```bash
# Manual trigger when buffer reaches threshold
python3 /data/SpecForge/hermes-agent/scripts/training_orchestrator.py --mode full

# Or run as systemd service with proper logging
sudo systemctl start qwen-training
```

**Anti-pattern:**
```bash
# NEVER set up cron jobs for this pipeline
crontab -e
# */30 * * * * python3 /data/SpecForge/hermes-agent/scripts/auto_training_trigger.py
```
When user asks a yes/no or direct question ("would it be possible?", "what is the answer?", "status?"), lead with the answer IMMEDIATELY. Do NOT do line-by-line log analysis before answering. Do NOT trace through evidence step-by-step unless the user explicitly asks for the debugging path.

**Critical signals — STOP all tool calls immediately:**
- **"loop?"** — User detects you're repeating the same check pattern. Stop. Give the answer now.
- **"you said that 10 minutes ago"** — SECOND frustration signal. You already explored and didn't conclude. State the answer directly with AT MOST 2 lines of evidence.
- **"what is the answer?"** — User explicitly calling out that you're not answering. Stop all exploration. Give the conclusion.
- **"status?"** — User wants current state, not a diagnostic journey. One SSH check + answer.

**Anti-pattern to avoid:**
- User: "would rank 512 work?"
- Wrong: grep line 1, grep line 2, grep line 3, sed line 4, awk line 5... (15 tool calls later) "yes"
- Right: "Yes. Rank 512 failed due to weights_only serialization, not OOM. Here's the evidence: [2-3 lines]"

**Corrective action after frustration signal:**
1. STOP all current tool calls immediately
2. State the answer directly (yes/no/number/conclusion)
3. Provide AT MOST 2 lines of supporting evidence
4. Ask if user wants the full analysis, or proceed with the decision

**Example from May 8, 2026 session:**
- User: "would rank 512 work after the fix?"
- Wrong: 15 SSH log greps hunting for evidence, user says "you said that 10 minutes ago"
- Right: "Yes. The log shows rank 512 crashed on `weights_only` error at line 4134, not OOM. Rank 1024 ran steps 10-100 at 85GB GPU. All previous high-rank failures were serialization, not memory."
- Then: "Want me to verify the exact memory math, or shall we kill 256 and launch 1024 now?"

### Infrastructure Kill-First Management
When user sees multiple processes, they want them all dead immediately — no review, no nuance. Kill everything first, then selectively re-enable only what matters.

### Clean Start Preference (No Resume)
When user says "start training from 0" or "no resume", they mean:
1. Delete old checkpoints before launching (`rm -rf /data/SpecForge/custom_dflash/checkpoints/checkpoint_step_*`)
2. Do NOT pass resume flags or load adapter weights
3. Training script starts with `global_step = 0` hardcoded — verify this in code
4. Fresh optimizer state, fresh learning rate schedule from step 0
5. Only the precomputed teacher cache is reused (static PKL files on disk)

**Why:** Old checkpoints may have corrupted state, wrong hyperparameters, or stale optimizer momentum. Starting clean eliminates hidden state bugs.

**Checkpoint cleanup command:**
```bash
# Before launching fresh training, free disk space and eliminate stale state
ssh djg6228@10.0.0.171 'rm -rf /data/SpecForge/custom_dflash/checkpoints/checkpoint_step_*'
ssh djg6228@10.0.0.171 'rm -f /mnt/bigssd/training_launched.flag /mnt/bigssd/training.pid'
```

### CRITICAL: `low_cpu_mem_usage=False` for LoRA on >20B Models (May 2026)

**When loading models >20B params with `device_map="auto"` for LoRA training, ALWAYS set `low_cpu_mem_usage=False`.**

Without this flag, `accelerate` offloads some layers to the "meta" device (lazy loading). LoRA's `get_peft_model()` creates adapter weights on the meta device, but the backward pass fails:

```
RuntimeError: Function MmBackward0 returned an invalid gradient at index 1
- expected device meta but got cuda:0
```

**Root cause:** Meta-device parameters have no actual memory backing. When backward tries to compute gradients for LoRA adapters attached to meta-device base weights, the gradient tensor lands on CUDA while the parameter is on meta.

**Fix:**
```python
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16,
    device_map="cuda:0",  # or "auto"
    low_cpu_mem_usage=False,  # CRITICAL: prevents meta-device offloading
    trust_remote_code=True
)
```

**Trade-off:** Loading takes ~2x longer (all parameters copied to CPU first, then GPU), but training works correctly. On GB10 with 128GB unified memory, this is acceptable.

**Verified on Qwen 27B BF16 (51GB):**
- With `low_cpu_mem_usage=False`: Model loads in ~5 min, LoRA applies, forward+backward+optimizer all work
- With `low_cpu_mem_usage=True` (default): Model loads in ~30 sec, LoRA applies, backward fails immediately

**Memory impact:**
- `low_cpu_mem_usage=True`: ~4GB GPU allocated (most params on meta device)
- `low_cpu_mem_usage=False`: ~54GB GPU allocated (all params on GPU)

This is the CORRECT behavior for training — you want all parameters on GPU anyway.

### Pre-tokenization Required for 2M+ Example Datasets

On-the-fly tokenization of large datasets (2M+ examples) is impossibly slow (~100 examples/sec) and creates a massive preprocessing bottleneck before training starts.

**Pattern: Pre-tokenize once, train multiple times**

```python
# pre_tokenize.py — run once before training
import json
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)

def preprocess_file(input_path, output_path, max_length=4096):
    with open(input_path) as f_in, open(output_path, 'w') as f_out:
        for line in f_in:
            data = json.loads(line)
            text = format_chat(data)  # Your formatting function
            enc = tokenizer(text, truncation=True, max_length=max_length, padding="max_length")
            f_out.write(json.dumps({"input_ids": enc["input_ids"], "attention_mask": enc["attention_mask"]}) + "\n")

# Run: ~15k examples/min on GB10
# 2.15M examples → ~2.5 hours, ~20GB output
```

**Training script loads pre-tokenized data:**
```python
from datasets import Dataset
import json

# Load pre-tokenized JSONL directly — no tokenizer calls during training
def load_preprocessed(path):
    examples = []
    with open(path) as f:
        for line in f:
            examples.append(json.loads(line))
    return Dataset.from_list(examples)

train_dataset = load_preprocessed("/data/SpecForge/custom_dflash/preprocessed/tier1_preprocessed.jsonl")
# DataCollatorForLanguageModeling(mlm=False) handles batching
```

**Benefits:**
- Training starts immediately (no preprocessing wait)
- ~50x faster epoch iteration
- Deterministic — same tokenization every run
- Can reuse preprocessed data across training runs with different hyperparameters

### Lazy Loading for Multi-Tier Datasets (May 13, 2026)

When combining multiple datasets of different sizes (e.g., tier1: 328k, tier2: 131k, tier3: 194 examples), loading all examples into RAM causes OOM or stalls. Use **file-offset indexing** for memory-efficient lazy loading:

```python
class LazyPreTokenizedDataset(Dataset):
    """Stores file offsets, loads examples on demand. ~0 RAM overhead."""
    def __init__(self, file_path, max_length=4096):
        self.file_path = file_path
        self.max_length = max_length
        self.offsets = []
        with open(file_path, 'rb') as f:
            offset = 0
            for line in f:
                self.offsets.append(offset)
                offset += len(line)
    def __len__(self): return len(self.offsets)
    def __getitem__(self, idx):
        with open(self.file_path, 'rb') as f:
            f.seek(self.offsets[idx])
            data = json.loads(f.readline().decode('utf-8'))
        # Return tensors directly
        return {
            'input_ids': torch.tensor(data['input_ids'], dtype=torch.long),
            'attention_mask': torch.tensor(data['attention_mask'], dtype=torch.long),
            'labels': torch.tensor(data['labels'], dtype=torch.long)
        }
```

**Weighting via ConcatDataset repetition** (avoids custom samplers that deadlock in Trainer):
```python
from torch.utils.data import ConcatDataset

tier1 = LazyPreTokenizedDataset('preprocessed/tier1.jsonl')      # 328k
 tier2 = LazyChatDataset('datasets/tier2.jsonl', tokenizer)       # 131k
 tier3 = LazyChatDataset('datasets/tier3.jsonl', tokenizer)       # 194

# Repeat smaller datasets to approximate desired weights
# tier3 * 120 ≈ 23k, giving ~70/25/5% split
train_dataset = ConcatDataset([tier1, tier2] + [tier3] * 120)
```

**CRITICAL: Avoid these patterns** (they deadlock or OOM):
- `WeightedIterableDataset` with `random.choices` in `__iter__` — deadlocks in `Trainer`
- `DataLoader(num_workers > 0)` with large datasets — forks double RAM
- `padding='max_length'` in tokenizer + `DataCollatorForSeq2Seq` — double-padding conflict
- Pre-computing `index_map` with 900k+ entries at init — blocks for minutes

**Pitfall: "Training never starts"** — Model loading takes ~5 min on GB10. If you kill the process before seeing "Step 1", you mistake loading for a hang. Use `nvidia-smi` to confirm GPU memory allocation (~51GB) before declaring a stall.

### CRITICAL: CUDA OOM on Forward Pass — Not a Hang (May 13, 2026)

**Symptom:** Model loads successfully (~54GB GPU), but training never starts. Process shows 100% CPU, futex sleep in stack traces. `nvidia-smi` shows ~51GB allocated. No metrics after 5+ minutes.

**Actual cause:** CUDA OOM on the first forward pass. The model loading progress bar completes, but the forward pass + gradient computation + optimizer states exceed 121GB GB10 VRAM.

**Error signature (only visible if you wait for crash or test with small steps):**
```
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 80.00 MiB.
GPU 0 has a total capacity of 121.69 GiB of which 583.20 MiB is free.
```

**Memory breakdown for Qwen 27B BF16 + LoRA r=256:**
- Model weights: ~54GB
- LoRA adapters: ~1.3GB
- Optimizer states (8-bit AdamW): ~2.6GB
- Gradients: ~1.3GB
- Activations (batch=1, seq=4096): ~2-4GB
- **Subtotal: ~62GB**
- **BUT** `DataCollatorForLanguageModeling(mlm=False)` duplicates input_ids for labels, adding ~16GB
- **Total: ~78GB** — should fit, but PyTorch allocator fragmentation pushes it over

**Fixes (apply ALL):**

1. **Enable gradient checkpointing** (trades compute for memory):
```python
training_args = TrainingArguments(
    # ... other args ...
    gradient_checkpointing=True,
    gradient_checkpointing_kwargs={"use_reentrant": False},
)
# OR manually:
model.gradient_checkpointing_enable()
```

2. **Use a custom collator that doesn't duplicate tensors**:
```python
class CausalLMCollator:
    """For pre-tokenized data with existing labels. No duplication."""
    def __init__(self, pad_token_id=0):
        self.pad_token_id = pad_token_id
    def __call__(self, features):
        input_ids = torch.stack([f["input_ids"] for f in features])
        attention_mask = torch.stack([f["attention_mask"] for f in features])
        labels = torch.stack([f["labels"] for f in features])
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
        }
```

3. **Set `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`** to reduce fragmentation:
```bash
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
```

4. **Verify with a 3-step test before launching full training**:
```python
args = TrainingArguments(..., max_steps=3, warmup_steps=0)
trainer = Trainer(model=model, args=args, ...)
trainer.train()  # Should complete in <2 min after model load
```

**Anti-pattern: Mistaking OOM for "dataloader hang"**
- Wrong: "DataLoader with ConcatDataset is deadlocking, let me rewrite with IterableDataset"
- Wrong: "WeightedDataset is causing futex waits, let me try random sampling"
- Right: "Model loads at 54GB but forward pass OOMs. Enable gradient checkpointing and test with 3 steps."

**The futex waits are PyTorch's CUDA memory allocator retrying**, not a Python deadlock.

### CRITICAL: Gradient Checkpointing "Deadlock" Was Actually CPU-Only PyTorch (May 14, 2026) — CORRECTED

**UPDATE:** The "gradient checkpointing deadlock with Qwen3.5 linear attention" was NOT a model architecture issue. The actual cause was CPU-only PyTorch in the `train-venv` environment.

**What happened:**
- `train-venv` at `/home/djg6228/train-venv` had `torch 2.10.0+cpu` (CPU-only build)
- When `model.gradient_checkpointing_enable()` was called, PyTorch tried to move tensors to CUDA but failed silently
- Process entered uninterruptible sleep (D state) because PyTorch was retrying CUDA operations on a CPU-only build
- This appeared as a "deadlock" but was actually an environment misconfiguration

**Verification:**
```python
import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
# If CUDA available is False, ALL training issues are environment-related
```

**Fix:**
```bash
# ALWAYS use system Python for training on DGX
/usr/bin/python3 -c "import torch; print(torch.__version__)"  # Should show +cuXXX

# NEVER use train-venv for training (it has CPU-only torch)
```

**With correct environment (system Python with CUDA torch), gradient checkpointing works perfectly:**
- `model.gradient_checkpointing_enable({"use_reentrant": False})` — works
- `model.config.use_cache = False` — required companion setting
- GPU memory: 53.8GB (model) → 59.1GB (LoRA r=256) → ~62.4GB (training with GC)
- Forward pass: ~2.5s, Backward pass: ~8.5s, Total step: ~38-40s

**The May 8 Mystery — SOLVED:**
The script `train_lora_sae_teacher_v1.py` worked on May 8 because it was run with system Python (which has CUDA torch). When we later tried to run it from `train-venv`, it "deadlocked" because the venv had CPU-only torch. The broken log path (`/mnt/bigssd/`) was a secondary issue that masked the real problem.

**Anti-pattern: Assuming the model or code is broken**
- Wrong: "Gradient checkpointing deadlocks with Qwen3.5 linear attention — must be a model bug"
- Right: "Verify `torch.cuda.is_available()` first. The environment is the most likely culprit."

**Anti-pattern: Chasing OOM without checking GC compatibility**
- Wrong: "Without GC we OOM, so we MUST make GC work"
- Right: "If GC appears to deadlock, check PyTorch environment first before blaming model architecture"
## Current Live Training State (May 14, 2026 18:30 UTC) — INFERENCE MODE
- **Status: TRAINING STOPPED — User requested inference instead**
- **vLLM serving:** Base model + LoRA adapter via `--enable-lora` on port 8000
- **LoRA adapter path:** `/data/SpecForge/custom_dflash/checkpoints/final_model/` (r=256, alpha=512)
- **Base model:** `/data/models/Qwen3.6-27B-Uncensored/`
- **Context length:** 131,072 tokens (max_model_len)
- **Tool calling:** ENABLED via `--enable-auto-tool-choice --tool-call-parser qwen3_xml`
- **Hermes config:** `~/.hermes/config.yaml` with `context_length: 131072`
- **Container:** `vllm-merged` (docker)
- **GPU memory:** ~55GB model + ~5GB LoRA + KV cache
- **Speed:** ~20 tok/s (no thinking), ~4-8 tok/s (with thinking)
- **Training can be resumed:** `sudo systemctl start qwen-training`
- **Prior training preserved:** All FrankenV8 distillation intact in merged model weights

## Current Live Training State (May 14, 2026 11:40 UTC) — TRAINING ENVIRONMENT ISSUE IDENTIFIED
- **Status: TRAINING BLOCKED — CPU-only PyTorch in train-venv caused false "deadlock"**
- **Finding:** `train-venv` had `torch 2.10.0+cpu` — gradient checkpointing appeared to deadlock but was actually PyTorch failing on CUDA operations
- **Fix:** Use system Python `/usr/bin/python3` which has `torch 2.11.0+cu130`
- **With correct environment:** Gradient checkpointing works perfectly with `use_reentrant=False`
- **GPU memory with GC:** ~62GB (model 54GB + LoRA 5GB + activations ~3GB)
- **Files on DGX:** train_lora_sae_teacher_v1.py (May 8, works with system Python), train_micro.py (r=128, seq=1024, no GC), train_reentrant.py (r=256, seq=4096, GC default)
- **Next action:** Launch training with system Python, verify 3 steps complete successfully

### CRITICAL: vLLM Tool Calling Requires Correct Parser Name (May 14, 2026)

**For Qwen3.5/Qwen3.6 models, the correct tool-call parser is `qwen3_xml` (NOT `qwen25`).**

**Error if wrong parser:**
```
KeyError: 'invalid tool call parser: qwen25 (chose from { deepseek_v3, ..., qwen3_xml, qwen3_coder, ... })'
```

**Working vLLM launch command:**
```bash
docker run -d --name vllm-merged \
  --runtime nvidia --gpus all \
  -p 8000:8000 \
  -v /data/models:/data/models \
  -v /data/SpecForge/custom_dflash/checkpoints/final_model:/data/checkpoints/final_model \
  vllm/vllm-openai:latest \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --enable-lora \
  --lora-modules merged-lora=/data/checkpoints/final_model \
  --max-lora-rank 256 \
  --max-model-len 131072 \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.95 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml
```

**Hermes config must also be updated:**
```yaml
context_length: 131072  # NOT 65536
```

**Key flags:**
- `--enable-auto-tool-choice` — Required for Hermes "auto" tool_choice
- `--tool-call-parser qwen3_xml` — Qwen3.5/3.6 XML-based tool calling format
- `--max-model-len 131072` — 128K context (base model supports 262K but 128K is stable)
- `--enable-lora` + `--max-lora-rank 256` + `--lora-modules` — Serve LoRA adapter

**Verification:**
```bash
curl -s http://localhost:8000/v1/models | grep -E 'id|max_model_len'
# Should show: "id": "merged-lora", "max_model_len": 131072
```

**Always verify `torch.cuda.is_available()` before debugging ANY training issue.**

The "gradient checkpointing deadlock" was actually CPU-only PyTorch in train-venv:
- `train-venv` at `/home/djg6228/train-venv` had `torch 2.10.0+cpu` (CPU-only build)
- System Python `/usr/bin/python3` has `torch 2.11.0+cu130` (CUDA-enabled)
- All "deadlock" symptoms were PyTorch failing when trying to move tensors to CUDA

**Verification pattern:**
```python
import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
# If CUDA available is False, fix PyTorch BEFORE debugging anything else
```

**Fix:**
```bash
# On DGX Spark — ALWAYS use system Python for training
/usr/bin/python3 -c "import torch; print(torch.__version__)"  # Should show +cuXXX

# NEVER use train-venv for training (it has CPU-only torch)
```

**With correct environment, gradient checkpointing works perfectly:**
- `model.gradient_checkpointing_enable({"use_reentrant": False})` — works
- `model.config.use_cache = False` — required companion setting
- GPU memory: 53.8GB (model) → 59.1GB (LoRA r=256) → ~62.4GB (training with GC)
- Forward pass: ~2.5s, Backward pass: ~8.5s, Total step: ~38-40s

**Anti-pattern: Assuming the model or code is broken**
- Wrong: "Gradient checkpointing deadlocks with Qwen3.5 linear attention — must be a model bug"
- Right: "Verify `torch.cuda.is_available()` first. The environment is the most likely culprit."

**The May 8 Mystery — SOLVED:**
The script `train_lora_sae_teacher_v1.py` worked on May 8 because it was run with system Python (which has CUDA torch). When we later tried to run it from `train-venv`, it "deadlocked" because the venv had CPU-only torch. The broken log path (`/mnt/bigssd/`) was a secondary issue that masked the real problem.

### CRITICAL: Gradient Checkpointing "Deadlock" Was Actually CPU-Only PyTorch (May 14, 2026) — CORRECTED

**UPDATE:** The "gradient checkpointing deadlock with Qwen3.5 linear attention" was NOT a model architecture issue. The actual cause was CPU-only PyTorch in the `train-venv` environment.

**What happened:**
- `train-venv` at `/home/djg6228/train-venv` had `torch 2.10.0+cpu` (CPU-only build)
- When `model.gradient_checkpointing_enable()` was called, PyTorch tried to move tensors to CUDA but failed silently
- Process entered uninterruptible sleep (D state) because PyTorch was retrying CUDA operations on a CPU-only build
- This appeared as a "deadlock" but was actually an environment misconfiguration

**Verification:**
```python
import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
# If CUDA available is False, ALL training issues are environment-related
```

**Fix:**
```bash
# ALWAYS use system Python for training on DGX
/usr/bin/python3 -c "import torch; print(torch.__version__)"  # Should show +cuXXX

# NEVER use train-venv for training (it has CPU-only torch)
```

**With correct environment (system Python with CUDA torch), gradient checkpointing works perfectly:**
- `model.gradient_checkpointing_enable({"use_reentrant": False})` — works
- `model.config.use_cache = False` — required companion setting
- GPU memory: 53.8GB (model) → 59.1GB (LoRA r=256) → ~62.4GB (training with GC)
- Forward pass: ~2.5s, Backward pass: ~8.5s, Total step: ~38-40s

**The May 8 Mystery — SOLVED:**
The script `train_lora_sae_teacher_v1.py` worked on May 8 because it was run with system Python (which has CUDA torch). When we later tried to run it from `train-venv`, it "deadlocked" because the venv had CPU-only torch. The broken log path (`/mnt/bigssd/`) was a secondary issue that masked the real problem.

**Anti-pattern: Assuming the model or code is broken**
- Wrong: "Gradient checkpointing deadlocks with Qwen3.5 linear attention — must be a model bug"
- Right: "Verify `torch.cuda.is_available()` first. The environment is the most likely culprit."

**Anti-pattern: Chasing OOM without checking GC compatibility**
- Wrong: "Without GC we OOM, so we MUST make GC work"
- Right: "If GC appears to deadlock, check PyTorch environment first before blaming model architecture"

### OBSOLETE: Gradient Checkpointing Deadlock with Qwen3.5 Linear Attention (May 14, 2026)

**This section is OBSOLETE.** The "deadlock" was actually CPU-only PyTorch. See corrected section above.

~~**Symptom:** `model.gradient_checkpointing_enable()` causes process to enter D state (uninterruptible sleep) at first forward pass. Process cannot be killed with `kill -9`. `nvidia-smi` shows GPU memory allocated but 0% utilization.~~

~~**Finding:** Gradient checkpointing deadlocks with this specific model architecture (Qwen3.5-VL hybrid with linear attention).~~228/train-venv` had `torch 2.10.0+cpu` (CPU-only build)
- When `model.gradient_checkpointing_enable()` was called, PyTorch tried to move tensors to CUDA but failed silently
- Process entered uninterruptible sleep (D state) because PyTorch was retrying CUDA operations on a CPU-only build
- This appeared as a "deadlock" but was actually an environment misconfiguration

**Verification:**
```python
import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
# If CUDA available is False, ALL training issues are environment-related
```

**Fix:**
```bash
# ALWAYS use system Python for training on DGX
/usr/bin/python3 -c "import torch; print(torch.__version__)"  # Should show +cuXXX

# NEVER use train-venv for training (it has CPU-only torch)
```

**With correct environment (system Python with CUDA torch), gradient checkpointing works perfectly:**
- `model.gradient_checkpointing_enable({"use_reentrant": False})` — works
- `model.config.use_cache = False` — required companion setting
- GPU memory: 53.8GB (model) → 59.1GB (LoRA r=256) → ~62.4GB (training with GC)
- Forward pass: ~2.5s, Backward pass: ~8.5s, Total step: ~38-40s

**The May 8 Mystery — SOLVED:**
The script `train_lora_sae_teacher_v1.py` worked on May 8 because it was run with system Python (which has CUDA torch). When we later tried to run it from `train-venv`, it "deadlocked" because the venv had CPU-only torch. The broken log path (`/mnt/bigssd/`) was a secondary issue that masked the real problem.

**Anti-pattern: Assuming the model or code is broken**
- Wrong: "Gradient checkpointing deadlocks with Qwen3.5 linear attention — must be a model bug"
- Right: "Verify `torch.cuda.is_available()` first. The environment is the most likely culprit."

**Anti-pattern: Chasing OOM without checking GC compatibility**
- Wrong: "Without GC we OOM, so we MUST make GC work"
- Right: "If GC appears to deadlock, check PyTorch environment first before blaming model architecture"

### OBSOLETE: Gradient Checkpointing Deadlock with Qwen3.5 Linear Attention (May 14, 2026)

**This section is OBSOLETE.** The "deadlock" was actually CPU-only PyTorch. See corrected section above.

~~**Symptom:** `model.gradient_checkpointing_enable()` causes process to enter D state (uninterruptible sleep) at first forward pass. Process cannot be killed with `kill -9`. `nvidia-smi` shows GPU memory allocated but 0% utilization.~~

~~**Finding:** Gradient checkpointing deadlocks with this specific model architecture (Qwen3.5-VL hybrid with linear attention).~~
- Merged model: `/data/SpecForge/custom_dflash/checkpoints/final_model_merged/` (base + LoRA weights combined)

**The merged model IS further tunable** — it is just a standard Qwen 27B weights file with the prior training baked in. You can apply a NEW LoRA adapter on top of it.

**Wrong (throws away prior training):**
```python
model_path = "/data/models/Qwen3.6-27B-Uncensored/"  # Base model — discards FrankenV8 distillation
```

**Right (preserves prior training):**
```python
model_path = "/data/SpecForge/custom_dflash/checkpoints/final_model_merged/"  # Post-trained model
```

**Verification that merged model has prior training:**
- Step 0 loss from base: ~3.40
- Step 0 loss from merged: ~1.19 (much lower, confirms prior training preserved)

**How to verify which model you're loading:**
```bash
# Check if it's a merged model (full weights) or LoRA adapter (small)
ls -la /path/to/model/*.safetensors
# Merged: multiple large .safetensors files (50GB+)
# Adapter: small adapter_model.safetensors (~5GB) + adapter_config.json

# Check config for base model path
grep "base_model_name_or_path" /path/to/model/adapter_config.json 2>/dev/null || echo "This is a merged model (no adapter_config)"
```

**Anti-pattern: "Start from base to be safe"**
- Wrong: "I'll use the base model to avoid any issues with the merged model"
- Right: "The merged model has 10k steps of prior training. Starting from base discards that work."

**Anti-pattern: "Merged models can't be further tuned"**
- Wrong: "Once merged, the model is frozen and can't be trained further"
- Right: "Merged models are just standard weights files. Apply a new LoRA adapter and continue training."

**Note on LoRA stacking:** The new LoRA adapter is independent of the old one. The old adapter's weights are now part of the base model. The new adapter learns additional adjustments on top. This is standard practice for iterative fine-tuning.

### CRITICAL: Custom Training Loop vs transformers.Trainer — 25x Speed Difference (May 13, 2026)

**Finding:** The SAME model (Qwen 27B), SAME GPU (GB10), SAME LoRA config (r=256) can train at either ~20s/step or ~517s/step depending entirely on the training loop implementation.

**UPDATE:** With correct Python environment (system Python with CUDA torch), training is viable at ~38s/step with gradient checkpointing and all 3 tiers of data. The earlier "intractable" assessment was partially due to CPU-only PyTorch in train-venv.

**Measured speeds (batch=1, grad_accum=4, seq=1024, LoRA r=128):**
| Approach | GPU Memory | Step Time | 10k Steps ETA | Working? |
|----------|-----------|-----------|---------------|----------|
| Custom loop + GC + 8-bit AdamW (all 3 tiers) | ~58GB | ~38s/step | ~107 hours | YES — LIVE |
| Custom loop + 8-bit AdamW (May 8, no GC) | ~62GB | ~20s/step | ~55 hours | YES |
| transformers.Trainer + grad checkpointing | ~81GB | ~517s/step | ~1,450 hours | NO |
| QLoRA (NF4, r=64) + paged AdamW | ~49GB | ~529s/step | ~1,470 hours | NO |

**Key insight:** `transformers.Trainer` with `DataCollatorForLanguageModeling(mlm=False)` duplicates input tensors for labels, adding ~16GB memory overhead. This forces gradient checkpointing, which trades compute for memory. The result is ~25x slower than a custom loop.

**Gradient checkpointing IS viable** when using:
1. Correct Python environment (system Python, NOT train-venv)
2. Custom training loop (not transformers.Trainer)
3. `use_reentrant=False`
4. `model.config.use_cache = False`
5. 8-bit AdamW optimizer

**The May 8 custom loop succeeded because:**
1. **No tensor duplication** — labels computed in-place from input_ids, no collator duplication
2. **8-bit AdamW (`bnb.optim.Adam8bit`)** — optimizer states in ~2.6GB vs ~10GB for standard AdamW
3. **Custom streaming dataloader** — parquet streaming, no DataLoader overhead

**The transformers.Trainer failed because:**
1. `DataCollatorForLanguageModeling(mlm=False)` duplicates `input_ids` → `labels` (+16GB)
2. Total memory ~78GB + fragmentation → OOM without gradient checkpointing
3. Gradient checkpointing adds ~25x compute overhead (recomputing activations)
4. Standard AdamW optimizer states add ~10GB

**Fix: Use custom training loop for 27B on GB10**

```python
# CORRECT: Custom loop with gradient checkpointing (current live training)
import bitsandbytes as bnb

# 8-bit optimizer
optimizer = bnb.optim.Adam8bit(
    [p for p in model.parameters() if p.requires_grad],
    lr=1e-4, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.01
)

# Enable gradient checkpointing
model.config.use_cache = False
model.gradient_checkpointing_enable({"use_reentrant": False})
model.train()

# Training loop
for batch in dataloader:
    outputs = model(input_ids=batch['input_ids'], labels=batch['labels'])
    loss = outputs.loss / grad_accum_steps
    loss.backward()
    if (step + 1) % grad_accum_steps == 0:
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        optimizer.zero_grad()
```

**Anti-pattern: "Use transformers.Trainer for convenience"**
- Wrong: "Let's use transformers.Trainer — it's the standard way"
- Right: "For 27B on GB10, custom loop with 8-bit AdamW is required. Use the working script pattern."

**Anti-pattern: "QLoRA will make it fast enough"**
- Wrong: "Let's try QLoRA — 4-bit should be much faster"
- Right: "QLoRA adds dequantization overhead. On GB10, custom loop BF16 with GC is the viable path."

**Verification:** Before committing to a training approach, run a 3-step timing test:
```python
# Test custom loop
import time
start = time.time()
for i in range(3):
    batch = next(iter(dataloader))
    outputs = model(**batch)
    outputs.loss.backward()
print(f"3 custom steps in {time.time()-start:.0f}s")
# Should be <120s (40s/step) for viable training
```

**Current live training:** `/data/SpecForge/custom_dflash/train_qwen_all_tiers.py`
- All 3 tiers: 463k examples
- LoRA r=128, seq_len=1024, batch=1, grad_accum=4
- Gradient checkpointing enabled
- 8-bit AdamW
- ~38s/step, ETA ~107h for 10k steps

### SSH Session Timeout Kills Background Training (May 13, 2026)

**CRITICAL:** When you launch training via SSH and the SSH session times out (~3 minutes), the training process is killed. `nohup` and `disown` are required but the SSH connection itself is the problem.

**Wrong:**
```bash
ssh dgx "python train.py"  # Dies when SSH drops
```

**Right — use `nohup` inside a persistent shell:**
```bash
# Write a launcher script ON the remote host, then execute it
ssh dgx "cat > launch.sh << 'EOF'
#!/bin/bash
cd /data/SpecForge/custom_dflash
export PYTHONPATH=/data/SpecForge/custom_dflash:$PYTHONPATH
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
nohup $HOME/train-venv/bin/python train_simple.py > training_launch.log 2>&1 &
echo $! > training.pid
disown
EOF
bash launch.sh"
```

**Even better — use `screen` or `tmux`:**
```bash
ssh dgx "screen -dmS training bash -c 'cd /data/SpecForge/custom_dflash && python train_simple.py > training.log 2>&1'"
# Reattach later:
ssh dgx "screen -r training"
```

**Verification that process survived SSH disconnect:**
```bash
# From local machine, after disconnecting and reconnecting:
ssh dgx "ps aux | grep train_simple | grep -v grep"
ssh dgx "nvidia-smi | grep python"
```

### Pre-tokenization Already Done — Check Before Assuming (May 13, 2026)

Session checkpoint names can be stale. The checkpoint said "pre-tokenization-running" but the file was already complete at 327k lines / 20GB.

**Always verify actual state:**
```bash
ssh dgx "wc -l /data/SpecForge/custom_dflash/preprocessed/*.jsonl"
ssh dgx "ls -lh /data/SpecForge/custom_dflash/preprocessed/"
```

**Don't trust checkpoint names alone.**

**CRITICAL DISTINCTION (May 13, 2026):** When a user says "training crashed", verify what actually happened before diagnosing. Common confusion:

| What user says | What actually happened | Correct response |
|---------------|------------------------|------------------|
| "Training crashed" | Pre-tokenization still running | "Training hasn't started yet — pre-tokenization is 13% complete" |
| "It died" | Process was loading model weights | "Process is loading weights (~5 min), not dead" |
| "Background process completed" | Old SSH session terminated | "That was the SSH session, not the training process" |

**Verification checklist before declaring "crash":**
```bash
# 1. Check if training process exists
ssh djg6228@10.0.0.171 "ps aux | grep train_direct | grep -v grep"

# 2. Check if pre-tokenization is running
ssh djg6228@10.0.0.171 "ps aux | grep pre_tokenize | grep -v grep"

# 3. Check GPU for compute processes
ssh djg6228@10.0.0.171 "nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader"

# 4. Check recent log activity
ssh djg6228@10.0.0.171 "tail -20 /tmp/train.log"
```

**Rule: Training hasn't started until you see "Step 1/XXX" in the log.**
Pre-tokenization, model loading, and dataset preparation are NOT training.

### Training Completion Verification — Don't Trust Log Messages
**CRITICAL PITFALL (May 10, 2026):** The log says "Merging LoRA weights..." but this does NOT mean the merge succeeded. The process logged the merge start, compiled C extensions (gcc output), then died without writing weight files.

**Verification required before declaring "training complete":**
1. Process gone: `ps aux | grep train | grep -v grep` → empty
2. Weight files exist: `find final_model_merged/ -name '*.safetensors' | wc -l` → MUST be > 0
3. File count realistic: Qwen 27B has ~15-30 sharded .safetensors files
4. Explicit completion message in log: "Merge complete" or "Model saved"
5. Fallback: checkpoint_step_10000/ exists if merge failed

**WRONG:** "Training complete, LoRA merged, ready for evaluation"
**RIGHT:** "Training reached step 10000/10000. Checkpoint saved. Merge started but weight files not verified. Checking final_model_merged/ for .safetensors... [then report actual finding]"

See `references/training-completion-verification-may10-2026.md` for full checklist and recovery steps.

### LoRA Merge Verification — Separate Step from Training
**CRITICAL (May 10, 2026):** The training script's `merge_and_unload()` may fail silently, producing only config files (config.json, generation_config.json) with NO weight files (.safetensors, .bin). This is a known PEFT issue where the merge starts, compiles extensions, then dies without writing weights.

**Post-training merge MUST be verified independently:**
1. Training saves checkpoint → verify checkpoint exists
2. Training calls merge → **DO NOT TRUST** — verify separately
3. Check `final_model_merged/` for `.safetensors` or `.bin` files
4. If only config files exist → merge failed → run manual merge

**Manual merge recovery (proven working May 10, 2026):**
```python
# On DGX via SSH
from peft import PeftModel
from transformers import AutoModelForCausalLM
import torch

base = AutoModelForCausalLM.from_pretrained(
    "/data/models/Qwen3.6-27B-Uncensored",
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True
)
model = PeftModel.from_pretrained(base, "/data/SpecForge/custom_dflash/checkpoints/checkpoint_step_10000")
merged = model.merge_and_unload()
merged.save_pretrained("/data/SpecForge/custom_dflash/checkpoints/final_model_merged/")
```

**Common merge failure: Missing `adapter_config.json`**
- Checkpoint directory may only contain `adapter_model.bin` + `optimizer.pt`
- `adapter_config.json` is required by PEFT but may be in `final_model/` instead
- Fix: `cp final_model/adapter_config.json checkpoint_step_10000/`

**Background process over SSH:**
- `terminal(background=true)` does NOT background on remote host — it backgrounds on local machine
- Use `execute_code` with `subprocess.run(["ssh", "...", "nohup python3 /tmp/merge.py > log 2>&1 & echo $!"])`
- Poll merge progress with separate SSH commands checking `ps aux` and `tail -5 log`

**Missing LoRA keys warning (expected):**
- PEFT warns "Found missing adapter keys" when config claims more layers than checkpoint has
- Common case: Config targets all 64 layers, but checkpoint only has attention LoRA on every 4th layer (16 layers)
- This is cosmetic — merge still succeeds with available weights
- Verify: `torch.load("adapter_model.bin")` → check actual keys present

## Pipeline Configuration
- **Student:** Qwen3.6-27B-Uncensored (frozen, bf16, ~58GB GPU)
- **LoRA:** rank-256, α=512, all linear layers (~1.27B trainable params)
- **Teacher:** Franken V8 (precomputed hidden states at layers [8,16,24,32,40,48])
- **SAEs:** Qwen-Scope at layers [16,32,48] (feature alignment)
- **Loss:** CE + hidden-state MSE + SAE feature MSE
- **Optimizer:** 8-bit AdamW
- **Schedule:** WSD-S (warmup 500, stable 8000, decay 1500)
- **Data:** Streaming Parquet (58 files, curatedthoughts + openthoughts2-1m)

## Current Live Training State (May 13, 2026 16:00 UTC)
- **Status:** PRE-TOKENIZATION RUNNING — PID 572146, ~280k/2.15M tier1 examples processed
- **Training script:** `/data/SpecForge/custom_dflash/train_direct.py` (READY, not launched)
- **Pre-tokenized output:** `/data/SpecForge/custom_dflash/preprocessed/tier1_preprocessed.jsonl` (19GB)
- **ETA:** ~3 hours remaining for pre-tokenization
- **Telemetry:** http://10.0.0.171:8080 (PID 575336)
- **Monitor:** PID 579274 (GPU health daemon)
- **Stack:** Direct PEFT + transformers.Trainer, LoRA r=256, 8-bit AdamW
- **Critical fix:** `low_cpu_mem_usage=False` prevents meta-device gradient bugs
- **Axolotl:** ABANDONED (config parse errors, preprocessing timeouts)

## Current Live Training State (May 13, 2026 17:30 UTC)
- **Status:** PRE-TOKENIZATION COMPLETE — tier1_preprocessed.jsonl has 327,718 examples (20.6GB)
- **Training script:** `/data/SpecForge/custom_dflash/train_simple.py` (READY, uses lazy-loading + ConcatDataset)
- **Datasets:** tier1 (328k), tier2 (131k), tier3 (194) — combined 481k examples with repetition weighting
- **Verified:** Lazy loading works, DataLoader iterates, Trainer initializes
- **Pending:** Full training launch (model loading ~5 min, then training starts)
- **Critical fix:** `low_cpu_mem_usage=False` prevents meta-device gradient bugs
- **Pitfall avoided:** WeightedIterableDataset deadlocks in Trainer; use ConcatDataset repetition instead

## Current Live Training State (May 13, 2026 18:30 UTC)
- **Status:** TRAINING ABANDONED — GB10 cannot practically train 27B models
- **Finding:** Both BF16+grad_checkpointing (~517s/step) and QLoRA (~529s/step) are intractably slow
- **Root cause:** GPU compute throughput bottleneck, not memory
- **GPU:** 121GB VRAM sufficient, but SM throughput too low for 27B forward/backward
- **Alternatives:** Train 7B model, use GB10 for inference, or use cloud A100/H100
- **Pre-tokenized data:** `/data/SpecForge/custom_dflash/preprocessed/tier1_preprocessed.jsonl` (327k examples, 20.6GB) — reusable for cloud training
- **Datasets:** tier1 (328k), tier2 (131k), tier3 (194) — ready for upload to cloud

## Current Live Training State (May 14, 2026 00:15 UTC)
- **Status: TRAINING IS LIVE — Continuing from merged post-trained model**
- **Training script:** `/data/SpecForge/custom_dflash/train_qwen_all_tiers.py`
- **Model:** `/data/SpecForge/custom_dflash/checkpoints/final_model_merged/` (FrankenV8-distilled Qwen 27B, NOT base uncensored)
- **Systemd service:** `qwen-training.service` (uses `/usr/bin/python3`, NOT train-venv)
- **Config:** LoRA r=256, alpha=512, seq_len=1024, batch=1, grad_accum=4
- **Gradient checkpointing:** ENABLED with `use_reentrant=False`
- **GPU memory:** 53.8GB (model) → 59.1GB (LoRA r=256) → ~62GB (training)
- **Optimizer:** 8-bit AdamW
- **Data (all 3 tiers):** 463,151 total examples
  - Tier 1: 327,718 (pre-tokenized reasoning)
  - Tier 2: 130,583 (reasoning chat, tokenized on-the-fly)
  - Tier 3: 4,850 (health chat, 194 unique repeated 25x)
- **Progress:** Step 0/10000, Loss: 1.1943 (lower than base's 3.40, confirming prior training preserved)
- **Speed:** ~38-40s/step, ETA ~107h for 10k steps
- **Checkpoints:** Every 500 steps to `/data/SpecForge/custom_dflash/checkpoints/`

**Key distinction from previous training:**
- Prior training (May 8-10): LoRA r=256 on base `Qwen3.6-27B-Uncensored` → merged to `final_model_merged/`
- Current training (May 14): NEW LoRA r=256 on `final_model_merged/` (post-trained model)
- This preserves all prior FrankenV8 distillation work and continues improving it

## Current Live Training State (May 14, 2026 05:30 UTC) — INFERENCE MODE
- **Status: TRAINING STOPPED — User requested inference instead**
- **Reason:** User wants to use the merged model for inference via Hermes before continuing training
- **vLLM serving:** Base model + LoRA adapter via `--enable-lora` (merged model has vision config issues with vLLM)
- **Hermes config:** `/data/SpecForge/hermes-agent/config.yaml` pointing to `http://localhost:8000/v1`
- **Context length:** 32K (reduced from 262K for better memory/speed)
- **Speed:** ~20 tok/s (no thinking), ~4-8 tok/s (with thinking)
- **Training can be resumed:** `sudo systemctl start qwen-training`
- **Prior training preserved:** All FrankenV8 distillation intact in merged model weights

## Current Live Training State (May 14, 2026 11:40 UTC) — TRAINING ENVIRONMENT ISSUE IDENTIFIED
- **Status: TRAINING BLOCKED — CPU-only PyTorch in train-venv caused false "deadlock"**
- **Finding:** `train-venv` had `torch 2.10.0+cpu` — gradient checkpointing appeared to deadlock but was actually PyTorch failing on CUDA operations
- **Fix:** Use system Python `/usr/bin/python3` which has `torch 2.11.0+cu130`
- **With correct environment:** Gradient checkpointing works perfectly with `use_reentrant=False`
- **GPU memory with GC:** ~62GB (model 54GB + LoRA 5GB + activations ~3GB)
- **Files on DGX:** train_lora_sae_teacher_v1.py (May 8, works with system Python), train_micro.py (r=128, seq=1024, no GC), train_reentrant.py (r=256, seq=4096, GC default)
- **Next action:** Launch training with system Python, verify 3 steps complete successfully

## Previous Training State (May 14, 2026 11:40 UTC) — OBSOLETE
- **Status: TRAINING BLOCKED — Gradient checkpointing deadlock with Qwen3.5 linear attention**
- **Finding:** `model.gradient_checkpointing_enable()` causes process to enter D state (uninterruptible sleep) at first forward pass
- **Without GC:** OOM at 117GB even with seq_len=1024, r=128, batch=1
- **With GC (use_reentrant=False):** Deadlock after "Using 8-bit AdamW"
- **With GC (use_reentrant=True):** Same deadlock
- **Memory breakdown without GC:** Model 51GB + LoRA + activations + gradients + optimizer = 117GB+ (exceeds 121GB)
- **Critical open question:** Does the May 8 script (train_lora_sae_teacher_v1.py) actually work? It has broken log path (/mnt/bigssd/) and supposedly used GC successfully
- **Files on DGX:** train_lora_sae_teacher_v1.py (May 8, broken path), train_micro.py (r=128, seq=1024, no GC), train_reentrant.py (r=256, seq=4096, GC default)
- **Next action:** Fix May 8 script log path and test if gradient checkpointing works with that script's pattern

### Session-to-Training-Data Pipeline Gap (May 14, 2026)

**Finding:** The existing Hermes iteration engine (cerebrum_memory.db with 244 experiences) and distillation bridge (2 staging tips) are NOT feeding into Qwen model training. The pipeline captures experiences but only 0.8% become tips, and none become training data.

**Existing infrastructure on DGX:**
- `~/.hermes/cerebrum_memory.db` — 244 experiences, 2 staging tips
- `agent/iteration_engine.py` — Sub-millisecond pattern matching
- `agent/distillation_bridge.py` — Converts outcomes → tips
- `agent/adaptive_cortex.py` — Real-time personalized learning

**The gap:** Distilled tips go back to Hermes context, but never become training data for the Qwen LoRA.

**Anti-pattern: Building parallel export pipeline**
- Wrong: Create `export_sessions_to_training.py` that scans raw session files independently
- Right: Tap into existing `experiences` table and export high-quality experiences as ShareGPT format
- Right: Fix the distillation bridge conversion rate (2 tips from 244 experiences = 0.8%)

**Correct approach:**
1. Export from `cerebrum_memory.db` experiences table (not raw sessions)
2. Filter for high-quality experiences (success rate, confidence > 0.7)
3. Convert to ShareGPT format for Qwen training
4. Merge with existing tiered training data

**Verification:**
```bash
# Check existing experiences
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT action_type, result, COUNT(*) FROM experiences GROUP BY action_type, result"

# Check staging tips
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT content, source_tier FROM staging_tips"
```
### CRITICAL: Shell Escaping Pitfall — SSH File Transfer (May 14, 2026)
When creating Python scripts via SSH/terminal, NEVER use inline heredocs or f-strings with newlines. The shell interprets `\n` and quote characters, causing unterminated string literal errors.

**Wrong:**
```bash
ssh host "cat > file.py << 'EOF'
print("hello\nworld")
EOF"
```

**Right — Method 1: Write locally, then scp:**
```bash
# On local machine
write_file /tmp/script.py "print('hello')"
scp /tmp/script.py host:/tmp/
ssh host "python3 /tmp/script.py"
```

**Right — Method 2: Base64 encode locally, decode on remote:**
```bash
# Encode script as base64 locally, pipe through SSH, decode on remote
base64 -w0 < script.py | ssh host "base64 -d > /tmp/script.py && python3 /tmp/script.py"
```

**Right — Method 3: Python one-liner via SSH (avoids all shell escaping):**
```bash
ssh host "python3 -c 'import base64; data=base64.b64decode(\"ENCODED_STRING\"); open(\"/tmp/script.py\",\"wb\").write(data)'"
```

**Anti-pattern: Using execute_code with triple-quoted strings containing newlines**
- Wrong: `execute_code` with `code="""..."""` containing `\n` — shell interprets newlines
- Right: `write_file` locally first, then `scp` to remote
- Right: Base64 encode the entire script content before SSH transfer

**Anti-pattern: Using heredocs through SSH**
- Wrong: `ssh host "cat > file.py << 'EOF'...EOF"` — shell on local machine interprets the heredoc, not the remote
- Right: Use `scp` or base64 encoding to transfer file content intact

**Verified working pattern (May 14, 2026):**
After 5+ failed attempts with heredocs and f-strings, the only reliable method was base64 encoding:
```python
import subprocess

# Encode script as base64 locally
script_content = """#!/usr/bin/env python3
print('hello world')
# ... more lines ...
"""
encoded = script_content.encode('utf-8').hex()  # or base64

# Transfer via SSH and decode
subprocess.run(['ssh', 'host', f'python3 -c "import binascii; data=binascii.unhexlify(\\'{encoded}\\'); open(\\'/tmp/script.py\\',\\'wb\\').write(data)"'])
```

**vLLM serving details:**
```bash
docker run -d --name vllm-merged \
  --gpus all --privileged --ipc host --network host \
  -v /data/models:/data/models \
  -v /data/SpecForge/custom_dflash/checkpoints:/data/checkpoints \
  -e VLLM_MARLIN_USE_ATOMIC_ADD=1 \
  --entrypoint python3 \
  ghcr.io/aeon-7/vllm-dflash:latest \
  -m vllm.entrypoints.openai.api_server \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --port 8000 --host 0.0.0.0 \
  --max-model-len 32768 --gpu-memory-utilization 0.8 \
  --max-cudagraph-capture-size 256 \
  --enable-auto-tool-choice --tool-call-parser qwen3_coder \
  --kv-cache-dtype fp8_e5m2 --load-format fastsafetensors \
  --attention-backend flashinfer --enable-prefix-caching \
  --enable-chunked-prefill --dtype bfloat16 \
  --enable-lora --max-lora-rank 256 \
  --lora-modules merged-lora=/data/checkpoints/final_model
```

**Key flags:**
- `--enable-lora` + `--max-lora-rank 256` + `--lora-modules` for LoRA serving
- `--max-model-len 32768` for agent workloads (saves ~37GB vs 262K)
- `--dtype bfloat16` — FP8 weight quantization fails with torch.compile pickling errors
- `--kv-cache-dtype fp8_e5m2` — Safe for KV cache (different from weight FP8)

**Hermes launch:** `hermes-dgx --model merged-lora`

## Current Live Training State (May 13, 2026 23:00 UTC) — OBSOLETE
- **Status: TRAINING WAS LIVE BUT FROM WRONG MODEL (base instead of merged)**
- **Mistake:** Started from `/data/models/Qwen3.6-27B-Uncensored/` instead of `final_model_merged/`
- **Step 0 loss:** 3.4022 (higher than merged's 1.19, indicating prior training discarded)
- **Corrected:** Stopped and restarted from merged model (see above)

## Current Live Training State (May 13, 2026 22:30 UTC) — OBSOLETE
- **Status: TRAINING IS LIVE AND RUNNING** (tier1 only)
- **Training script:** `/data/SpecForge/custom_dflash/train_qwen_gc_working.py`
- **Systemd service:** `qwen-training.service` (uses `/usr/bin/python3`, NOT train-venv)
- **Config:** Qwen3.6-27B-Uncensored, LoRA r=128, alpha=256, seq_len=1024, batch=1, grad_accum=4
- **Gradient checkpointing:** ENABLED with `use_reentrant=False` — works perfectly
- **GPU memory:** 53.8GB (model) → 56.4GB (LoRA) → ~58GB (training)
- **Optimizer:** 8-bit AdamW
- **Data:** 327k pre-tokenized examples from tier1_preprocessed.jsonl
- **Max steps:** 10,000, checkpoint every 500 steps
- **Verified:** 5/5 test steps passed with gradient checkpointing (forward ~2.5s, backward ~8.5s)

## Current Live Training State (May 13, 2026 22:00 UTC) — OBSOLETE
- **Status:** TRAINING BLOCKED — Gradient checkpointing DEADLOCK with Qwen3.5 linear attention
- **Finding:** model.gradient_checkpointing_enable() causes process to enter D state (uninterruptible sleep) at first forward pass
- **Without GC:** OOM at 117GB even with seq_len=1024, r=128, batch=1
- **With GC (use_reentrant=False):** Deadlock after "Using 8-bit AdamW"
- **With GC (use_reentrant=True):** Same deadlock
- **Memory breakdown without GC:** Model 51GB + LoRA + activations + gradients + optimizer = 117GB+ (exceeds 121GB)
- **Critical open question:** Does the May 8 script (train_lora_sae_teacher_v1.py) actually work? It has broken log path (/mnt/bigssd/) and supposedly used GC successfully
- **Files on DGX:** train_lora_sae_teacher_v1.py (May 8, broken path), train_micro.py (r=128, seq=1024, no GC), train_reentrant.py (r=256, seq=4096, GC default)
- **Next action:** Fix May 8 script log path and test if gradient checkpointing works with that script's pattern

## Previous Training State (May 13, 2026 22:30 UTC) — OBSOLETE
- **Status: TRAINING ABANDONED — GB10 cannot practically train 27B models**
- **Finding:** Both BF16+grad_checkpointing (~517s/step) and QLoRA (~529s/step) are intractably slow
- **Root cause:** GPU compute throughput bottleneck, not memory
- **GPU:** 121GB VRAM sufficient, but SM throughput too low for 27B forward/backward
- **Alternatives:** Train 7B model, use GB10 for inference, or use cloud A100/H100
- **Pre-tokenized data:** `/data/SpecForge/custom_dflash/preprocessed/tier1_preprocessed.jsonl` (327k examples, 20.6GB) — reusable for cloud training
- **Datasets:** tier1 (328k), tier2 (131k), tier3 (194) — ready for upload to cloud

## Previous Training State (May 13, 2026 22:00 UTC) — OBSOLETE
- **Status:** TRAINING BLOCKED — Gradient checkpointing DEADLOCK with Qwen3.5 linear attention
- **Finding:** model.gradient_checkpointing_enable() causes process to enter D state (uninterruptible sleep) at first forward pass
- **Without GC:** OOM at 117GB even with seq_len=1024, r=128, batch=1
- **With GC (use_reentrant=False):** Deadlock after "Using 8-bit AdamW"
- **With GC (use_reentrant=True):** Same deadlock
- **Memory breakdown without GC:** Model 51GB + LoRA + activations + gradients + optimizer = 117GB+ (exceeds 121GB)
- **Critical open question:** Does the May 8 script (train_lora_sae_teacher_v1.py) actually work? It has broken log path (/mnt/bigssd/) and supposedly used GC successfully
- **Files on DGX:** train_lora_sae_teacher_v1.py (May 8, broken path), train_micro.py (r=128, seq=1024, no GC), train_reentrant.py (r=256, seq=4096, GC default)
- **Next action:** Fix May 8 script log path and test if gradient checkpointing works with that script's pattern

## Previous Training State (May 13, 2026 19:30 UTC) — OBSOLETE
- **Status:** TRAINING ABANDONED — Both transformers.Trainer and QLoRA approaches are intractably slow (~517s/step)
- **Root cause:** transformers.Trainer duplicates tensors (+16GB), forcing gradient checkpointing which adds ~25x overhead
- **Discovery:** May 8 training used CUSTOM LOOP at ~20s/step — same model, same GPU, 25x faster
- **Key difference:** Custom loop + 8-bit AdamW + no tensor duplication = ~62GB, no checkpointing needed
- **Next approach:** Use custom loop based on `train_lora_sae_teacher_v1.py` for tiered training
- **Working script:** `/data/SpecForge/custom_dflash/train_lora_sae_teacher_v1.py` (May 8, 10k steps completed)
- **Failed scripts:** `train_final.py` (Trainer, 517s/step), `train_qlora.py` (529s/step)
- **Lesson:** For 27B on GB10, custom loop is REQUIRED. transformers.Trainer is not viable.

## Previous Training State (May 13, 2026 19:30 UTC) — OBSOLETE
- **Status:** TRAINING ABANDONED — Both transformers.Trainer and QLoRA approaches are intractably slow (~517s/step)
- **Root cause:** transformers.Trainer duplicates tensors (+16GB), forcing gradient checkpointing which adds ~25x overhead
- **Discovery:** May 8 training used CUSTOM LOOP at ~20s/step — same model, same GPU, 25x faster
- **Key difference:** Custom loop + 8-bit AdamW + no tensor duplication = ~62GB, no checkpointing needed
- **Next approach:** Use custom loop based on `train_lora_sae_teacher_v1.py` for tiered training
- **Working script:** `/data/SpecForge/custom_dflash/train_lora_sae_teacher_v1.py` (May 8, 10k steps completed)
- **Failed scripts:** `train_final.py` (Trainer, 517s/step), `train_qlora.py` (529s/step)
- **Lesson:** For 27B on GB10, custom loop is REQUIRED. transformers.Trainer is not viable.

## Previous Training State (May 13, 2026 18:00 UTC) — OBSOLETE
- **Status:** TRAINING NOT YET LAUNCHED — Incorrectly diagnosed as CUDA OOM
- **Actual cause:** transformers.Trainer tensor duplication, not raw OOM
- **Fix attempted:** Gradient checkpointing (made it 25x slower, not fixed)
- **Training script:** `/data/SpecForge/custom_dflash/train_simple.py` (Trainer-based, intractable)

## Previous Training State (May 10, 2026 17:10 UTC)
- **Status:** TRAINING COMPLETE — Step 10000/10000 reached
- **Final checkpoint:** checkpoint_step_10000 saved
- **LoRA merge:** STARTED but NOT VERIFIED (see pitfall above)
- **final_model_merged/:** Only config.json + generation_config.json (NO WEIGHTS)
- **Action needed:** Verify merge completion or re-run merge manually
- **Loss trajectory:** 2.7 → 0.87 (68% decrease)
- **CE loss:** 0.55 (excellent)
- **Training time:** ~55.8 hours continuous
- **Script used:** `train_lora_sae_teacher_v1.py` (custom loop + 8-bit AdamW + teacher distillation + SAE)

## SSH Connection
- Host: `spark-85e8.local` or `10.0.0.171`
- User: `djg6228`
- Key: `~/Library/Application Support/NVIDIA/Sync/config/nvsync.key`
- Config: `~/Library/Application Support/NVIDIA/Sync/config/ssh_config`

## Real-Time Status Check Commands

### Quick Status (1 command)
```bash
ssh djg6228@spark-85e8.local "grep -E 'Step [0-9]+/[0-9]+' /mnt/bigssd/train_v2_max1000.log | tail -3"
```

### Full Status (process + GPU + latest steps)
```bash
ssh djg6228@spark-85e8.local "ps aux | grep train | grep -v grep; nvidia-smi | grep -E 'GPU|Processes' -A 20; grep -E 'Step [0-9]+/[0-9]+' /mnt/bigssd/train_v2_max1000.log | tail -5"
```

### ETA Calculation (from log)
Use `scripts/estimate_training_eta.py` locally or on DGX:
```bash
python3 scripts/estimate_training_eta.py /mnt/bigssd/train_v2_max1000.log
```
Measures actual step rate from last N steps, calculates exact ETA.

### Completion Verification
```bash
# 1. Check process gone
ssh djg6228@spark-85e8.local "ps aux | grep train | grep -v grep"

# 2. Check weight files exist
ssh djg6228@spark-85e8.local "find /data/SpecForge/custom_dflash/checkpoints/final_model_merged/ -name '*.safetensors' | wc -l"

# 3. Check checkpoint fallback
ssh djg6228@spark-85e8.local "ls -lh /data/SpecForge/custom_dflash/checkpoints/checkpoint_step_10000/"
```

## Training Scripts
- **Main:** `train_lora_sae_teacher_v1.py` (v2 variants: `train_v2_max1000.py`, `train_r256_final.py`)
- **Log:** `/mnt/bigssd/train_v2_max1000.log`
- **Checkpoints:** `/data/SpecForge/custom_dflash/checkpoints/checkpoint_step_*`
- **Merged output:** `/data/SpecForge/custom_dflash/checkpoints/final_model_merged/`

## Recovery Patterns

### If training crashes mid-run
1. Check latest checkpoint: `ls -t /data/SpecForge/custom_dflash/checkpoints/ | head -1`
2. Check log tail: `tail -20 /mnt/bigssd/train_v2_max1000.log`
3. If checkpoint exists, relaunch with resume
4. If no checkpoint, investigate error before relaunching

### If merge fails (no weight files in final_model_merged/)
1. Verify checkpoint_step_10000/ exists and is complete
2. Re-run merge manually using PEFT merge_and_unload()
3. Or use training script's merge function if available
4. See `references/training-completion-verification-may10-2026.md` for recovery script

### If SSH fails under training load
- Use `ssh -o ConnectTimeout=15` to avoid hanging
- Try IP `10.0.0.171` if hostname `spark-85e8.local` fails
- Training load may cause SSH timeouts — this is normal, retry

## References

- `references/dgx-spark-ssh-connection.md` — SSH connection details and NVIDIA Sync config
- `references/ssh-loop-detection-workaround-may8-2026.md` — Loop detection workaround for SSH terminal
- `references/ssh-terminal-failure-recovery.md` — Recovery from SSH terminal failures
- `references/training-monitor-auto-resume-may7-2026.md` — Auto-resume monitoring
- `references/rank-256-stable-config-may7-2026.md` — Stable rank-256 config
- `references/rank-feasibility-analysis-pattern.md` — Rank feasibility analysis
- `references/rank-768-oom-backward-pass-may8-2026.md` — Rank 768 OOM analysis
- `references/rank-512-oom-backward-pass-may8-2026.md` — Rank 512 OOM analysis
- `references/process-duplication-oom-may8-2026.md` — Process duplication OOM
- `references/process-duplication-auto-resume-may8-2026.md` — Auto-resume with process duplication
- `references/oom-stuck-kill-resume-hazard.md` — OOM stuck kill resume hazard
- `references/pytorch-2.6-weights-only-breaks-resume-may8-2026.md` — PyTorch 2.6 weights_only issue
- `references/checkpoint-corruption-verification-may8-2026.md` — Checkpoint corruption verification
- `references/dgx-gpu-memory-reconciliation.md` — GPU memory reconciliation
- `references/bulletproof-strips-features-may8-2026.md` — Bulletproof strips features
- `references/evaluation-framework-post-training-may8-2026.md` — Post-training evaluation
- `references/post-training-deployment-may8-2026.md` — Post-training deployment
- `references/direct-answer-delay-frustration-may8-2026.md` — Direct answer delay frustration
- `references/autobrowse-realtime-integration-may7-2026.md` — Autobrowse integration
- `references/training-completion-verification-may10-2026.md` — **CRITICAL: Don't trust "Merging LoRA weights..." log message. Verify with `find *.safetensors` before declaring training complete.**
- `references/lora-r256-memory-analysis-may13-2026.md` — **LoRA r=256 vs r=128 memory analysis on GB10. Only 4GB extra GPU memory for doubling trainable params. Earlier r=256 "failure" was CPU-only PyTorch, not actual OOM.**
- `references/lora-merge-recovery-manual-merge-may10-2026.md` — **Manual merge recovery when training script's merge_and_unload() fails silently. Includes SSH background execution pattern and missing adapter_config.json fix.**
- `references/dataset-consolidation-tiered-training-may13-2026.md` — **Dataset consolidation for tiered training: converting raw datasets (reasoning, health/Synthea) into input-output JSONL format for PEFT/LoRA training.**
- `references/axolotl-incompatibility-gb10-workaround-may13-2026.md` — **Axolotl is incompatible with DGX Spark GB10. Use direct PEFT + transformers.Trainer instead. Includes CRITICAL `low_cpu_mem_usage=False` fix for meta-device gradient errors, verified training script pattern, and pre-tokenization requirement for 2M+ example datasets.**
- `references/cuda-oom-forward-pass-may13-2026.md` — **CUDA OOM on first forward pass masquerading as "training hang". Memory breakdown, futex wait explanation, gradient checkpointing fix, and 3-step verification pattern.**
- `references/axolotl-dataset-format-conversion-may13-2026.md` — **Axolotl `chat_template` type requires `messages` field, not `input/output`. Conversion script for 2M+ example datasets.**
- `references/axolotl-preprocessing-slowdown-pattern-may13-2026.md` — **Preprocessing speed drops 40x (4000→100 examples/sec) as memory pressure increases. Expected behavior for large datasets.**
- `references/training-monitoring-ssh-pattern.md` — **SSH + log tail pattern for monitoring remote training. Process alive check, tokenization progress parsing, warning signs, automation.**
- `references/axolotl-training-launch-background-may13-2026.md` — **Launching axolotl training in background on DGX. Hermes `terminal(background=true)` does NOT background on remote host. Use `nohup` + `subprocess.run` via `execute_code` instead.**
- `references/dgx-training-telemetry-monitoring-may13-2026.md` — **Real-time telemetry server + health monitor daemon for DGX training. HTTP endpoints for loss/LR tracking, GPU utilization alerts, stale metric detection.**
- `references/dgx-training-session-state-may13-2026.md` — **Session state snapshot for resuming work across CLI sessions. Pre-tokenization status, verified stack, active PIDs, next steps.**
- `references/gb10-training-intractability-qlora-vs-gradient-checkpointing-may13-2026.md` — **CRITICAL: GB10 cannot practically train 27B models. Both QLoRA and gradient checkpointing are intractably slow (~517-529s/step). GPU compute throughput is the bottleneck, not memory. Includes measured data, alternatives, and anti-patterns.**
- `references/lazy-loading-multi-tier-training-may13-2026.md` — **Lazy loading + ConcatDataset repetition for multi-tier datasets. Avoids WeightedIterableDataset deadlock, OOM from full RAM load, and fork memory doubling. Includes anti-pattern table and verification steps.**
- `references/dgx-environment-cpu-only-torch-trap-may13-2026.md` — **CRITICAL: DGX train-venv has CPU-only PyTorch. The "gradient checkpointing deadlock" was actually this environment bug. Always verify `torch.cuda.is_available()` before debugging training issues.**
- `references/gb10-training-intractability-qlora-vs-gradient-checkpointing-may13-2026.md` — **CRITICAL: GB10 cannot practically train 27B models. Both QLoRA and gradient checkpointing are intractably slow (~517-529s/step). GPU compute throughput is the bottleneck, not memory. Includes measured data, alternatives, and anti-patterns.**
- `references/meta-device-gradient-error-may13-2026.md` — **CRITICAL: `low_cpu_mem_usage=False` is required for LoRA on >20B models. Full error signature, reproduction, and verification steps.**
- `references/ssh-background-process-confusion-may13-2026.md` — **Diagnostic checklist for when user reports "training crashed". Distinguishes between: SSH session termination, pre-tokenization, stale logs, and actual training failure.**
- `references/dgx-training-session-state-may13-2026.md` — **Session state snapshot for resuming work across CLI sessions. Pre-tokenization status, verified stack, active PIDs, next steps.**
- `references/dgx-qwen-training-deadlock-analysis-may14-2026.md` — **Gradient checkpointing deadlock with Qwen3.5 linear attention. Without GC OOM at 117GB. May 8 script mystery with broken log path. Files and next actions documented.**
- `references/shell-escaping-ssh-script-deployment-may14-2026.md` — **NEVER use heredocs through SSH. After 5+ failed attempts, hex encoding is the only reliable method for deploying Python scripts to DGX via SSH.**
- `references/dgx-iteration-pipeline-fix-may14-2026.md` — **Distillation daemon was stuck — 238/247 experiences had empty lessons. Fixed by extracting lessons from ALL experiences (successes + failures), lowering threshold 3→2. Result: 59 tips from 247 experiences.**
- `references/distillation-daemon-v2-fix-may14-2026.md` — **Distillation daemon v2: Extract lessons from successes, not just failures. Includes backfill script, success-pattern heuristics, frequency threshold adjustment, and verification commands.**

## Templates

- `templates/train_all_tiers.py` — **Working training script with all 3 tiers of data. Uses system Python, gradient checkpointing with `use_reentrant=False`, 8-bit AdamW, custom collator. Verified LIVE on DGX Spark GB10. ~38s/step.**
- `templates/train_gradient_checkpointed.py` — QLoRA training script with 4-bit NF4 + paged AdamW. **Note: As of May 13 2026, QLoRA on GB10 is still intractably slow for 27B models. Provided for reference and smaller models.**
- `templates/train_custom_loop.py` — **Custom training loop for 27B on GB10. Based on May 8 success (train_lora_sae_teacher_v1.py). Uses 8-bit AdamW, no tensor duplication, no gradient checkpointing. Expected ~20s/step.**
- `templates/train_simple.py` — Simplified tiered training with lazy loading + ConcatDataset repetition. Use when combining multiple datasets of different sizes. Avoids WeightedIterableDataset deadlock.
- `templates/train_direct.py` — Direct PEFT training script for GB10 (verified working)
- `templates/launch_training.sh` — Launch training script
- `templates/dgx_watchdog.sh` — DGX watchdog script

## Scripts

- `scripts/estimate_training_eta.py` — Calculate exact ETA from training log step rate. Run locally or on DGX via SSH.
- `scripts/dgx_distillation_daemon.py` — **Fixed distillation daemon that extracts lessons from ALL experiences (successes + failures). Runs as systemd service, auto-distills every 5 minutes, exports training data hourly.**