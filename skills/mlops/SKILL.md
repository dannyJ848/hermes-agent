---
name: mlops
version: 2.0
description: MLOps skills — umbrella covering model training, inference, deployment, evaluation, and optimization. Includes large model training, speculative decoding, medical VLMs, TTS, music generation, and GPU cloud platforms.
trigger: When training, fine-tuning, deploying, or optimizing ML/AI models, or when working with GPUs, inference servers, or model serving infrastructure.
---

# MLOps Skills

## Model Training

### Large Model Training on Constrained GPU

Train 20B+ parameter models on single GPU with limited VRAM (80-130GB).

**Impossibility Matrix:**

| Model Size | bf16 Weights | bf16 Grads | AdamW States (fp32) | Min GPU Needed | Viable on 130GB? |
|-----------|-------------|-----------|--------------------|---------------|-----------------|
| 7B | 14GB | 14GB | 28GB | 56GB | ✅ Yes |
| 13B | 26GB | 26GB | 52GB | 104GB | ✅ Barely |
| 20B | 40GB | 40GB | 80GB | 160GB | ❌ No |
| 27B | 54GB | 54GB | 108GB | 216GB | ❌ No |
| 70B | 140GB | 140GB | 280GB | 560GB | ❌ No |

**Formula:** `Minimum GPU = 2 * model_size_GB (weights + grads) + 3 * model_size_GB (AdamW states)`

**SGD-only workaround:** SGD lr=1e-5 on 27B produces gradients too small to meaningfully update weights. Loss decreases ~40% over 1000 steps but perplexity shows NO improvement. Not actually learning.

### Large Model Full Fine-Tuning

Full parameter fine-tuning of 20B+ models on 100-150GB VRAM. Verified working config for Qwen 27B on 130GB GPU. Memory-optimized loading, gradient checkpointing, teacher distillation workarounds.

**CRITICAL:** SGD produces flat losses — no actual learning. Use AdamW with 8-bit quantization or DeepSpeed ZeRO-Infinity if possible.

### Large Model + Modular Component Integration

Integrate SAEs, adapters, LoRA into base models exceeding GPU memory. **Wave-loading pattern:**

| Component | Memory | Notes |
|-----------|--------|-------|
| Base model (bf16) | ~55GB | Fixed, always loaded |
| Per modular component | ~1.8GB | e.g., one SAE layer |
| Wave size (8 components) | ~14GB | Active subset |

Load only a wave (subset) at a time. Process, evict, load next wave.

### Iterative Batch Training Disk Management

Manage disk space during iterative batch training on storage-constrained systems (e.g., 3.7TB NVMe).

**Triple-Batch Pipeline:**
1. Generate target logits / hidden states
2. Train model on that batch
3. Save final checkpoint
4. Delete batch's intermediate artifacts
5. Repeat for next batch

Peak disk usage: ~1 batch + 1 model + overhead instead of N batches.

### Post-Training Dataset Archival

After training completes, datasets are **for archive only**:
- Retraining on identical data → overfitting, no new learning
- Continued training on same data → catastrophic forgetting
- Keep on external SSD (exFAT for cross-platform compatibility)
- Free up local disk — 300GB+ of training data on laptop SSD is wasteful
- Only reload to DGX when starting a NEW training run

### Qwen 27B Expert Logician Training Pipeline

Maximum-quality LoRA + SAE + teacher distillation pipeline for Qwen 27B on DGX Spark (130GB GPU).

**LoRA Rank:** Any positive integer — not just powers of 2. Memory savings scale linearly with rank. User prefers "turn everything on" over maximizing rank. Drop rank incrementally (1024→768→640→512) until all features (SAE, teacher distillation, optimizer state) can run simultaneously.

**User preference:** Aggressive stability over marginal fixes. When training is "on the edge of stable" (GPU memory >90%), apply ALL available stability fixes simultaneously, not sequentially.

### Franken V8 Training Pipeline

3-batch progressive training on DGX Spark. Extract logits from hidden states → train 25-graft model → delete logits → next batch. Final: train Qwen3.6-27B on FrankenV8 draft.

- **Model:** 8.1B params, 248320 vocab, 25 grafts
- **Hardware:** DGX Spark, NVIDIA GB10, 121GB RAM, CUDA 13.0
- **Pipeline:** Batch 2 (0-3332) → Batch 1 (3333-6665) → Batch 3 (6666-9999)

### EAGLE-3 Draft Model Training

Train custom EAGLE-3 speculative decoding draft model when SpecForge's SGLang backend is incompatible.

- Use `transformers>=5.x` for recent architectures (SpecForge pins 4.57.1 but works with 5.x)
- UltraChat/ShareGPT dataset in `.jsonl` format
- Custom HF-based hidden state generation when SGLang fails

### OPSD (On-Policy Self-Distillation) Training

Train single model as both student and teacher by conditioning on different contexts. More sample-efficient than GRPO. No separate reward model needed.

**Why OPSD over GRPO/DPO:** Higher accuracy with fewer generated tokens. Single model architecture. Effective for reasoning tasks (math, coding, clinical reasoning).

**Paper:** [Self-Distilled Reasoner](https://arxiv.org/pdf/2601.18734v3) — Siyan Zhao et al.

### Reasoning Distillation LoRA

Improve LLM reasoning via LoRA fine-tuning on distilled chain-of-thought data. Post-training alignment for reasoning capabilities.

## Sparse Autoencoders (SAE)

### Qwen-Scope SAE Integration

Insert SAEs into Qwen's hidden layers to guide training by monitoring and shaping internal activations.

**SAE Structure (per layer):**
- Input: 5120-dim hidden states (d_model)
- Latent: 81920-dim sparse features (d_sae = 16x expansion)
- TopK: 50 (exactly 50 non-zero features per token)
- Layers: 0-63 (64 SAE files for Qwen3.5-27B)

**Files:** `/data/models/Qwen-Scope/` (64 files, 201GB total)

### SAE Model Integration

Integrate Sparse Autoencoders into transformer training pipelines. Covers Qwen-Scope, Franken architectures, and student-teacher training with SAE modules.

**Correct architecture:** Qwen as trainable student, Franken as frozen teacher. NOT the reverse.

## Speculative Decoding

### Franken Custom Speculative Decoding

When vLLM/native frameworks don't support your model architecture, build custom model classes that ARE compatible.

**Philosophy:** Never accept "doesn't work." Build a version that DOES work.
- "EAGLE-3 not supported for Qwen3_5ForCausalLM" → Build custom EAGLE-3 model class
- "DFlash dimensions don't match" → Build dimension adapter
- "MTP deadlocks on GB10" → Build custom draft model

## CUDA / GPU Fixes

### FlashKDA Blackwell Debug

Test FlashKDA (or any custom CUDA attention kernel) on NVIDIA Blackwell/GB10.

**SM121a Discovery:** The 'a' suffix is mandatory for TMA enablement:
- `sm_121` → DISABLED → `Assertion: Trying to use tma without CUTE_ARCH_TMA_SM90_ENABLED`
- `sm_121a` → ENABLED → **WORKS**
- `sm_120a` → `cudaErrorNoKernelImageForDevice` — wrong architecture

```python
# In setup.py, add ONLY sm_121a:
arch_flags.extend(["-gencode", "arch=compute_121a,code=sm_121a"])
```

**Numerical validation:** Do not expect exact `torch.equal` between kernel output and PyTorch reference. Use `allclose` with `rtol=0.01, atol=0.01` for bfloat16.

### Triton Blackwell SM121a Fix

Fix Triton kernel compilation failures on NVIDIA Blackwell SM121a GPUs where ptxas 12.8 does not recognize `sm_121a`.

**Error:** `ptxas fatal : Value 'sm_121a' is not defined for option 'gpu-name'`

**Fix:** Patch Triton's `triton/backends/nvidia/compiler.py` to map `sm_121a` → `sm_120a` for ptxas while keeping `sm_121a` for CUDA runtime.

## Model Config Compatibility

Safe attribute extraction and dtype handling for HuggingFace model configs that deviate from standard attributes.

```python
# Always use getattr with fallback chains:
hidden_size = getattr(config, 'hidden_size',
              getattr(config, 'd_model',
              getattr(config, 'n_embd', 4096)))

num_heads = getattr(config, 'num_attention_heads',
          getattr(config, 'num_heads',
          getattr(config, 'n_head', 64)))
```

## HuggingFace Hub

### HF CLI (`hf` — replaces deprecated `huggingface-cli`)

- Install: `curl -LsSf https://hf.co/cli/install.sh | bash -s`
- Download: `hf download REPO_ID`
- Upload: `hf upload REPO_ID` / `hf upload-large-folder REPO_ID LOCAL_PATH`
- Auth: `HF_TOKEN` environment variable or `--token` flag

### Gated Repo Access

Gated repos require browser form acceptance BEFORE CLI/API download works. CSRF tokens rendered client-side by Svelte — cannot be automated.

**Steps:**
1. Open gated repo URL in browser
2. Fill: First Name, Last Name, Country
3. Click "Agree and access repository"
4. CLI download works immediately after

**Token requirements:** Fine-grained tokens MUST have "Read access to contents of all public gated repos you can access" checkbox enabled.

## Medical Vision-Language Models

### M3D-LaMed

Multi-modal LLM for 3D medical image analysis (segmentation, VQA, report generation, grounding). By BAAI-DCAI. 428 stars.

### MedGemma 1.5

Google's open multimodal LLM for medical image interpretation and bilingual medical text comprehension. Radiology report drafting, medical Q&A, clinical data extraction.

### Merlin (Stanford MIMI)

3D VLM for CT scans. Published in **Nature 2026**. Combines EHR + radiology reports for pretraining. 353 stars. MIT license. Python package: `merlin-vlm`.

### MONAI Medical Imaging

PyTorch-based framework for healthcare-imaging deep learning. Built by NVIDIA/King's College London. Full pipeline: DICOM loading → preprocessing → training → inference → visualization.

**Components:** MONAI Core (transforms, networks, losses), MONAI Bundle (pretrained model zoo), MONAI Label (active learning annotation), MONAI Deploy (production inference packaging).

## Audio / Speech / Music

### ACE-Step 1.5

Open-source music generation foundation model rivaling commercial tools (Suno, Udio). 8500+ stars. Apache-2.0.

- Text-to-music, lyrics-to-song, audio editing, style transfer
- LoRA fine-tuning for custom styles
- Multi-platform: CUDA, Apple Silicon MPS, AMD ROCm, Intel

### Chatterbox TTS

Resemble AI's state-of-the-art open-source TTS family. 24K+ stars. MIT license.

| Model | Params | Speed | Use Case |
|-------|--------|-------|----------|
| Chatterbox (full) | ~1B | Standard | Highest quality, voice cloning |
| Chatterbox-Turbo | 350M | Fast | Low-latency, production |
| Chatterbox-Multilingual | - | Standard | Multi-language (ES support) |

**Why it matters:** Bilingual EN/ES, in-browser via Transformers.js v4, voice cloning, outperforms ElevenLabs in blind tests.

### IndexTTS2

Industrial-level zero-shot TTS with emotional control and duration precision. 19.8K stars. Disentangles emotion from speaker identity. Bilingual EN/ES. Best for: expressive medical narration, bilingual audio, video dubbing with AV sync.

### Whisper STT/TTS

Bilingual (EN/ES) speech recognition and synthesis using Whisper + TTS pipeline.

## Vector Databases

### pgvector Embedding Population

Batch-encode text from PostgreSQL tables into pgvector embedding columns using sentence-transformers.

```python
import psycopg2
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-small-en-v1.5')
# Batch UPDATE pattern with embedding IS NULL filter
```

## Health Simulation Model Training

Train a model that connects ecological factors (zip code, weather, terrain, policy) through macro medical-political-economic systems to concrete micro-level disease outcomes.

**Core principle:** Every reasoning chain MUST terminate in a concrete medical outcome:
`ECOLOGICAL INPUT → MACRO SYSTEMS → MICRO PATHOPHYSIOLOGY → DISEASE/CONDITION`

Example: Zip 90210 vs 90220 → income disparity $85K vs $34K → grocery access differential → dietary pattern shift (low folate, high sodium) → 3-year trajectory → homocysteine elevation → endothelial dysfunction → hypertension onset at age 42 → BP 158/96, LVH on ECG, ACE inhibitor indicated, 10-year ASCVD risk 14.2%

## GPU Cloud Platforms

### Lambda Labs GPU Cloud

Reserved and on-demand GPU cloud instances for ML training. Lambda Labs provides high-performance GPU instances with NVIDIA A100, H100, and other accelerators.

### Modal Serverless GPU

Serverless GPU cloud platform for running ML workloads. Deploy functions that run on GPU without managing infrastructure. Scale from zero to thousands of GPUs.

## Pitfalls

- **SGD on large models:** SGD lr=1e-5 on 27B parameters produces gradients too small to meaningfully update weights. Loss decreases but perplexity shows NO improvement. Use AdamW with 8-bit quantization.
- **Memory budgeting:** Always calculate minimum GPU before starting. The impossibility matrix above is accurate.
- **Wave loading:** Never quantize base model to 4-bit for training compatibility. Use wave loading instead.
- **SM121a:** The 'a' suffix is mandatory for TMA on Blackwell. `sm_121` without 'a' fails.
- **Triton on Blackwell:** ptxas 12.8 doesn't recognize `sm_121a`. Patch Triton compiler to map to `sm_120a` for ptxas.
- **Gated repos:** Browser form acceptance is mandatory. Cannot be automated. Ask user to do it manually.
- **HF CLI:** Use `hf` command, not deprecated `huggingface-cli`.
- **Disk management:** Never hold more than one batch of intermediate artifacts on disk at a time. Delete after training each batch.
- **SAE integration:** Correct architecture is Qwen as trainable student, Franken as frozen teacher. NOT the reverse.
