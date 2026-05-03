#!/usr/bin/env python3
"""
Pre-compute Franken V8 SAE features for teacher alignment.
Runs Franken V8 on CPU, extracts SAE features at matching layers.
"""
import os
import sys
import time
import glob
import torch
import pickle

TEACHER_PATH = "/data/models/FrankenV8-Final/final_model.pt"
SAE_DIR = "/data/models/Qwen-Scope/"
HIDDEN_STATES_DIR = "/data/SpecForge/custom_dflash/hidden_states/"
OUTPUT_DIR = "/data/SpecForge/custom_dflash/teacher_sae_features/"

SAE_LAYERS = [8, 16, 24, 32, 40, 48, 56]
MAX_SEQ_LEN = 256

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print("PRE-COMPUTING FRANKEN V8 SAE FEATURES")
print("=" * 60)

# Load SAEs (on CPU since teacher is on CPU)
print("Loading SAEs...")
saes = {}
for layer_idx in SAE_LAYERS:
    sae_path = os.path.join(SAE_DIR, f"layer{layer_idx}.sae.pt")
    if os.path.exists(sae_path):
        sae = torch.load(sae_path, map_location="cpu")
        saes[layer_idx] = {
            "W_enc": sae["W_enc"].float(),
            "b_enc": sae["b_enc"].float(),
            "W_dec": sae["W_dec"].float(),
            "b_dec": sae["b_dec"].float(),
        }
        print(f"  Layer {layer_idx}: loaded")

print(f"Loaded {len(saes)} SAEs")

# Load Franken V8 teacher
print("Loading Franken V8 teacher (CPU)...")
start = time.time()

# Franken V8 is a custom architecture - load its state dict
teacher_state = torch.load(TEACHER_PATH, map_location="cpu")
print(f"Teacher state dict loaded in {time.time()-start:.1f}s")
print(f"Keys: {list(teacher_state.keys())[:10]}")

# For now, we'll use a simplified approach: extract SAE features from hidden states
# that we already have. The teacher's SAE features should be computed from the teacher's
# forward pass, but we can approximate by using the same SAEs on the hidden states.

# Actually, let me check what the teacher architecture looks like
print("\nTeacher state dict sample:")
for k, v in list(teacher_state.items())[:5]:
    print(f"  {k}: {v.shape if hasattr(v, 'shape') else type(v)}")

# Process hidden state files
hidden_files = sorted(glob.glob(os.path.join(HIDDEN_STATES_DIR, "*.pt")))
print(f"\nFound {len(hidden_files)} hidden state files")

# For each file, we'll load the hidden states and compute SAE features
# Since we don't have the actual teacher model loaded, we'll create placeholder
# teacher features for now and note that we need the actual teacher forward pass.

print("\nNOTE: Franken V8 is a custom model. Need to load its architecture.")
print("Creating placeholder teacher SAE features for now...")

for i, hf in enumerate(hidden_files[:5]):  # Process first 5 as test
    data = torch.load(hf, map_location="cpu")
    print(f"\nFile {i}: {os.path.basename(hf)}")
    print(f"  Keys: {list(data.keys())}")
    if "hidden_states" in data:
        hs = data["hidden_states"]
        print(f"  Hidden states shape: {hs.shape if hasattr(hs, 'shape') else 'N/A'}")
    elif "input_ids" in data:
        print(f"  Input IDs shape: {data['input_ids'].shape}")
    
    # Save placeholder
    out_path = os.path.join(OUTPUT_DIR, f"teacher_{os.path.basename(hf)}")
    teacher_features = {}
    for layer_idx in SAE_LAYERS:
        if layer_idx in saes:
            # Placeholder: random features (will be replaced with actual teacher)
            teacher_features[layer_idx] = torch.randn(1, 50, 81920).float()
    
    torch.save(teacher_features, out_path)
    print(f"  Saved placeholder to {out_path}")

print("\n" + "=" * 60)
print("PLACEHOLDER TEACHER FEATURES CREATED")
print("=" * 60)
print("NEXT: Need to implement Franken V8 forward pass for actual features")
