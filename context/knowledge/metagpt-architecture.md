# metagpt-architecture

*Researched: 2026-03-31 19:18 CDT*

# MetaGPT Architecture Deep-Dive

## Novel Techniques (vs basic ReAct/CoT agent loops)

### 1. Watch-CauseBy Implicit SOP
No central orchestrator -- pipeline emerges from roles watching specific action types. Each role declares `_watch([ActionClass])`. When message with `cause_by=ActionClass` appears, watching roles pick it up. More decoupled than LangGraph's explicit graphs.

### 2. Three-Axis Message Routing
Messages routed on three dimensions simultaneously:
- `cause_by` (content-based) -- Action class that produced the message
- `send_to` (address-based) -- Explicit targeting, supports `<all>`, `<none>`, `<self>`
- `addresses` (subscription-based) -- Role has address set, environment matches incoming

### 3. ActionNode Tree System
Declarative structured output specification that compiles to prompts and dynamically generates Pydantic validators. Each node has key, expected_type, instruction, example, children. `create_model_class()` generates Pydantic models dynamically.

### 4. Dual-Mode Roles (`use_fixed_sop` flag)
Same role class runs as either:
- Fixed SOP mode (BY_ORDER): Predefined action sequence
- Dynamic mode (REACT): Free-form agent with tool calling
Toggle via single flag.

### 5. Experience Pool with @exp_cache
Automatic experience caching for LLM calls with semantic matching, scoring, and perfect-judge evaluation. Learned codebase cache.

### 6. TeamLeader Dispatcher Pattern
Meta-agent that understands team composition and routes tasks to appropriate specialists, replacing hardcoded pipelines.

### 7. Context Cascading via ContextMixin
Shared config/LLM/cost-manager with per-role override through property cascade: `role.private_X > context.X > default()`.

### 8. Per-Role Async Message Queues
Each role has `asyncio.Queue`-backed buffer. Concurrent agent execution via `asyncio.gather()`.

## Message Format
```python
class Message(BaseModel):
    id: str                    # UUID
    content: str               # Natural language
    instruct_content: BaseModel # Structured output
    cause_by: str              # Action class name
    sent_from: str             # Role name
    send_to: set[str]          # Recipients
    metadata: Dict[str, Any]   # Extra data
```

## Error Handling Layers
1. @handle_exception decorator (serialization)
2. @role_raise_decorator on Role.run()
3. Tenacity retry on LLM calls (6 attempts, exponential backoff)
4. Command execution fallback (stop on first failure)
5. is_pass self-evaluation (Engineer loops until complete)
6. max_react_loop circuit breaker (default 50)
7. Serialization/recovery of entire Team state
8. Budget enforcement (NoMoneyException)


## Sources

- https://github.com/FoundationAgents/MetaGPT
