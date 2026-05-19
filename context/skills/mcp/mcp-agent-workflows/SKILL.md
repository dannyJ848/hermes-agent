---
name: mcp-agent-workflows
version: 1.0
description: Build effective AI agents using Model Context Protocol with composable workflow patterns. Orchestrator, router, map-reduce, evaluator-optimizer. Based on lastmile-ai/mcp-agent (8.2k stars).
trigger: When designing multi-step agent workflows, orchestrating MCP tool calls, or building agent pipelines.
---

# MCP-Agent Workflow Patterns

## Overview
Composable workflow patterns for building agents that use Model Context Protocol servers. Based on the lastmile-ai/mcp-agent library (8,200+ GitHub stars).

## Installation
```bash
pip install mcp-agent
```

## Workflow Patterns

### 1. Orchestrator Pattern
Central agent delegates subtasks to specialized workers:
```python
from mcp_agent.workflows import Orchestrator

orchestrator = Orchestrator(
    mcp_servers=["biomcp", "fhir-mcp"],
    model="gpt-4"
)
result = await orchestrator.run("Analyze this patient's lab results")
```

### 2. Router Pattern
Routes queries to the right handler (useful for EN/ES bilingual):
```python
from mcp_agent.workflows import Router

router = Router(
    routes={
        "medical_query": biomcp_handler,
        "fhir_data": fhir_handler,
        "anatomy_3d": anatomy_handler
    }
)
```

### 3. Map-Reduce Pattern
Process multiple items in parallel:
```python
from mcp_agent.workflows import MapReduce

pipeline = MapReduce(
    mapper=process_patient_record,
    reducer=aggregate_findings,
    mcp_servers=["fhir-mcp"]
)
```

### 4. Evaluator-Optimizer Pattern
Generate → Evaluate → Refine loop:
```python
from mcp_agent.workflows import EvaluatorOptimizer

eo = EvaluatorOptimizer(
    generator=generate_medical_content,
    evaluator=check_medical_accuracy,
    max_iterations=3
)
```

## SOMA Use Cases
1. **Bilingual content pipeline**: Router sends EN queries to one path, ES to another
2. **Medical QA**: Orchestrator coordinates BioMCP + FHIR + anatomy viewer
3. **Content quality**: Evaluator-optimizer ensures medical accuracy before display
4. **Batch processing**: Map-reduce for generating encyclopedia entries in bulk

## Pitfalls
- MCP server connections can timeout — always set timeouts
- Orchestrator adds latency — use Router for simple cases
- Not all MCP servers support concurrent connections
- Needs Python 3.10+

## Links
- GitHub: https://github.com/lastmile-ai/mcp-agent
- Docs: https://github.com/lastmile-ai/mcp-agent/tree/main/docs
