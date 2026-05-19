#!/usr/bin/env python3
"""
Unified Dataset Preprocessor for Reasoning Distillation Training
Standardizes ANY HuggingFace dataset into TRL SFTTrainer-compatible format.

Usage:
  python3 normalize_datasets.py --output-dir ./processed
  python3 normalize_datasets.py --output-dir ./processed --sample  # small samples for testing
"""

import json
import os
import random
import argparse
from pathlib import Path
from datasets import load_dataset, load_from_disk, concatenate_datasets
import glob


# ===== SYSTEM PROMPTS FOR EACH SUB-STAGE =====
SYSTEM_PROMPTS = {
    "reasoning": (
        "You are a transcendent reasoning engine. You excel at:\n"
        "- Multi-step logical deduction and systematic problem-solving\n"
        "- Mathematical proof, calculation, and optimization\n"
        "- Causal inference and counterfactual reasoning\n"
        "- Probabilistic thinking under uncertainty\n"
        "- Code analysis and algorithmic design\n"
        "- Tool use and multi-step agent execution\n\n"
        "Always think step-by-step. Show your reasoning explicitly.\n"
        "Never skip logical steps. Quantify uncertainties when possible."
    ),
    "tooluse": (
        "You are an expert agent capable of using external tools to solve complex problems.\n"
        "When given a task, analyze what tools you need, call them with correct arguments,\n"
        "interpret the results, and continue until the task is complete.\n\n"
        "Rules:\n"
        "1. Think before acting\n"
        "2. Use tools only when necessary\n"
        "3. Pass correct JSON arguments\n"
        "4. Interpret results carefully\n"
        "5. Iterate until the problem is solved"
    ),
    "causal": (
        "You are an expert in causal inference and formal logic.\n"
        "You carefully distinguish correlation from causation.\n"
        "You reason about interventions, counterfactuals, and structural causal models.\n"
        "You identify confounders, mediators, and colliders.\n\n"
        "Always:\n"
        "1. State the assumed causal structure\n"
        "2. Identify what can and cannot be concluded\n"
        "3. Consider alternative explanations\n"
        "4. Quantify uncertainty"
    ),
}


# ===== CASCADE STANDARDIZER =====
def standardize_record(record, system_prompt):
    """Convert any dataset record to unified message format."""

    # 1. messages list
    if "messages" in record and isinstance(record["messages"], list):
        messages = list(record["messages"])
        if messages and messages[0].get("role") != "system":
            messages.insert(0, {"role": "system", "content": system_prompt})
        else:
            messages[0]["content"] = system_prompt
        return {"messages": messages}

    # 2. conversations list
    if "conversations" in record and isinstance(record["conversations"], list):
        messages = list(record["conversations"])
        if messages and messages[0].get("role") != "system":
            messages.insert(0, {"role": "system", "content": system_prompt})
        else:
            messages[0]["content"] = system_prompt
        return {"messages": messages}

    # 3. instruction / output
    if "instruction" in record and "output" in record:
        return {"messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": record["instruction"]},
            {"role": "assistant", "content": record["output"]}
        ]}

    # 4. input / output
    if "input" in record and "output" in record:
        return {"messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": record["input"]},
            {"role": "assistant", "content": record["output"]}
        ]}

    # 5. prompt / completion
    if "prompt" in record and "completion" in record:
        return {"messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": record["prompt"]},
            {"role": "assistant", "content": record["completion"]}
        ]}

    # 6. question / answer
    if "question" in record and "answer" in record:
        return {"messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": record["question"]},
            {"role": "assistant", "content": record["answer"]}
        ]}

    # 7. problem / solution
    if "problem" in record and "solution" in record:
        return {"messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": record["problem"]},
            {"role": "assistant", "content": record["solution"]}
        ]}

    # 8. prompt / generation (code gen)
    if "prompt" in record and "generation" in record:
        return {"messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": record["prompt"]},
            {"role": "assistant", "content": record["generation"]}
        ]}

    # 9. thinking / solution (Claude Opus format)
    if "thinking" in record and "solution" in record:
        assistant_content = record["thinking"] + "\n\n" + record["solution"]
        user_content = record.get("problem", record.get("prompt", ""))
        return {"messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant_content}
        ]}

    return None


# ===== QUALITY FILTER =====
def filter_quality(record, min_chars=50, max_chars=64000):
    messages = record.get("messages", [])
    if not messages:
        return False

    assistant_msgs = [m for m in messages if m.get("role") == "assistant"]
    if not assistant_msgs:
        return False

    total_chars = sum(len(m.get("content", "")) for m in messages)
    if total_chars < min_chars or total_chars > max_chars:
        return False

    # Garbage/refusal detection
    garbage_patterns = [
        "i'm sorry, but i can't",
        "i cannot assist",
        "i'm not able to",
        "as an ai language model",
        "i don't have the ability",
    ]
    content = assistant_msgs[-1].get("content", "").lower()[:200]
    for pattern in garbage_patterns:
        if pattern in content:
            return False

    return True


# ===== DATASET PROCESSING =====
def process_dataset(dataset_path, dataset_name, output_path, system_prompt, max_records=None):
    print(f"\nProcessing {dataset_name}...")
    print(f"  Source: {dataset_path}")

    records = []

    try:
        if os.path.isdir(dataset_path) and os.path.exists(os.path.join(dataset_path, "dataset_info.json")):
            ds = load_from_disk(dataset_path)
        else:
            # Try JSONL first
            jsonl_files = list(Path(dataset_path).glob("*.jsonl")) + list(Path(dataset_path).glob("*.jsonl.zst"))
            if jsonl_files:
                ds = load_dataset("json", data_files=[str(f) for f in jsonl_files], split="train")
            else:
                # Try loading by repo_id
                ds = load_dataset(dataset_path, split="train", trust_remote_code=True)

        for i, record in enumerate(ds):
            if max_records and i >= max_records:
                break

            standardized = standardize_record(record, system_prompt)
            if standardized and filter_quality(standardized):
                records.append(standardized)

            if (i + 1) % 10000 == 0:
                print(f"  Processed {i+1} records, kept {len(records)}")

    except Exception as e:
        print(f"  ERROR loading {dataset_name}: {e}")
        return 0

    random.shuffle(records)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    print(f"  Saved {len(records)} records to {output_path}")
    return len(records)


# ===== MAIN =====
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="./processed")
    parser.add_argument("--sample", action="store_true", help="Process small samples for testing")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # Configure your datasets here: (path, name, system_prompt_key)
    datasets = [
        # Phase 1A: Massive reasoning
        ("./datasets/reasoning-v1-20m", "reasoning-v1-20m", "reasoning"),
        ("./datasets/openmathreasoning", "openmathreasoning", "reasoning"),
        ("./datasets/opencodereasoning", "opencodereasoning", "reasoning"),
        ("./datasets/am-deepseek-r1-distilled", "am-deepseek", "reasoning"),
        ("./datasets/openthoughts2-1m", "openthoughts2", "reasoning"),
        ("./datasets/codeforces-cots", "codeforces-cots", "reasoning"),
        ("./datasets/numinamath-cot", "numinamath-cot", "reasoning"),

        # Phase 1B: Tool use
        ("./datasets/toolmind", "toolmind", "tooluse"),
        ("./datasets/kodcode-v1", "kodcode-v1", "tooluse"),

        # Phase 1C: High-quality refinement
        ("./datasets/s1k", "s1k", "reasoning"),
        ("./datasets/s1k-1.1", "s1k-1.1", "reasoning"),
        ("./datasets/limo", "limo", "reasoning"),
        ("./datasets/curatedthoughts", "curatedthoughts", "reasoning"),
        ("./datasets/claude-opus-4.6-10000x", "claude-opus", "reasoning"),

        # Phase 1D: Causal & logic
        ("./datasets/causal-arcs", "causal-arcs", "causal"),
        ("./datasets/zebralogic", "zebralogic", "causal"),
    ]

    max_records = 5000 if args.sample else None
    total = 0

    for ds_path, ds_name, prompt_key in datasets:
        if not os.path.exists(ds_path):
            print(f"  SKIP {ds_name} (not downloaded yet)")
            continue
        output = f"{args.output_dir}/{ds_name}.jsonl"
        count = process_dataset(ds_path, ds_name, output, SYSTEM_PROMPTS[prompt_key], max_records)
        total += count

    print(f"\n{'='*60}")
    print(f"PREPROCESSING COMPLETE: {total} total records")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
