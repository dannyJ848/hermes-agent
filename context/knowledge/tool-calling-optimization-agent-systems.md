# tool-calling-optimization-agent-systems

*Researched: 2026-04-11 23:34 CDT*

# Tool Calling Optimization for Agent Systems

## Key Findings (Paragon Research, Apr 2025)

### Tool Calling Mechanics
- Tool calling transforms LLMs from QA machines into agents capable of actions
- JSON schema format is standard across OpenAI and Anthropic providers
- Schema components: name, description, parameters — critical for model to decide WHEN to call, WHAT inputs needed, HOW to extract from natural language

### Optimization Levers
1. **Tool descriptions matter more than system prompts** — Changing tool descriptions had larger impact on accuracy than system prompt changes
2. **Fewer tools per decision point** — Models degrade when selecting from >10 tools at once
3. **Clear parameter descriptions** — Each parameter needs explicit description of expected format
4. **Tool naming conventions** — Consistent naming (VERB_NOUN_TARGET) improves selection accuracy

### Architecture Patterns
- **ReAct pattern** (Reason → Act → Observe) remains most reliable for tool chains
- **Parallel tool calling** supported by newer models but increases error surface
- **Circuit breakers** essential for production — stop retrying after 3 failures
- **Observability** — log every tool call with input/output for evaluation

### Evaluation Methodology
- Test with synthetic + real user queries
- Measure: tool selection accuracy, parameter extraction accuracy, end-to-end task success
- Compare across models before deploying

## Relevance to Hermes Agent
- Hermes has 50+ registered tools — should consider tool grouping/contextual filtering
- Tool descriptions in `tools/registry.py` schemas directly impact model selection accuracy
- `toolsets.py` already provides grouping — leverage for context window efficiency
- Weak tool stats (knowledge_search 0%, browser_navigate 0%) suggest description or routing issues

## Sources
- Paragon: Optimizing Tool Calling (useparagon.com)
- Patronus AI: Custom Optimization Tools for LLMs
- Maxim AI: Observability and Evaluation for Tool-Calling Agents


## Sources

- https://www.useparagon.com/learn/rag-best-practices-optimizing-tool-calling/
- https://www.patronus.ai/llm-testing/custom-optimization-tools-for-llm
- https://www.getmaxim.ai/articles/observability-and-evaluation-strategies-for-tool-calling-ai-agents-a-complete-guide/
