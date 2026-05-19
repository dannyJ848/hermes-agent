---
name: agent-native-cli
description: CLI design pattern for AI agent consumption. APIs and MCPs waste tokens — agent-native CLIs are purpose-built for LLM interaction. Based on the Printing Press pattern.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
prerequisites:
  commands: [python3]
---

# Agent-Native CLI Design Pattern

Based on the Printing Press pattern by Matt Van Horn and trevin. Most APIs suck for agents. Most MCPs suck for agents. Most official CLIs suck for agents. They waste tokens and time.

## The Problem

When you ask your AI agent "go check this website for me," it has two bad options:
1. **Use a browser** — click around like a human (slow, burns 10-30x more tokens)
2. **Use an API** — structured but requires understanding docs, auth, rate limits

Both cost more tokens than they should.

## The Solution: Agent-Native CLI

A CLI designed specifically for LLM consumption:
- **Structured output** — JSON by default, not human-readable tables
- **Single-purpose** — One command does one thing, no flags needed
- **Deterministic** — Same input = same output, no surprises
- **Token-efficient** — Minimal output, no decorative formatting
- **Error codes** — Exit codes mean things, stderr has details

## Design Principles

### 1. JSON First

```bash
# Bad: Human-readable table
$ some-cli list-users
NAME    EMAIL           ROLE
Alice   a@example.com   admin
Bob     b@example.com   user

# Good: JSON for agent consumption
$ some-cli list-users --json
[{"name":"Alice","email":"a@example.com","role":"admin"},
 {"name":"Bob","email":"b@example.com","role":"user"}]
```

### 2. One Command, One Action

```bash
# Bad: Multi-mode Swiss army knife
$ some-cli --mode=search --query=foo --format=json --limit=10

# Good: Composable single-purpose commands
$ some-cli search --query foo | some-cli format --json | head -10
```

### 3. Idempotent by Default

Agents run commands multiple times. Make it safe:
```bash
$ some-cli create-user --email a@example.com  # First run: creates
$ some-cli create-user --email a@example.com  # Second run: returns existing (exit 0)
```

### 4. Self-Describing

```bash
$ some-cli --help --json
{
  "commands": [
    {"name": "search", "description": "Search records", "args": ["query"]},
    {"name": "get", "description": "Get record by ID", "args": ["id"]}
  ]
}
```

## Printing Press Implementation

The Printing Press is a CLI factory + library:
- **Library**: Pre-built CLIs for common services (Linear, ESPN, Google Flights, LinkedIn)
- **Factory**: Input `/printing-press <service-name>` to auto-generate a new CLI

### Example: Generated CLI

```bash
$ /printing-press github

# Generates:
$ github search-repos --query "AI agent" --json
$ github get-repo --owner nousresearch --repo hermes-agent --json
$ github list-issues --repo hermes-agent --state open --json
```

## Hermes Integration

When building tools for Hermes Agent:
1. **Output JSON** — `browser_snapshot` already returns structured data
2. **Single action per tool** — `web_search` searches, `web_extract` extracts
3. **Clear error codes** — Tools return structured error dicts
4. **Self-documenting** — Tool schemas describe themselves

## When to Build an Agent-Native CLI

- Service has no API (or API is complex/expensive)
- Agent needs to interact with service frequently
- Browser automation is too slow/token-heavy
- Service has a simple data model (CRUD operations)

## When NOT to Build One

- Official API is already good and well-documented
- Service has complex auth flows (OAuth2 with refresh)
- Rate limits make CLI approach impractical
- Service changes frequently (maintenance burden)

## Examples in the Wild

| CLI | Service | Pattern |
|-----|---------|---------|
| `gh` | GitHub | Official, but verbose |
| `linear` | Linear | API wrapper, JSON output |
| `infsh` | inference.sh | Agent-native by design |
| `xurl` | X/Twitter | Cookie-based, read-only |

## Template for New CLI

```python
#!/usr/bin/env python3
"""Agent-native CLI for {Service}. JSON output, single actions, idempotent."""
import json, sys, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["search", "get", "list"])
    parser.add_argument("--json", action="store_true", default=True)
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--id", help="Record ID")
    args = parser.parse_args()
    
    if args.command == "search":
        results = search(args.query)
        print(json.dumps(results))
    elif args.command == "get":
        result = get(args.id)
        print(json.dumps(result))
    elif args.command == "list":
        results = list_all()
        print(json.dumps(results))

if __name__ == "__main__":
    main()
```
