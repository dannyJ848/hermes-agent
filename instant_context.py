#!/usr/bin/env python3
"""
Instant Context — Qwen 27B Expert Logician Training State
Single source of truth for session resume.
Updated: May 8, 2026
"""

import json
from pathlib import Path

STATE = {
    "project": "Qwen 27B Expert Logician",
    "hardware": "DGX Spark (130GB GPU)",
    "host": "spark-85e8.local (10.0.0.171)",
    "user": "djg6228",
    
    "model_config": {
        "base": "Qwen/Qwen3.6-27B-Uncensored",
        "torch_dtype": "bfloat16",
        "frozen": True,
        "lora_r": 256,
        "lora_alpha": 512,
        "lora_target_modules": "all_linear",
        "trainable_params": "1,275,068,416 (4.53%)",
        "max_feasible_rank": 256,
        "rank_experiment_results": {
            "1024": "Crashed — weights_only error (fixed)",
            "768": "OOM at batch 1 — SAE feature extraction",
            "512": "OOM at batch 1 — SAE feature extraction",
            "256": "STABLE — 62.6GB GPU, all features active"
        }
    },
    
    "training_features": {
        "teacher_distillation": True,
        "teacher_model": "Franken V8 (8 layers, CPU)",
        "teacher_weight": 0.3,
        "sae_guidance": True,
        "sae_layers": [16, 32, 48],
        "sae_weight": 0.1,
        "multi_objective_loss": True,
        "curriculum_learning": True,
        "data_mixing": "curatedthoughts + openthoughts2-1m"
    },
    
    "current_status": {
        "step": 2290,
        "max_steps": 10000,
        "progress_percent": 22.9,
        "loss": 1.5435,
        "loss_breakdown": {"ce": 1.282, "distill": 1.359, "sae": 0.592},
        "weights": [0.89, 0.27, 0.07],
        "learning_rate": 1.81e-04,
        "gpu_memory_log": "62.6GB",
        "gpu_memory_actual": "~93GB (oscillates 0-93GB, normal for GB10)",
        "gpu_utilization": "92-93%",
        "gpu_temp_c": 63,
        "system_ram": "116.5/128GB",
        "eta_hours": 35,
        "pid": 443609,
        "status": "RUNNING",
        "last_checkpoint": "step_2200",
        "checkpoint_interval": 100,
        "loss_components": {"CE": 1.282, "distillation": 1.359, "SAE": 0.592},
        "gpu_memory_gb": 62.6,
        "gpu_utilization": 92,
        "gpu_temperature_c": 63,
        "eta_hours": 35,
        "log_file": "/mnt/bigssd/train_r256_final.log",
        "pid": 443609
    },
    
    "critical_fixes": [
        "weights_only=False on all torch.load() calls (PyTorch 2.6 compatibility)",
        "Atomic launch script — kills existing before starting new",
        "Loop guard v2 — prevents SSH intent loops"
    ],
    
    "paths": {
        "project_dir": "/data/SpecForge/custom_dflash",
        "training_script": "/data/SpecForge/custom_dflash/train_lora_sae_teacher_v1.py",
        "checkpoints": "/data/SpecForge/custom_dflash/checkpoints/",
        "latest_checkpoint": "/data/SpecForge/custom_dflash/checkpoints/checkpoint_step_1500",
        "logs": "/mnt/bigssd/train_r256_final.log",
        "merged_model": "/data/SpecForge/custom_dflash/checkpoints/final_merged_model",
        "evaluation_script": "/data/SpecForge/custom_dflash/evaluate_model.py",
        "merge_script": "/data/SpecForge/custom_dflash/merge_model.sh",
        "deploy_script": "/data/SpecForge/custom_dflash/deploy_hermes_qwen.sh",
        "pipeline_script": "/data/SpecForge/custom_dflash/post_training_pipeline.sh",
        "master_doc": "/data/SpecForge/custom_dflash/MASTER_DOC.md"
    },
    
    "deployment": {
        "format": "BF16 merged model (no quantization)",
        "inference_server": "vLLM",
        "port": 8000,
        "api_key": "hermes-local",
        "hermes_integration": "100% local Qwen, no external fallback",
        "gpu_memory_required_gb": 54,
        "expected_tokens_per_sec": "20-40"
    },
    
    "post_training_pipeline": [
        "1. bash merge_model.sh — merge LoRA into base",
        "2. python3 evaluate_model.py — benchmark suite",
        "3. bash deploy_hermes_qwen.sh — launch vLLM + Hermes config"
    ],
    
    "ssh_info": {
        "host": "10.0.0.171",
        "user": "djg6228",
        "connect_timeout": 10
    }
}


def get_state():
    """Return current training state."""
    return STATE


def print_resume_summary():
    """Print formatted resume summary."""
    s = STATE
    print("=" * 60)
    print(f"QWEN 27B EXPERT LOGICIAN — RESUME SUMMARY")
    print("=" * 60)
    print(f"Step: {s['current_status']['step']}/{s['current_status']['max_steps']}")
    print(f"Loss: {s['current_status']['loss']:.3f}")
    print(f"GPU: {s['current_status']['gpu_memory_gb']:.1f}GB, {s['current_status']['gpu_utilization']}% util")
    print(f"ETA: {s['current_status']['eta_hours']:.0f} hours")
    print(f"Log: {s['paths']['logs']}")
    print(f"PID: {s['current_status']['pid']}")
    print("=" * 60)


if __name__ == "__main__":
    print_resume_summary()
    print("\nFull state available via get_state()")
