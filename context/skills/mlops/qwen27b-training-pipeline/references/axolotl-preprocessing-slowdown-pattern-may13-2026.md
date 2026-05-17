# Axolotl Preprocessing Slowdown Pattern (May 13, 2026)

## Observation
When preprocessing large datasets (2M+ examples) with axolotl, tokenization speed drops dramatically over time:

| Progress | Speed | ETA |
|----------|-------|-----|
| 0-50% | 4000-6000 examples/sec | ~10 min |
| 50-75% | 2000-3000 examples/sec | ~15 min |
| 75-80% | 1000-1500 examples/sec | ~20 min |
| 80%+ | 100-500 examples/sec | 1-2 hours |

## Root Cause
Memory pressure from accumulating tokenized examples in the Arrow dataset. As RAM fills, the `datasets.map()` operation thrashes.

## Mitigation
1. **Expect the slowdown** — don't kill and restart; it will finish eventually
2. **Monitor with `ps aux`** — if processes are still running, it's working
3. **Check debug.log** for progress: `tail -f adapters/*/debug.log`
4. **Reduce `dataloader_num_workers`** from 20 to 4-8 if RAM is constrained
5. **Use `sample_packing: false`** for initial preprocessing test runs

## Monitoring Commands

```bash
# Check if preprocessing still running
ssh djg6228@10.0.0.171 "ps aux | grep 'axolotl preprocess' | grep -v grep | wc -l"

# Check progress from debug log
ssh djg6228@10.0.0.171 "tail -5 /data/SpecForge/custom_dflash/adapters/qwen27b-tiered-r256/debug.log"

# Expected output format:
# Tokenizing Prompts (num_proc=20):  80%|████████  | 1716729/2158309 [10:32<1:45:14, 69.78 examples/s]
```

## Decision: Wait vs Kill
- **Speed > 1000 examples/sec** → Normal, wait
- **Speed 100-500 examples/sec** → Slow but progressing, wait (may take 1-2 hours)
- **Speed < 50 examples/sec** → Consider kill + reduce workers
- **No progress for 30+ min** → Kill and investigate

## Post-Preprocessing
Once preprocessing completes, axolotl saves cached datasets. Subsequent training runs will skip preprocessing and load from cache.