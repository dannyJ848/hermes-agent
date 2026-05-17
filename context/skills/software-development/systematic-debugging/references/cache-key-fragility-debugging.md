# Cache Key Fragility: Content-Based Hash Debugging

## Pattern
When two components (producer + consumer) use content-based hashes (MD5, SHA) as cache keys, **ANY mismatch in the data pipeline produces 100% cache misses** — silently, with no errors.

## Symptoms
- Cache exists (thousands of entries)
- Consumer never finds entries (cache miss rate ~100%)
- No error messages — system degrades gracefully to fallback path
- Performance drops but doesn't crash
- Logs show fallback path active (e.g., "computing on-the-fly", "skipping distillation")

## Root Cause Layers
The cache key depends on a chain of transformations. One mismatch anywhere = complete failure:

```
Raw data → Extraction → Formatting → Tokenization → Truncation → Padding strip → Hash
     ↑          ↑            ↑            ↑              ↑              ↑
  Schema    Columns    Join chars   Tokenizer    Max length   Pad token ID
```

## The Five Layers to Check

### Layer 1: Data Schema / Column Extraction
Producer and consumer must extract the SAME columns from the raw data.

**Example mismatch:**
- Producer: handles `text`, `conversation`, `messages`, `content`, `prompt` + fallback concatenation
- Consumer: only handles `conversations`, `messages`
- Dataset has columns `['problem', 'deepseek_reasoning', 'deepseek_solution']` — no `messages` field
- Consumer returns empty string → empty tokens → empty hash → cache miss

**Debug:**
```python
producer_text = producer_extract(row)
consumer_text = consumer_extract(row)
assert producer_text == consumer_text, f"EXTRACTION MISMATCH: {repr(producer_text)} != {repr(consumer_text)}"
assert len(producer_text) > 0, "EMPTY TEXT — check column handling"
```

### Layer 2: Text Formatting
Producer and consumer must format text identically (join characters, spacing, ordering).

**Example mismatch:**
- Producer: joins with `\n\n` (double newline)
- Consumer: joins with `\n` (single newline)
- Different text → different tokens → different hash

**Debug:**
```python
assert producer_text == consumer_text, f"FORMAT MISMATCH:\n{repr(producer_text)}\n!=\n{repr(consumer_text)}"
```

### Layer 3: Tokenizer
Producer and consumer must use the EXACT SAME tokenizer (same vocab, same special tokens).

**Example mismatch:**
- Producer: `/data/models/Qwen3-0.6B/` tokenizer
- Consumer: student model's tokenizer (`/data/models/Qwen3.6-27B-Uncensored/`)
- Different vocab files → different token IDs → different hash

**Debug:**
```bash
# Compare tokenizer.json MD5 hashes
md5sum /path/to/producer/tokenizer.json
md5sum /path/to/consumer/tokenizer.json
# Different hashes = different tokenizers = cache miss
```

```python
# Compare tokenization output
t1 = producer_tokenizer(text)
t2 = consumer_tokenizer(text)
assert t1['input_ids'].tolist() == t2['input_ids'].tolist(), "TOKENIZER MISMATCH"
```

### Layer 4: File Ordering
If the cache key includes a file index or sample index, producer and consumer must process files in the SAME order.

**Example mismatch:**
- Producer: `sorted(files)` — deterministic alphabetical
- Consumer: `os.walk()` — arbitrary filesystem order
- Same row at index 5 in file A vs file B → different content → different hash

**Debug:**
```python
producer_files = sorted(glob("**/*.parquet"))
consumer_files = dataset.real_files
assert producer_files == consumer_files, f"FILE ORDER MISMATCH: first diff at index {next(i for i,(a,b) in enumerate(zip(producer_files, consumer_files)) if a!=b)}"
```

### Layer 5: Post-Processing (Truncation, Padding, Special Tokens)
After tokenization, producer and consumer must apply the SAME post-processing.

**Example mismatches:**
- Truncation: `max_length=512` vs `max_length=1024`
- Padding strip: strip `pad_token_id` vs keep it
- Special tokens: add `bos`/`eos` vs don't
- Contiguous: `.contiguous()` vs not

**Debug:**
```python
# Compare full tokenization pipeline
def full_pipeline(text, tokenizer, max_length=512):
    tokens = tokenizer(text, truncation=True, max_length=max_length, return_tensors="pt")
    input_ids = tokens['input_ids'][0]
    # Strip padding
    mask = input_ids != tokenizer.pad_token_id
    input_ids = input_ids[mask]
    if len(input_ids) == 0:
        input_ids = input_ids[:1]
    return input_ids.contiguous()

p = full_pipeline(text, producer_tokenizer)
c = full_pipeline(text, consumer_tokenizer)
assert p.tolist() == c.tolist(), f"POST-PROCESS MISMATCH: {p.tolist()} != {c.tolist()}"
```

## Verification Script

```python
import hashlib, json

def verify_cache_compatibility(producer_fn, consumer_fn, sample_data, cache_index):
    """
    Verify producer and consumer produce identical cache keys.
    Returns (hit_rate, mismatches_by_layer).
    """
    # Layer 1: Extraction
    p_text = producer_fn['extract'](sample_data)
    c_text = consumer_fn['extract'](sample_data)
    if p_text != c_text:
        return 0.0, {'layer': 'extraction', 'producer': p_text, 'consumer': c_text}
    
    # Layer 2: Tokenization
    p_tokens = producer_fn['tokenize'](p_text)
    c_tokens = consumer_fn['tokenize'](c_text)
    if p_tokens.tolist() != c_tokens.tolist():
        return 0.0, {'layer': 'tokenization', 'diff_at': next(i for i,(a,b) in enumerate(zip(p_tokens, c_tokens)) if a!=b)}
    
    # Layer 3: Hash
    p_hash = hashlib.md5(p_tokens.numpy().tobytes()).hexdigest()
    c_hash = hashlib.md5(c_tokens.numpy().tobytes()).hexdigest()
    if p_hash != c_hash:
        return 0.0, {'layer': 'hash', 'producer': p_hash[:16], 'consumer': c_hash[:16]}
    
    # Layer 4: Cache lookup
    if p_hash in cache_index:
        return 1.0, {'layer': 'cache_hit'}
    else:
        return 0.0, {'layer': 'cache_miss', 'key': p_hash[:16]}
```

## Prevention

1. **Single source of truth:** Share the formatting/tokenization function between producer and consumer. Don't duplicate logic.
2. **Version cache keys:** Include a version hash of the formatting function in the cache key. If the function changes, invalidate old cache.
3. **Validation on startup:** Run `verify_cache_compatibility()` before starting training. Fail fast if hit rate < 95%.
4. **Logging:** Log cache hit/miss rate every N steps. Alert if rate drops below threshold.

## Cross-Domain Examples

| Domain | Producer | Consumer | Typical Mismatch |
|--------|----------|----------|------------------|
| ML training | Precompute teacher cache | Training loop | Tokenizer, text format, file order |
| Web caching | CDN edge | Origin server | URL normalization, query param ordering |
| Database | Write path | Read path | Serialization format, timestamp precision |
| Build systems | Dependency hash | Build cache | File ordering, env var inclusion |
| API caching | Request signer | Cache lookup | Header ordering, encoding |

## Key Insight

> Content-based cache keys are **brittle by design**. They guarantee exact matching but require exact pipeline parity. When debugging cache misses, check ALL five layers systematically. One mismatch anywhere = complete failure.
