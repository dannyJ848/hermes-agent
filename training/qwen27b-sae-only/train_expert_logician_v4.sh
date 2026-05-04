#!/bin/bash
# Training launcher with memory optimization
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export CUDA_LAUNCH_BLOCKING=0
export TORCH_USE_CUDA_DSA=0

cd /data/SpecForge/custom_dflash
python3 train_expert_logician_v4.py > /mnt/bigssd/train_expert_logician_v4.log 2>&1
