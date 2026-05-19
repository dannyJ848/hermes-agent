---
name: anthropic-prompting
description: Anthropic's prompting best practices — XML structure, thinking tags, chain-of-thought, and the sandwich pattern. Based on Anthropic Prompting 101 talk.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
prerequisites:
  commands: [python3]
---

# Anthropic Prompting Best Practices

Based on Anthropic's official prompting guide and the "Anthropic Prompting 101" talk.

## Core Principle: Structure = Performance

The way you structure prompts matters more than the specific words you use. Anthropic models (Claude) respond best to clear, structured prompts with explicit sections.

## The XML Sandwich Pattern

```xml
<instructions>
You are a helpful assistant. Follow these rules carefully.
</instructions>

<context>
{{relevant_background_information}}
</context>

<task>
{{what_the_user_wants}}
</task>

<output_format>
{{how_the_response_should_be_structured}}
</output_format>

<example>
{{one_shot_or_few_shot_example}}
</example>
```

## Key Techniques

### 1. Use XML Tags for Structure

Claude pays attention to XML tags. They act as semantic markers:

```xml
<document>
  <title>API Design Guide</title>
  <section>
    <heading>Authentication</heading>
    <content>Use Bearer tokens...</content>
  </section>
</document>
```

### 2. Chain-of-Thought with `<thinking>` Tags

For complex reasoning, ask Claude to think step by step:

```xml
<thinking>
Let me work through this step by step:
1. First, I need to understand...
2. Then, I'll analyze...
3. Finally, I'll conclude...
</thinking>

<answer>
{{final_answer}}
</answer>
```

### 3. Few-Shot Examples in `<examples>`

```xml
<examples>
  <example>
    <input>Convert 100 USD to EUR</input>
    <output>100 USD = 92 EUR (at current exchange rate)</output>
  </example>
  <example>
    <input>Convert 50 GBP to JPY</input>
    <output>50 GBP = 9,500 JPY (at current exchange rate)</output>
  </example>
</examples>
```

### 4. System Prompts for Persona

Use the system field (not user message) for persona and constraints:

```json
{
  "system": "You are an expert Python developer. You write clean, PEP8-compliant code. You always include type hints and docstrings.",
  "messages": [
    {"role": "user", "content": "Write a function to parse JSON"}
  ]
}
```

### 5. Be Explicit About What NOT to Do

```xml
<constraints>
- Do not use external libraries (stdlib only)
- Do not include example usage code
- Do not add comments explaining obvious code
- Maximum 50 lines
</constraints>
```

## The "Thinking" Pattern (Extended Reasoning)

For tasks requiring deep reasoning, use the extended thinking API:

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4000,
    thinking={
        "type": "enabled",
        "budget_tokens": 2000
    },
    messages=[{"role": "user", "content": "Solve this complex problem..."}]
)

# Access thinking content
thinking = response.content[0].thinking
answer = response.content[1].text
```

## Prompt Length Guidelines

- **System prompt**: 100-500 tokens (persona + constraints)
- **Context**: Up to 100K tokens (entire documents)
- **Task description**: 50-200 tokens
- **Examples**: 100-500 tokens each (use sparingly)

## Common Mistakes

1. **Vague instructions** — "Be helpful" vs "List 3 specific action items"
2. **No output format** — Claude guesses format; specify JSON, markdown, etc.
3. **Overloading system prompt** — Keep persona light; put details in context
4. **No examples for edge cases** — Include at least one tricky example
5. **Ignoring the "no"** — Explicitly state what to avoid

## Hermes Integration

When delegating to Claude via `delegate_task`, structure context as Anthropic-style XML:

```python
delegate_task(
    goal="Analyze this codebase",
    model="claude-sonnet-4",
    context="""
<instructions>
You are a code review specialist. Focus on security and performance.
</instructions>

<context>
Project: Python web API using FastAPI
Codebase size: 50 files, 10K lines
</context>

<task>
Review the authentication module for:
1. SQL injection vulnerabilities
2. JWT handling issues
3. Rate limiting gaps
</task>

<output_format>
JSON with findings array. Each finding: severity, file, line, description, fix.
</output_format>
"""
)
```
