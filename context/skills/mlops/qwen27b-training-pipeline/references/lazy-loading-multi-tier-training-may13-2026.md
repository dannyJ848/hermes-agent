# Lazy Loading Multi-Tier Dataset Training — May 13, 2026

## Problem
Training with multiple datasets of different sizes (tier1: 328k, tier2: 131k, tier3: 194 examples) fails when:
1. Loading all examples into RAM → OOM
2. Using `WeightedIterableDataset` with `random.choices` → deadlocks in `Trainer`
3. Using `DataLoader(num_workers > 0)` → fork doubles RAM usage
4. Killing process during model loading (~5 min) → mistaken for hang

## Solution: Lazy File-Offset Loading + ConcatDataset Repetition

### LazyPreTokenizedDataset
Stores byte offsets into JSONL file, loads single example on `__getitem__`. Memory overhead: ~8 bytes per example (offset array) vs ~30GB for full load.

```python
class LazyPreTokenizedDataset(Dataset):
    def __init__(self, file_path, max_length=4096):
        self.file_path = file_path
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
        # ... truncate/pad, return tensors
```

### Weighting via ConcatDataset Repetition
Instead of custom sampler (deadlocks), repeat smaller datasets:

```python
tier1 = LazyPreTokenizedDataset('preprocessed/tier1.jsonl')      # 328k
tier2 = LazyChatDataset('datasets/tier2.jsonl', tokenizer)       # 131k
tier3 = LazyChatDataset('datasets/tier3.jsonl', tokenizer)       # 194

# tier3 * 120 ≈ 23k → ~70/25/5% split
train_dataset = ConcatDataset([tier1, tier2] + [tier3] * 120)
```

### Critical Config
```python
TrainingArguments(
    dataloader_num_workers=0,      # CRITICAL: avoid fork memory doubling
    dataloader_pin_memory=False,   # No benefit on unified memory GB10
    remove_unused_columns=False,   # Keep all columns from datasets
)
```

## Anti-Patterns That Deadlock or OOM

| Pattern | Why It Fails | Fix |
|---------|-------------|-----|
| `WeightedIterableDataset` with `random.choices` in `__iter__` | `Trainer` expects `__len__`, iterable sampling conflicts with epoch logic | Use `ConcatDataset` with repetition |
| Pre-computing `index_map` with 900k entries | `random.choices` blocks for minutes at init | Let `ConcatDataset` + `RandomSampler` handle shuffling |
| `DataLoader(num_workers=2)` | Fork copies 30GB+ dataset into each worker | `num_workers=0` |
| `padding='max_length'` in tokenizer + `DataCollatorForSeq2Seq` | Double-padding to 4096, wastes compute | Use `DataCollatorForLanguageModeling(mlm=False)` |
| Killing process before GPU memory shows ~51GB | Model loading takes ~5 min on GB10, not a hang | Wait for `nvidia-smi` to show python process with 50GB+ |

## Verification Steps

1. **Dataset indexing:** `LazyPreTokenizedDataset` indexes 328k lines in ~7s
2. **Random access:** Single example loads in ~0.001s
3. **DataLoader iteration:** `for batch in dl: print(batch.shape)` works immediately
4. **Trainer init:** `Trainer(model=..., args=..., train_dataset=combined)` creates in <1s
5. **Model loading:** `AutoModelForCausalLM.from_pretrained(...)` takes ~5 min, GPU shows 51GB
6. **Training start:** First "Step 1: loss=X" appears within 30s of model load complete

## File Locations
- Script: `/data/SpecForge/custom_dflash/train_simple.py`
- Preprocessed: `/data/SpecForge/custom_dflash/preprocessed/tier1_preprocessed.jsonl` (327,718 examples, 20.6GB)
- Raw: `/data/SpecForge/custom_dflash/datasets/tier{1,2,3}-*-chat.jsonl`

## Session Context
- DGX Spark GB10, 121GB GPU, 128GB RAM
- Qwen 27B BF16, LoRA r=256, 8-bit AdamW
- Verified: lazy loading + ConcatDataset works, training ready to launch
