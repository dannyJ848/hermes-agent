import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import sys
sys.path.insert(0, '/data/SpecForge/custom_dflash')
from integrate_qwen_sae import QwenWithSAE

print("Testing Qwen+SAE integration with wave loading (2 waves only)...")

# Load model
model = QwenWithSAE(
    base_model_path="/data/models/Qwen3.6-27B-Uncensored",
    sae_dir="/data/models/Qwen-Scope"
)

print(f"\nModel loaded. Testing with short text...")
text = "Hello"
tokenizer = AutoTokenizer.from_pretrained("/data/models/Qwen3.6-27B-Uncensored", trust_remote_code=True)
inputs = tokenizer(text, return_tensors="pt", max_length=5, truncation=True)
inputs = {k: v.to(model.device) for k, v in inputs.items()}

with torch.no_grad():
    outputs = model(**inputs)

print(f"Logits shape: {outputs['logits'].shape}")
print(f"SAE features collected: {len(outputs['sae_features'])} layers")
if outputs['sae_features']:
    first_key = list(outputs['sae_features'].keys())[0]
    print(f"First SAE feature shape: {outputs['sae_features'][first_key].shape}")

print(f"\nGPU memory: {torch.cuda.memory_allocated() / 1e9:.1f}GB")
print("\n✅ Wave-loading integration test passed!")
