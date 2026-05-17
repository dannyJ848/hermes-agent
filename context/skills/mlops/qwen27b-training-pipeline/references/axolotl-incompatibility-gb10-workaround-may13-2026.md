# Axolotl Incompatibility with DGX Spark GB10 (May 13, 2026)

## Problem

Axolotl (0.14-0.16) is INCOMPATIBLE with NVIDIA DGX Spark (GB10) due to PyTorch version conflicts.

**Root cause chain:**
1. GB10 has CUDA 13.0 and sm_121 GPU architecture
2. Working PyTorch for GB10: torch 2.11.0+cu130 (from eval_venv)
3. Axolotl 0.16 requires torch 2.8.0
4. Axolotl 0.15 requires torch 2.8.0
5. Axolotl 0.14 requires torch 2.8.0
6. torch 2.8.0 does NOT have CUDA 13.0 wheels for ARM64
7. Installing axolotl force-reinstalls torch 2.8.0 (non-CUDA), breaking GPU support

## Error Signatures

### Error 1: PyTorch CUDA capability mismatch
```
NVIDIA GB10 with CUDA capability sm_121 is not compatible with the current PyTorch installation.
The current PyTorch install supports CUDA capabilities sm_50 sm_80 sm_86 sm_89 sm_90 sm_90a.
```

### Error 2: torch.int4 missing (axolotl 0.14 with torch 2.5.1)
```
File ".../axolotl/utils/schemas/enums.py", line 9, in TorchAOQuantDType
    int4 = torch.int4
           ^^^^^^^^^^
AttributeError: module 'torch' has no attribute 'int4'
```

### Error 3: Flash-attn build failure
```
ModuleNotFoundError: No module named 'torch'
# During flash-attn compilation (expects torch already installed)
```

### Error 4: Torch not compiled with CUDA (after axolotl install)
```
AssertionError: Torch not compiled with CUDA enabled
```
This happens when axolotl installs torch 2.8.0 CPU-only, overwriting your CUDA torch.

## Solution 1: Separate Training Venv with CUDA Torch (RECOMMENDED)

Create an isolated training venv, install axolotl, then replace CPU torch with CUDA torch:

```bash
# Create isolated training venv
python3 -m venv ~/train-venv
source ~/train-venv/bin/activate

# Install axolotl (will pull torch 2.8.0 CPU-only and many deps)
pip install axolotl

# CRITICAL: Uninstall CPU torch, reinstall CUDA torch
pip uninstall -y torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128

# Fix axolotl telemetry bug (missing whitelist.yaml)
echo 'organizations: []' > ~/train-venv/lib/python3.12/site-packages/axolotl/telemetry/whitelist.yaml

# Verify CUDA works
python3 -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

**Key points:**
- Keep `eval_venv` (torch 2.11.0+cu130) for inference — do NOT install axolotl into it
- The separate venv prevents axolotl from breaking your working inference environment
- CUDA 12.8 wheels work on GB10's CUDA 13.0 (backward compatible)

## Solution 2: Direct PEFT + transformers.Trainer (RECOMMENDED for GB10)

Use `eval_venv` which already has the correct PyTorch (2.11.0+cu130), then install peft/accelerate and write a direct training script.

**CRITICAL: `low_cpu_mem_usage=False` is required** when loading large models (27B+) with LoRA. The default `device_map="auto"` with `low_cpu_mem_usage=True` (default) places some parameters on the "meta" device, which breaks LoRA backward pass with:
```
RuntimeError: Function MmBackward0 returned an invalid gradient at index 1 - expected device meta but got cuda:0
```

```bash
# eval_venv has correct torch for GB10
source /data/SpecForge/custom_dflash/eval_venv/bin/activate
python3 -c "import torch; print(torch.__version__)"  # 2.11.0+cu130
python3 -c "print(torch.cuda.is_available())"         # True

# Install training deps
pip install peft accelerate bitsandbytes transformers datasets

# Write direct training script (see templates/train_direct.py)
# Run training
python3 train_direct.py
```

### Verified Working Direct Training Script Pattern

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer, DataCollatorForLanguageModeling
from peft import LoraConfig, get_peft_model, TaskType
import torch

MODEL_PATH = '/data/SpecForge/custom_dflash/checkpoints/final_model_merged'

# CRITICAL: low_cpu_mem_usage=False prevents meta-device gradient errors
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16,
    device_map='cuda:0',  # Load entirely to GPU (130GB available)
    low_cpu_mem_usage=False,  # REQUIRED for LoRA backward pass
    trust_remote_code=True
)

lora_config = LoraConfig(
    r=256, lora_alpha=512,
    target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj'],
    lora_dropout=0.05, bias='none', task_type=TaskType.CAUSAL_LM
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()  # ~1.27B trainable

# Training arguments
training_args = TrainingArguments(
    output_dir='/data/SpecForge/custom_dflash/adapters/qwen27b-tiered-r256',
    num_train_epochs=2,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    warmup_steps=100,
    logging_steps=10,
    save_steps=500,
    save_total_limit=3,
    bf16=True, tf32=True,
    optim='adamw_torch',
    weight_decay=0.0, max_grad_norm=1.0,
    dataloader_num_workers=2,
    remove_unused_columns=False,
    report_to=['none']
)

trainer = Trainer(
    model=model, args=training_args,
    train_dataset=train_dataset,
    data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False)
)
trainer.train()
```

### Pre-tokenization Required for Large Datasets

**Do NOT tokenize on-the-fly** in `Dataset.__getitem__` for datasets with 2M+ examples. Tokenization becomes the bottleneck (14k examples/minute single-threaded).

**Pre-tokenize to disk first:**
```python
def pre_tokenize_file(tokenizer, input_file, output_file, max_length=4096):
    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for line in f_in:
            data = json.loads(line.strip())
            text = convert_to_text(data)  # Your format conversion
            enc = tokenizer(text, truncation=True, max_length=max_length,
                           padding='max_length', return_tensors='np')
            record = {
                'input_ids': enc['input_ids'][0].tolist(),
                'attention_mask': enc['attention_mask'][0].tolist(),
                'labels': enc['input_ids'][0].tolist()
            }
            f_out.write(json.dumps(record) + '\n')
```

Then load pre-tokenized data in training script:
```python
class PreTokenizedDataset(Dataset):
    def __init__(self, file_path):
        self.examples = []
        with open(file_path) as f:
            for line in f:
                self.examples.append(json.loads(line))
    def __len__(self): return len(self.examples)
    def __getitem__(self, idx):
        ex = self.examples[idx]
        return {
            'input_ids': torch.tensor(ex['input_ids']),
            'attention_mask': torch.tensor(ex['attention_mask']),
            'labels': torch.tensor(ex['labels'])
        }
```

## Attempted Solutions (ALL FAILED)

| Approach | Result |
|----------|--------|
| `pip install axolotl[flash-attn]` | flash-attn build fails, torch version conflict |
| `pip install axolotl==0.16.1` | reinstalls torch 2.8.0 (non-CUDA) |
| `pip install axolotl==0.15.0` | same, torch 2.8.0 overwrites CUDA build |
| `pip install axolotl==0.14.0 --no-deps` | missing torch.int4 attribute |
| Install torch 2.8.0 from cu124 index | No ARM64 CUDA 13.0 wheel available |
| Install torch 2.5.1 from cu124 index | Works but axolotl requires 2.8.0 |

## Key Differences from Axolotl

| Feature | Axolotl | Direct PEFT |
|---------|---------|-------------|
| Config format | YAML | Python script |
| Dataset loading | Built-in | Manual (datasets library) |
| Sample packing | Built-in | Manual or use `DataCollatorForLanguageModeling` |
| DeepSpeed | Built-in | Manual configuration |
| LoRA merge | Built-in | Manual `merge_and_unload()` |
| Logging | Built-in | transformers default |

## Recommendation

For GB10 training:
1. **If you need axolotl features** (YAML config, sample packing): Use Solution 1 (separate train-venv)
2. **If you want simplicity**: Use Solution 2 (direct PEFT in eval_venv)
3. **NEVER install axolotl into eval_venv** — it will break your working PyTorch installation
