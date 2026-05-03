import torch
import sys
sys.path.insert(0, "/data/SpecForge/custom_dflash")
from train_modelscope_simple import FrankenV8ModelScope, SimpleSAE, load_sae_to_cpu

print("Test 1: Build model...")
model = FrankenV8ModelScope(num_layers=6, d_model=5120, d_sae=81920, vocab_size=248320)
print(f"Model params: {sum(p.numel() for p in model.parameters()):,}")

print("\nTest 2: Load SAE...")
sae = load_sae_to_cpu("/data/models/Qwen-Scope/layer32.sae.pt")
print(f"SAE params: {sum(p.numel() for p in sae.parameters()):,}")

print("\nTest 3: Forward pass...")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device).to(torch.bfloat16)
input_ids = torch.randint(0, 1000, (1, 10)).to(device)
sae_features = {"32": torch.randn(1, 10, 81920).to(device).to(torch.bfloat16)}
outputs = model(input_ids, sae_features)
print(f"Logits shape: {outputs['logits'].shape}")
print(f"Loss: {outputs['loss']}")

print("\n✅ All tests passed!")
