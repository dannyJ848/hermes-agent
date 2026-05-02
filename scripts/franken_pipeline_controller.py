#!/usr/bin/env python3
"""
Franken Training Pipeline Phase Transition Controller
Auto-triggers next phases when milestones complete.
"""
import os, sys, json, time, subprocess, sqlite3, signal
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/Users/dannygomez/hermes-agent")
FRANKEN_DIR = Path("/mnt/8tb/franken-training")
QWEN_SCOPE_MAC = Path("/Users/dannygomez/Downloads/Qwen-Scope-3.5-27B")
QWEN_SCOPE_SPARK = Path("/mnt/8tb/qwen-scope")
LOG_FILE = Path("/mnt/8tb/pipeline.log")
STATE_DB = Path("/mnt/8tb/pipeline_state.db")

PHASES = {
    "batch1_training": {"desc": "Franken V8 Batch 1 training", "next": "batch3_extraction"},
    "batch3_extraction": {"desc": "Batch 3 logit extraction", "next": "batch3_training"},
    "batch3_training": {"desc": "Franken V8 Batch 3 training (final)", "next": "cleanup_logits"},
    "cleanup_logits": {"desc": "Delete batch 3 logits, retain hidden states + models", "next": "qwen_scope_migration"},
    "qwen_scope_migration": {"desc": "Move Qwen-Scope SAEs from Mac to Spark, finish compilation", "next": "qwen_scope_integration"},
    "qwen_scope_integration": {"desc": "Integrate SAEs into Qwen 3.6 27B", "next": "verify_integration"},
    "verify_integration": {"desc": "Verify ModelScope integration works", "next": "final_training"},
    "final_training": {"desc": "Train Qwen 3.6 27B (with ModelScope) on Franken V8 draft", "next": "complete"},
}

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def init_db():
    conn = sqlite3.connect(STATE_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_state (
            phase TEXT PRIMARY KEY,
            status TEXT,
            started_at TEXT,
            completed_at TEXT,
            metadata TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_state(phase):
    conn = sqlite3.connect(STATE_DB)
    c = conn.cursor()
    c.execute("SELECT status, metadata FROM pipeline_state WHERE phase=?", (phase,))
    row = c.fetchone()
    conn.close()
    return row if row else ("pending", "{}")

def set_state(phase, status, metadata=None):
    conn = sqlite3.connect(STATE_DB)
    c = conn.cursor()
    now = datetime.now().isoformat()
    meta = json.dumps(metadata or {})
    c.execute("""
        INSERT OR REPLACE INTO pipeline_state (phase, status, started_at, completed_at, metadata)
        VALUES (?, ?, COALESCE((SELECT started_at FROM pipeline_state WHERE phase=?), ?), ?, ?)
    """, (phase, status, phase, now, now if status == "completed" else None, meta))
    conn.commit()
    conn.close()

def check_batch1_complete():
    """Check if Franken V8 Batch 1 training is done."""
    final_model = Path("/data/models/FrankenV8-Batch1/final_model.pt")
    return final_model.exists()

def check_batch3_extraction_complete():
    """Check if Batch 3 logit extraction is done."""
    done_marker = Path("/data/SpecForge/custom_dflash/batch_3_logits/extraction_complete.marker")
    if done_marker.exists():
        return True
    # Check if all 3334 files exist
    batch3_dir = Path("/data/SpecForge/custom_dflash/batch_3_logits")
    if batch3_dir.exists():
        files = list(batch3_dir.glob("sample_*.pt"))
        return len(files) >= 3334
    return False

def trigger_batch3_training():
    """Trigger Franken V8 Batch 3 training (resume from Batch 1 final)."""
    log("PHASE TRANSITION: Batch 3 extraction complete → Starting Batch 3 training")
    set_state("batch3_training", "running")
    
    script = Path("/data/SpecForge/custom_dflash/train_franken_v8_PROGRESSIVE_FA4.py")
    if script.exists():
        subprocess.Popen(
            [sys.executable, str(script),
             "--resume-from", "/data/models/FrankenV8-Batch1/final_model.pt",
             "--data-dir", "/data/SpecForge/custom_dflash/batch_3_logits",
             "--output-dir", "/data/models/FrankenV8-Final",
             "--num-steps", "3334",
             "--start-step", "6666"],
            cwd=str(Path("/data/SpecForge/custom_dflash")),
            stdout=open("/data/models/FrankenV8-Final/training.log", "a"),
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
    else:
        log("WARNING: training script not found")

def check_batch3_training_complete():
    """Check if Batch 3 training is done."""
    final_model = Path("/data/models/FrankenV8-Final/final_model.pt")
    return final_model.exists()

def trigger_cleanup():
    """Delete batch 3 logits, retain hidden states + models."""
    log("PHASE TRANSITION: Batch 3 training complete → Cleaning up logits")
    set_state("cleanup_logits", "running")
    
    import shutil
    batch3_logits = Path("/data/SpecForge/custom_dflash/batch_3_logits")
    if batch3_logits.exists():
        log(f"Deleting {batch3_logits}")
        shutil.rmtree(batch3_logits)
    
    # Also clean up old checkpoints to save space
    for batch_dir in ["FrankenV8-Batch1", "FrankenV8-Batch2"]:
        checkpoint_dir = Path(f"/data/models/{batch_dir}")
        if checkpoint_dir.exists():
            for ckpt in checkpoint_dir.glob("checkpoint-*.pt"):
                log(f"Deleting old checkpoint: {ckpt}")
                ckpt.unlink()
    
    set_state("cleanup_logits", "completed")
    log("Cleanup complete. Retained: hidden_states_full + FrankenV8-Final + Qwen3.6-27B")

def check_ssd_ready():
    """Check if 8TB SSD is mounted."""
    return (Path("/mnt/8tb") / ".mounted").exists() or os.path.ismount("/mnt/8tb")

def trigger_qwen_scope_migration():
    """Move Qwen-Scope SAE files from Mac to Spark, finish compilation."""
    log("PHASE TRANSITION: Starting Qwen-Scope SAE migration")
    set_state("qwen_scope_migration", "running")
    
    # This will be triggered after SSD arrives Friday
    # For now, set up the transfer script
    transfer_script = FRANKEN_DIR / "scripts" / "migrate_qwen_scope.sh"
    if transfer_script.exists():
        subprocess.Popen(
            ["bash", str(transfer_script)],
            stdout=open(FRANKEN_DIR / "logs" / "qwen_scope_migration.log", "a"),
            stderr=subprocess.STDOUT,
            start_new_session=True
        )

def check_migration_complete():
    """Check if all 64 SAE files are on Spark."""
    if not QWEN_SCOPE_SPARK.exists():
        return False
    sae_files = list(QWEN_SCOPE_SPARK.glob("*.sae"))
    return len(sae_files) >= 64

def trigger_qwen_scope_integration():
    """Integrate SAEs into Qwen 3.6 27B."""
    log("PHASE TRANSITION: Qwen-Scope migration complete → Integrating into Qwen 3.6 27B")
    set_state("qwen_scope_integration", "running")
    
    script = FRANKEN_DIR / "scripts" / "integrate_qwen_scope.py"
    if script.exists():
        subprocess.Popen(
            [sys.executable, str(script),
             "--model", "/mnt/8tb/models/qwen-3.6-27b-uncensored",
             "--sae_dir", str(QWEN_SCOPE_SPARK)],
            cwd=str(FRANKEN_DIR),
            stdout=open(FRANKEN_DIR / "logs" / "qwen_scope_integration.log", "a"),
            stderr=subprocess.STDOUT,
            start_new_session=True
        )

def check_integration_verified():
    """Check if integration verification passed."""
    marker = FRANKEN_DIR / "integration_verified.marker"
    return marker.exists()

def trigger_final_training():
    """Train Qwen 3.6 27B (with ModelScope) on Franken V8 draft."""
    log("PHASE TRANSITION: Integration verified → Starting final training")
    set_state("final_training", "running")
    
    script = FRANKEN_DIR / "scripts" / "train_final_model.py"
    if script.exists():
        subprocess.Popen(
            [sys.executable, str(script),
             "--base_model", "/mnt/8tb/models/qwen-3.6-27b-uncensored",
             "--draft_model", str(FRANKEN_DIR / "franken_v8" / "final_model.pt"),
             "--output", "/mnt/8tb/models/qwen-3.6-27b-franken-v8"],
            cwd=str(FRANKEN_DIR),
            stdout=open(FRANKEN_DIR / "logs" / "final_training.log", "a"),
            stderr=subprocess.STDOUT,
            start_new_session=True
        )

def run_pipeline_check():
    """Main pipeline state machine."""
    init_db()
    
    # Determine current phase
    current_phase = None
    for phase in PHASES:
        status, _ = get_state(phase)
        if status in ("running", "pending"):
            current_phase = phase
            break
        if status == "completed":
            continue
    
    if not current_phase:
        log("All phases complete!")
        return
    
    log(f"Current phase: {current_phase} - {PHASES[current_phase]['desc']}")
    
    # Phase-specific checks and transitions
    # Batch 1 already complete — skip to batch 3
    set_state("batch1_training", "completed")
    set_state("batch2_training", "completed")
    
    if current_phase in ["batch1_training", "batch2_training", "batch3_extraction", "cleanup_logits"]:
        # Check if batch 3 extraction is running or done
        if check_batch3_extraction_complete():
            set_state("batch3_extraction", "completed")
            if not check_batch3_training_complete():
                trigger_batch3_training()
        else:
            log("Batch 3 extraction in progress...")
    
    elif current_phase == "batch3_training":
        if check_batch3_training_complete():
            set_state("batch3_training", "completed")
            trigger_cleanup()
    
    elif current_phase == "cleanup_logits":
        # Cleanup is synchronous, should already be done
        if check_ssd_ready():
            set_state("cleanup_logits", "completed")
            trigger_qwen_scope_migration()
        else:
            log("Waiting for 8TB SSD to arrive Friday...")
    
    elif current_phase == "qwen_scope_migration":
        if check_migration_complete():
            set_state("qwen_scope_migration", "completed")
            trigger_qwen_scope_integration()
    
    elif current_phase == "qwen_scope_integration":
        if check_integration_verified():
            set_state("qwen_scope_integration", "completed")
            set_state("verify_integration", "completed")
            trigger_final_training()
    
    elif current_phase == "verify_integration":
        # Handled in integration phase
        pass
    
    elif current_phase == "final_training":
        # Monitor final training
        final_model = Path("/data/models/qwen-3.6-27b-franken-v8/final_model.pt")
        if final_model.exists():
            set_state("final_training", "completed")
            log("PIPELINE COMPLETE: Final model trained and saved")

if __name__ == "__main__":
    run_pipeline_check()
