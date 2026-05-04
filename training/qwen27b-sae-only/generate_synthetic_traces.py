#!/usr/bin/env python3
"""
Synthetic Reasoning Trace Generator — Franken V8
Generates high-quality reasoning traces to augment SlimOrca + OpenHermes.

Uses the critical prompt structure from reasoning-distillation-lora skill:
- <|begin of thought|> ... <|end of thought|>
- <|begin of solution|> ... <|end of solution|>

Domains: Math, Code, Logic Puzzles, Tool Use, Multi-step Reasoning
"""

import os
import sys
import json
import random
import argparse
from pathlib import Path
from typing import List, Dict

# Reasoning prompt template (from research)
REASONING_PROMPT = """Your role as an assistant involves thoroughly exploring questions through a systematic long thinking process before providing the final precise and accurate solutions. This requires engaging in a comprehensive cycle of analysis, summarizing, exploration, reassessment, reflection, backtracking, and iteration to develop a well-considered thinking process.

Please structure your response into two main sections: Thought and Solution.

In the Thought section, detail your reasoning process using the specified format: <|begin of thought|> thought with steps separated with \n\n <|end of thought|> Each step should include detailed considerations such as analyzing questions, summarizing relevant findings, brainstorming new ideas, verifying the accuracy of the current steps, refining any errors, and revisiting previous steps.

In the Solution section, based on various attempts, explorations, and reflections from the Thought section, systematically present the final solution that you deem correct. <|begin of solution|> final formatted, precise, and clear solution <|end of solution|>"""


# ============================================================
# PROBLEM GENERATORS
# ============================================================

class ProblemGenerator:
    """Generates diverse reasoning problems across domains."""
    
    def __init__(self, seed=42):
        random.seed(seed)
        
    def generate_math_problem(self, difficulty=1):
        """Generate a math reasoning problem."""
        templates = [
            {
                "problem": "Find all integer solutions to the equation {a}x² + {b}x + {c} = 0.",
                "params": lambda: {"a": random.randint(1, 10), "b": random.randint(-20, 20), "c": random.randint(-50, 50)}
            },
            {
                "problem": "A train travels {speed} km/h. How far does it travel in {time} hours if it makes {stops} stops of {stop_time} minutes each?",
                "params": lambda: {"speed": random.randint(60, 120), "time": random.randint(2, 8), "stops": random.randint(1, 5), "stop_time": random.randint(5, 20)}
            },
            {
                "problem": "Prove that for any positive integer n, the sum 1 + 2 + ... + n equals n(n+1)/2 using mathematical induction.",
                "params": lambda: {}
            },
            {
                "problem": "Solve the system of equations: {a}x + {b}y = {c} and {d}x + {e}y = {f}",
                "params": lambda: {
                    "a": random.randint(1, 5), "b": random.randint(1, 5), "c": random.randint(10, 30),
                    "d": random.randint(1, 5), "e": random.randint(1, 5), "f": random.randint(10, 30)
                }
            },
            {
                "problem": "What is the probability of rolling a sum of {target} with two fair dice?",
                "params": lambda: {"target": random.randint(2, 12)}
            }
        ]
        template = random.choice(templates)
        params = template["params"]()
        problem = template["problem"].format(**params)
        return problem
    
    def generate_code_problem(self, difficulty=1):
        """Generate a code reasoning problem."""
        templates = [
            {
                "problem": "Write a function that finds the longest palindromic substring in a given string. Analyze the time and space complexity.",
                "params": lambda: {}
            },
            {
                "problem": "Implement a binary search tree with insert, delete, and search operations. Explain the balancing strategy.",
                "params": lambda: {}
            },
            {
                "problem": "Given an array of {n} integers, find the maximum sum of any contiguous subarray. Provide both brute force and optimized solutions.",
                "params": lambda: {"n": random.randint(10, 1000)}
            },
            {
                "problem": "Design a rate limiter that allows {requests} requests per {window} seconds. Explain your design choices.",
                "params": lambda: {"requests": random.randint(10, 1000), "window": random.choice([1, 60, 3600])}
            },
            {
                "problem": "Write a function to detect if a linked list has a cycle. Use O(1) space if possible.",
                "params": lambda: {}
            }
        ]
        template = random.choice(templates)
        params = template["params"]()
        problem = template["problem"].format(**params)
        return problem
    
    def generate_logic_problem(self, difficulty=1):
        """Generate a logic reasoning problem."""
        templates = [
            {
                "problem": "Three people — Alice, Bob, and Charlie — are wearing hats. They know there are {red} red hats and {blue} blue hats total. Alice sees Bob and Charlie's hats. Bob sees Alice and Charlie's hats. Charlie sees no hats. Alice says 'I don't know my hat color.' Bob says 'I don't know either.' What color is Charlie's hat?",
                "params": lambda: {"red": random.randint(2, 3), "blue": random.randint(0, 1)}
            },
            {
                "problem": "A farmer needs to transport a fox, a chicken, and grain across a river. The boat can only carry the farmer and one item. If left alone, the fox eats the chicken, and the chicken eats the grain. How does the farmer get everything across safely?",
                "params": lambda: {}
            },
            {
                "problem": "You have {coins} coins, one of which is counterfeit (lighter). Using a balance scale, what is the minimum number of weighings needed to guarantee finding the counterfeit coin?",
                "params": lambda: {"coins": random.choice([9, 12, 27])}
            },
            {
                "problem": "In a room of {people} people, what is the probability that at least two share the same birthday? Calculate and explain.",
                "params": lambda: {"people": random.randint(20, 50)}
            }
        ]
        template = random.choice(templates)
        params = template["params"]()
        problem = template["problem"].format(**params)
        return problem
    
    def generate_tool_problem(self, difficulty=1):
        """Generate a tool-use reasoning problem."""
        templates = [
            {
                "problem": "I need to book a flight from {origin} to {destination} on {date}. The flight should depart between {start_time} and {end_time}. Find the cheapest option with at most 1 stop. What tools would you use and what are the steps?",
                "params": lambda: {
                    "origin": random.choice(["NYC", "LAX", "ORD", "LHR", "CDG"]),
                    "destination": random.choice(["NYC", "LAX", "ORD", "LHR", "CDG"]),
                    "date": "2026-06-15",
                    "start_time": "08:00",
                    "end_time": "20:00"
                }
            },
            {
                "problem": "Calculate the compound interest on ${principal} invested at {rate}% annual interest, compounded monthly, for {years} years. Show the formula and step-by-step calculation.",
                "params": lambda: {
                    "principal": random.randint(1000, 100000),
                    "rate": random.randint(3, 8),
                    "years": random.randint(5, 30)
                }
            },
            {
                "problem": "I have a CSV file with columns: name, age, city, salary. I want to find the average salary by city for people over 30. Write the Python code using pandas and explain each step.",
                "params": lambda: {}
            }
        ]
        template = random.choice(templates)
        params = template["params"]()
        problem = template["problem"].format(**params)
        return problem
    
    def generate(self, domain=None, difficulty=1):
        """Generate a problem from specified domain or random."""
        if domain is None:
            domain = random.choice(["math", "code", "logic", "tool"])
        
        generators = {
            "math": self.generate_math_problem,
            "code": self.generate_code_problem,
            "logic": self.generate_logic_problem,
            "tool": self.generate_tool_problem,
        }
        
        return generators[domain](difficulty)


# ============================================================
# FRANKEN V8 INTERFACE
# ============================================================

class FrankenV8Interface:
    """
    Interface to Franken V8 for generating reasoning traces.
    
    In production, this would load the actual Franken V8 model.
    For now, provides the structure for integration.
    """
    
    def __init__(self, model_path="/data/models/FrankenV8-Final/final_model.pt"):
        self.model_path = model_path
        self.model = None
        
    def load(self):
        """Load Franken V8 model."""
        if not os.path.exists(self.model_path):
            print(f"Warning: Franken V8 not found at {self.model_path}")
            return False
        
        # Would load actual model here
        # For now, mark as loaded
        self.model = True
        return True
    
    def generate_trace(self, problem, max_length=2048):
        """
        Generate a reasoning trace for the given problem.
        
        Returns dict with:
        - problem: the input problem
        - thought: the reasoning process
        - solution: the final answer
        - full_response: complete formatted response
        """
        if self.model is None:
            self.load()
        
        # In production: actual model inference
        # For now, return structured placeholder
        
        prompt = f"{REASONING_PROMPT}\n\nProblem: {problem}\n\n"
        
        # Placeholder — would be replaced with actual model output
        thought = f"<|begin of thought|>\nLet me analyze this problem step by step.\n\nFirst, I need to understand what is being asked...\n\n[Detailed reasoning would go here]\n\n<|end of thought|>"
        
        solution = f"<|begin of solution|>\n[Final answer would go here]\n<|end of solution|>"
        
        full_response = f"{thought}\n\n{solution}"
        
        return {
            "problem": problem,
            "thought": thought,
            "solution": solution,
            "full_response": full_response,
            "prompt": prompt,
        }


# ============================================================
# DATASET GENERATOR
# ============================================================

class SyntheticDatasetGenerator:
    """Generates synthetic reasoning traces and saves to JSONL."""
    
    def __init__(self, output_dir, num_samples=10000):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.num_samples = num_samples
        self.problem_gen = ProblemGenerator()
        self.model = FrankenV8Interface()
        
    def generate(self, domain_mix=None):
        """
        Generate synthetic dataset.
        
        Args:
            domain_mix: Dict of {domain: ratio} or None for default
        """
        if domain_mix is None:
            domain_mix = {
                "math": 0.30,
                "code": 0.25,
                "logic": 0.25,
                "tool": 0.20,
            }
        
        output_file = self.output_dir / "synthetic_reasoning_traces.jsonl"
        
        print(f"Generating {self.num_samples} synthetic reasoning traces...")
        print(f"Domain mix: {domain_mix}")
        
        with open(output_file, 'w') as f:
            for i in range(self.num_samples):
                # Select domain
                r = random.random()
                cumulative = 0
                domain = "math"
                for d, ratio in domain_mix.items():
                    cumulative += ratio
                    if r <= cumulative:
                        domain = d
                        break
                
                # Generate problem
                difficulty = min(3, 1 + i // (self.num_samples // 3))
                problem = self.problem_gen.generate(domain, difficulty)
                
                # Generate trace (placeholder — would use actual model)
                trace = self.model.generate_trace(problem)
                
                # Format as conversation
                conversation = {
                    "conversations": [
                        {"from": "system", "value": REASONING_PROMPT},
                        {"from": "human", "value": problem},
                        {"from": "gpt", "value": trace["full_response"]}
                    ],
                    "domain": domain,
                    "difficulty": difficulty,
                    "synthetic": True,
                    "model": "franken_v8",
                }
                
                f.write(json.dumps(conversation) + "\n")
                
                if (i + 1) % 100 == 0:
                    print(f"  Generated {i + 1}/{self.num_samples} traces")
        
        print(f"Dataset saved to: {output_file}")
        print(f"Total samples: {self.num_samples}")
        
        # Print statistics
        self._print_stats(output_file)
        
    def _print_stats(self, file_path):
        """Print dataset statistics."""
        domains = {}
        total_tokens = 0
        
        with open(file_path, 'r') as f:
            for line in f:
                data = json.loads(line)
                domain = data.get("domain", "unknown")
                domains[domain] = domains.get(domain, 0) + 1
                
                # Approximate token count
                text = " ".join([t.get("value", "") for t in data.get("conversations", [])])
                total_tokens += len(text.split())
        
        print("\nDataset Statistics:")
        print(f"  Total samples: {sum(domains.values())}")
        print(f"  Approximate tokens: {total_tokens:,}")
        print(f"  Domain distribution:")
        for domain, count in sorted(domains.items()):
            pct = count / sum(domains.values()) * 100
            print(f"    {domain}: {count} ({pct:.1f}%)")


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic reasoning traces from Franken V8")
    parser.add_argument("--num-samples", type=int, default=10000, help="Number of traces to generate")
    parser.add_argument("--output-dir", type=str, default="/data/datasets/synthetic_reasoning/")
    parser.add_argument("--domain-mix", type=str, default=None, help="JSON string of domain ratios")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    
    random.seed(args.seed)
    
    domain_mix = None
    if args.domain_mix:
        domain_mix = json.loads(args.domain_mix)
    
    generator = SyntheticDatasetGenerator(args.output_dir, args.num_samples)
    generator.generate(domain_mix)


if __name__ == "__main__":
    main()
