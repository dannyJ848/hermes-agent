# event-driven-multi-agent-patterns

*Researched: 2026-04-18 09:05 CDT*

## Four Event-Driven Design Patterns for Multi-Agent Systems

Source: Confluent (Sean Falconer & Andrew Sellers), Jan 2025.

### Core Idea: Replace direct agent-to-agent connections with event streams (Apache Kafka topics) to gain scalability, fault tolerance, and simplified coordination.

### Pattern 1: Orchestrator-Worker
- Orchestrator uses key-based partitioning to distribute commands
- Workers form a consumer group, pulling from assigned partitions
- Failed workers auto-recover via Kafka's Consumer Rebalance Protocol and offset replay
- **Key benefit:** Orchestrator decoupled from worker lifecycle management

### Pattern 2: Hierarchical Agent
- Orchestrator-Worker applied recursively at each tree level
- Topics serve as logical swimlanes for agent-specific workloads
- Siblings form consumer groups on same topics
- **Key benefit:** Agents can be added/removed without managing change propagation

### Pattern 3: Blackboard
- Shared knowledge base becomes a streaming topic
- Agents produce/consume events without direct communication
- Keying or payload fields annotate originating agent
- **Key benefit:** Maximum decoupling — agents only need to know event schema

### Pattern 4: Market-Based
- Bids topic + asks topic + transaction notifications topic
- Market maker service matches bids/asks
- **Key benefit:** Eliminates quadratic connections between solver agents; leverages proven financial services architecture

### Meta-Pattern: Events as Shared Language
Agents react to upstream events/commands rather than divining action. Three uses: interpret commands (JSON), share context (broadcasts), coordinate tasks.

## Sources

- https://www.confluent.io/blog/event-driven-multi-agent-systems/
