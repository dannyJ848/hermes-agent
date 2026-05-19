# Post-Training Deployment — May 8, 2026

## Deployment Pipeline (after training completes)

### 1. Merge LoRA into Base Model
```bash
cd /data/SpecForge/custom_dflash
bash merge_model.sh
```
Produces: `checkpoints/final_merged_model/` (~54GB BF16)

### 2. Evaluate
```bash
python3 evaluate_model.py
```
Benchmarks: MMLU, GSM8K, HumanEval, BBH, ARC, Winogrande
Custom: Wason selection, syllogisms, counterfactuals, proof verification
Adversarial: Ambiguous premises, contradictory evidence, edge cases

### 3. Deploy vLLM + Hermes Integration
```bash
bash deploy_hermes_qwen.sh
```
- Port: 8000
- Dtype: bfloat16 (no quantization)
- Max model len: 32768
- GPU memory utilization: 95%
- API key: `hermes-local`

### 4. Hermes Agent Config (100% local, no fallback)
```yaml
providers:
  local_qwen:
    base_url: http://localhost:8000/v1
    api_key: hermes-local
    model: qwen-27b-expert-logician
    timeout: 120
    max_tokens: 4096
    temperature: 0.7

routing_rules:
  - pattern: ".*"
    provider: local_qwen
    priority: 1
```

## Key Decisions
- BF16 only — no quantization preserves adaptability for continued training
- Rank 256 max — SAE feature extraction OOMs at 512+
- No external fallback — all traffic stays on DGX
- weights_only=False — required for PyTorch 2.6 checkpoint compatibility

## File Locations
| File | Path |
|------|------|
| Training script | `/data/SpecForge/custom_dflash/train_lora_sae_teacher_v1.py` |
| Merged model | `/data/SpecForge/custom_dflash/checkpoints/final_merged_model/` |
| Evaluation | `/data/SpecForge/custom_dflash/evaluate_model.py` |
| Merge script | `/data/SpecForge/custom_dflash/merge_model.sh` |
| Deploy script | `/data/SpecForge/custom_dflash/deploy_hermes_qwen.sh` |
| Pipeline | `/data/SpecForge/custom_dflash/post_training_pipeline.sh` |
| Logs | `/mnt/bigssd/train_r256_final.log` |
| vLLM logs | `/mnt/bigssd/vllm_server.log` |
