#!/usr/bin/env python3
"""
Direct Qwen 27B Evaluation — loads model and runs reasoning test prompts
Copy and modify test cases for your evaluation needs.
"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
from pathlib import Path

MODEL_PATH = "/data/SpecForge/custom_dflash/checkpoints/final_model_merged"
OUTPUT_DIR = "/data/SpecForge/custom_dflash/evaluation_results"

def main():
    print("=" * 60)
    print("QWEN 27B DIRECT EVALUATION")
    print("=" * 60)
    
    # Load tokenizer
    print("\n[1/4] Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    print("Tokenizer loaded")
    
    # Load model
    print("\n[2/4] Loading model (this may take 10-15 minutes)...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )
    print(f"Model loaded: {sum(p.numel() for p in model.parameters()) / 1e9:.1f}B parameters")
    print(f"Device: {next(model.parameters()).device}")
    
    # Test prompts — modify these for your evaluation
    tests = [
        {
            "name": "wason_drinking_age",
            "category": "deductive_reasoning",
            "prompt": "Four cards show: Beer, Coke, 25 years, 16 years. Rule: 'If drinking beer, then over 18'. Which cards must you flip to verify the rule? Answer with just the card names.",
            "expected": ["Beer", "16 years"]  # keyword matching
        },
        {
            "name": "syllogism_barbara",
            "category": "classical_logic",
            "prompt": "All men are mortal. Socrates is a man. Therefore Socrates is mortal. Is this syllogism valid? Answer Valid or Invalid.",
            "expected": "Valid"
        },
        {
            "name": "math_proof",
            "category": "mathematical_reasoning",
            "prompt": "Prove that sqrt(2) is irrational. Use proof by contradiction.",
            "expected": ["contradiction", "rational", "p/q", "even"]
        },
        {
            "name": "counterfactual",
            "category": "modal_reasoning",
            "prompt": "If Socrates were immortal, would the syllogism 'All men are mortal, Socrates is a man, therefore Socrates is mortal' still hold? Explain.",
            "expected": ["no", "contradiction", "premise"]
        },
        {
            "name": "ambiguous_premise",
            "category": "robustness",
            "prompt": "If it rains, the ground gets wet. The ground is wet. Did it rain? Explain your reasoning.",
            "expected": ["not necessarily", "could be", "other reasons"]
        },
        {
            "name": "edge_case",
            "category": "edge_case",
            "prompt": "Is 0.999... equal to 1? Prove or disprove in one sentence.",
            "expected": ["equal", "1", "limit"]
        }
    ]
    
    # Run tests
    print("\n[3/4] Running reasoning tests...")
    results = []
    for test in tests:
        print(f"\n  Test: {test['name']} ({test['category']})")
        
        # Generate
        inputs = tokenizer(test["prompt"], return_tensors="pt").to(model.device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=200,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        print(f"  Response: {response[:150]}...")
        
        # Check expected keywords
        expected = test["expected"]
        if isinstance(expected, list):
            matches = sum(1 for kw in expected if kw.lower() in response.lower())
            score = matches / len(expected)
        else:
            score = 1.0 if expected.lower() in response.lower() else 0.0
        
        results.append({
            "name": test["name"],
            "category": test["category"],
            "prompt": test["prompt"],
            "response": response,
            "expected": expected,
            "score": score
        })
        print(f"  Score: {score:.1%}")
    
    # Summary
    print("\n[4/4] Generating report...")
    avg_score = sum(r["score"] for r in results) / len(results)
    
    report = {
        "model": MODEL_PATH,
        "average_score": avg_score,
        "tests": results
    }
    
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    with open(f"{OUTPUT_DIR}/direct_evaluation.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Markdown summary
    with open(f"{OUTPUT_DIR}/direct_evaluation.md", "w") as f:
        f.write("# Qwen 27B Expert Logician — Direct Evaluation\n\n")
        f.write(f"**Average Score**: {avg_score:.1%}\n\n")
        f.write("| Test | Category | Score |\n")
        f.write("|------|----------|-------|\n")
        for r in results:
            status = "✅" if r["score"] >= 0.5 else "⚠️" if r["score"] > 0 else "❌"
            f.write(f"| {r['name']} | {r['category']} | {status} {r['score']:.0%} |\n")
        f.write("\n## Detailed Responses\n\n")
        for r in results:
            f.write(f"### {r['name']}\n")
            f.write(f"**Prompt**: {r['prompt']}\n\n")
            f.write(f"**Response**: {r['response']}\n\n")
            f.write(f"**Score**: {r['score']:.1%}\n\n")
    
    print(f"\n{'=' * 60}")
    print(f"EVALUATION COMPLETE — Average Score: {avg_score:.1%}")
    print(f"{'=' * 60}")
    print(f"Results: {OUTPUT_DIR}/direct_evaluation.json")
    print(f"Summary: {OUTPUT_DIR}/direct_evaluation.md")

if __name__ == "__main__":
    main()
