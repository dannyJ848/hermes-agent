# Qwen 27B Training Status Tracking

## Current Status (May 9, 2026)

- **Model**: Qwen/Qwen2.5-VL-72B-Instruct (local vLLM on DGX)
- **Current step**: 5340 / 10000 (53.4%)
- **Latest loss**: 0.9443 (CE:0.663 D:1.122 SAE:0.525)
- **Weights**: (0.73, 0.36, 0.10)
- **Learning rate**: 9.54e-05
- **GPU memory**: 62.6GB
- **PID**: 443609 running on DGX at `spark-85e8.local`
- **ETA**: ~26 hours remaining
- **Training data**: `~/qwen-training-data/` (1.8MB) — push to DGX when step 10000 hits

## Status Check Command

```bash
# Check training progress on DGX
ssh dgx "tail -5 /tmp/qwen_training.log" 2>/dev/null || echo "DGX not reachable"
```

Or via Python:
```python
import subprocess
result = subprocess.run(
    ["ssh", "dgx", "tail -5 /tmp/qwen_training.log"],
    capture_output=True, text=True
)
print(result.stdout)
```

## When Training Completes

1. **Push training data** from MacBook to DGX:
   ```bash
   scp -r ~/qwen-training-data/ dgx:~/
   ```

2. **Deploy with vLLM** on DGX:
   ```bash
   # On DGX
   vllm serve Qwen/Qwen2.5-VL-72B-Instruct --tensor-parallel-size 8
   ```

3. **Configure Hermes vision provider**:
   ```yaml
   auxiliary:
     vision:
       provider: custom
       model: Qwen/Qwen2.5-VL-72B-Instruct
       base_url: http://spark-85e8.local:8000/v1
       api_key_env: NONE  # local vLLM
   ```

## Decision Rule

| Need | Action |
|------|--------|
| Check training status | `ssh dgx "tail -5 /tmp/qwen_training.log"` |
| Training complete | Push data, deploy vLLM, configure Hermes |
| Vision needed now | Use `browser_vision` for web pages, manual review for screenshots |
| MacBook usage | Hermes self-improvement ONLY |
| DGX usage | Qwen training ONLY |
