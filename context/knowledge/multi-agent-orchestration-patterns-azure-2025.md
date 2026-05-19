# multi-agent orchestration patterns Azure 2025

*Researched: 2026-04-17 21:06 CDT*

# Multi-Agent Orchestration Patterns (Azure Architecture Center)

**Source:** Microsoft Azure Architecture Center, 2025

## Core Principle
**"Use the lowest level of complexity that reliably meets your requirements."**

## Three Complexity Levels
1. **Direct model call** — Single LLM call, no agent logic. For classification, summarization, single-step tasks.
2. **Single agent with tools** — One agent reasons/acts by selecting tools. Right default for enterprise. *Guard against infinite tool-call loops with iteration limits.*
3. **Multi-agent orchestration** — Only when single agent can't reliably handle cross-functional/cross-domain problems.

## The Five Orchestration Patterns

### 1. Sequential (Pipeline)
- Predefined linear order, deterministic routing
- ✅ Multi-stage processes with clear dependencies (draft→review→polish)
- ❌ Avoid when stages are parallel, agents need real collaboration, or backtracking required

### 2. Concurrent (Fan-out/Fan-in)
- Multiple agents run simultaneously on same task
- Aggregation: voting, weighted merge, LLM synthesis
- ✅ Independent perspectives, time-sensitive, brainstorming
- ❌ Avoid when agents need cumulative context or shared state coordination

### 3. Group Chat
- Agents discuss in shared conversational space
- Orchestrator manages turn-taking, can insert context
- ✅ Collaborative reasoning, negotiation, creative problem-solving
- ❌ Avoid when deterministic results required or conversations cycle without convergence

### 4. Hierarchical (Manager-Worker)
- Manager agent decomposes → assigns to workers → aggregates
- ✅ Complex task decomposition, workload balancing, specialized workers
- ❌ Avoid when manager becomes bottleneck or workers can't work independently

### 5. Custom / Event-Driven
- Event-driven choreography with pub/sub, message queues
- ✅ Loose coupling, independent scaling, maximum flexibility
- ❌ Avoid when simplicity preferred; debugging distributed failures is hard

## Anti-Patterns to Avoid
- **Premature multi-agent:** Start with single agent + tools, escalate only when needed
- **Giant context sharing:** Don't dump everything into shared state
- **Missing failure handling:** Every agent interaction needs timeout, retry, fallback
- **Unbounded loops:** Set max iterations; multi-agent debates can cycle forever

## Sources

- https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns
