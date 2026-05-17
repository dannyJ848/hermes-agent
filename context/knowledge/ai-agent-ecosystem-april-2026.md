# ai-agent-ecosystem-april-2026

*Researched: 2026-04-02 15:41 CDT*

# AI Agent Ecosystem Research - April 2026

## Agent Frameworks
- **OpenAI Agents SDK**: Production-grade multi-agent orchestration with handoffs, guardrails, tracing. `github.com/openai/openai-agents-python`
- **CrewAI v0.95+**: Role-based multi-agent framework with persistent memory, RAG. Maps to medical team structures. `github.com/crewAIInc/crewAI`
- **AutoGen v0.5+** (Microsoft): Conversational multi-agent, nested conversations, event-driven. `github.com/microsoft/autogen`
- **LangGraph** (LangChain): Stateful multi-actor as cyclic graphs with persistence. Auditable decision paths. `github.com/langchain-ai/langgraph`
- **PydanticAI**: Type-safe validated agent interactions. Critical for medical data schemas. `github.com/pydantic/pydantic-ai`

## MCP Ecosystem
- **MCP Spec v2025-03-26**: Streamable HTTP transport, improved capability negotiation, structured tool metadata
- **OpenAI MCP compatibility**: Agents SDK supports MCP natively
- **MCP Auth**: OAuth 2.1 standardization for secure medical data
- **MCP Sampling**: Servers can request LLM completions for agentic reasoning
- Notable servers: MCP PubMed, MCP FHIR (emerging), MCP Blender (3D), MCP Three.js (experimental)
- **Recommendation for SOMA**: Build Medical MCP Gateway — single authenticated server multiplexing anatomy models, drug DBs, clinical guidelines

## Self-Improvement Systems
- **DSPy** (Stanford): Algorithmic prompt/weight optimization with declarative modules. Most mature self-improvement framework. `github.com/stanfordnlp/dspy`
- **TextGrad**: Text-based "differentiation" for optimizing prompts/code/solutions. `github.com/zou-group/textgrad`
- **Self-RAG / Corrective RAG**: Agent critiques and corrects its own retrieval and generation
- **NVIDIA AgentIQ**: Evaluation/improvement loops with benchmarking. Provides "fitness function" for self-evolution.

## Medical AI
- **Google Med-PaLM 2/Med-Gemini**: Expert-level on medical licensing exams
- **Hugging Face BioMistral**: Open-source medical LLM — best for privacy-preserving local inference
- **Data Standards**: FHIR (patient records), SNOMED-CT (clinical terminology), ICD-11 (disease classification)
- **3D Anatomy Sources**: OpenAnatomy, BodyParts3D, Visible Human Project

## 3D Visualization
- **Three.js r170+**: WebGPU backend, node-based material system (NodeMaterial)
- **glTF 2.0 + Draco**: Efficient model transmission with compression
- **WebGPU**: Compute shaders for volumetric rendering of CT/MRI
- Key techniques: SSS, volume rendering, clipping planes, label occlusion, progressive loading

## SOMA Integration Roadmap
1. Hermes 3 8B locally (quantized) + MCP + LangGraph
2. Medical MCP Gateway (FHIR, drugs, guidelines)
3. DSPy for self-improvement loops
4. Three.js anatomy viewer controllable via MCP
5. Safety validation step in every self-evolution cycle


## Sources

- web_research across multiple queries
