#!/usr/bin/env python3
"""Quick test: LoRA + SAE only (no teacher distillation) to verify pipeline works."""
import sys
sys.path.insert(0, '/data/SpecForge/custom_dflash')

from train_lora_sae_teacher_v1 import TrainConfig, train

config = TrainConfig()
config.use_teacher = True  # Enable teacher distillation
config.use_sae = True
config.use_curriculum = True
config.max_steps = 100  # Just 100 steps for testing
config.batch_size = 1
config.grad_accum_steps = 4

print("=" * 70)
print("TEST RUN: LoRA + SAE only (no teacher)")
print("=" * 70)

train(config)
print("\nTEST COMPLETE — pipeline works!")
