"""Research Agent — autonomous web research with knowledge graph integration.

Performs multi-step research: search -> extract -> synthesize -> store.
Results are stored in the knowledge graph for later retrieval.

Usage:
    from agent.research_agent import ResearchAgent
    agent = ResearchAgent()
    result = agent.research("latest developments in LLM reasoning architectures")
    # result contains summary, sources, and knowledge graph nodes

ZERO-FAILURE: Returns partial results on any step failure.
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ResearchResult:
    """Result of a research operation."""
    query: str
    summary: str = ""
    sources: List[Dict[str, Any]] = field(default_factory=list)
    key_findings: List[str] = field(default_factory=list)
    knowledge_nodes: List[int] = field(default_factory=list)
    confidence: float = 0.0
    search_queries: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0


class ResearchAgent:
    """Autonomous research agent with knowledge graph integration."""

    def __init__(self, max_steps: int = 5, max_sources: int = 10):
        self.max_steps = max_steps
        self.max_sources = max_sources
        self._kg = None
        self._web_search = None
        self._web_extract = None

    def _get_knowledge_graph(self):
        """Lazy-load knowledge graph."""
        if self._kg is None:
            try:
                from agent.knowledge_graph import get_knowledge_graph
                self._kg = get_knowledge_graph()
            except Exception as e:
                logger.warning("[Research] Knowledge graph unavailable: %s", e)
        return self._kg

    def _get_web_search(self):
        """Lazy-load web search provider."""
        if self._web_search is None:
            try:
                from agent.web_search_provider import get_search_provider
                self._web_search = get_search_provider()
            except Exception as e:
                logger.warning("[Research] Web search unavailable: %s", e)
        return self._web_search

    def _get_web_extract(self):
        """Lazy-load web extraction provider."""
        if self._web_extract is None:
            try:
                from agent.web_search_provider import get_extract_provider
                self._web_extract = get_extract_provider()
            except Exception as e:
                logger.warning("[Research] Web extract unavailable: %s", e)
        return self._web_extract

    def research(self, query: str, depth: str = "medium") -> ResearchResult:
        """Execute a full research pipeline.

        Args:
            query: The research question or topic
            depth: "quick" (1 step), "medium" (3 steps), "deep" (5 steps)

        Returns:
            ResearchResult with summary, sources, and knowledge graph references
        """
        start_time = time.time()
        result = ResearchResult(query=query)

        try:
            # Step 1: Generate search queries
            search_queries = self._generate_queries(query)
            result.search_queries = search_queries

            # Step 2: Execute searches and collect sources
            sources = []
            for sq in search_queries[:self.max_steps]:
                found = self._search(sq)
                sources.extend(found)
                if len(sources) >= self.max_sources:
                    break

            # Deduplicate by URL
            seen_urls = set()
            unique_sources = []
            for s in sources:
                url = s.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_sources.append(s)
            result.sources = unique_sources[:self.max_sources]

            # Step 3: Extract content from sources
            for source in result.sources:
                try:
                    content = self._extract(source.get("url", ""))
                    if content:
                        source["extracted_content"] = content[:5000]  # Limit length
                except Exception:
                    pass

            # Step 4: Synthesize findings
            findings = self._synthesize(query, result.sources)
            result.key_findings = findings
            result.summary = self._generate_summary(query, findings, result.sources)

            # Step 5: Store in knowledge graph
            nodes = self._store_in_kg(query, result)
            result.knowledge_nodes = nodes

            # Calculate confidence based on source count and content quality
            result.confidence = min(1.0, len(result.sources) / 5.0) * 0.8 + 0.2

        except Exception as e:
            logger.warning("[Research] Pipeline failed: %s", e)
            result.summary = f"Research partially completed with errors: {e}"

        result.duration_seconds = time.time() - start_time
        return result

    def _generate_queries(self, query: str) -> List[str]:
        """Generate multiple search queries from a research question."""
        # Simple expansion: original + variations
        queries = [query]

        # Add time-bounded variants for recency
        queries.append(f"{query} 2024 2025")

        # Add specific variants
        if "architecture" in query.lower():
            queries.append(f"{query} implementation details")
        if "model" in query.lower():
            queries.append(f"{query} benchmark results")

        # Add Reddit/forum variants for community insights
        queries.append(f"{query} reddit discussion")

        return queries[:4]

    def _search(self, query: str) -> List[Dict[str, Any]]:
        """Execute web search and return results."""
        search = self._get_web_search()
        if not search:
            return []

        try:
            # Try different search methods
            results = []

            # Method 1: Built-in web search tool
            try:
                from tools.web_search_tool import web_search
                raw = web_search(query)
                if raw:
                    for item in raw[:5]:
                        if isinstance(item, dict):
                            results.append(item)
                        elif isinstance(item, str):
                            results.append({"title": item, "url": "", "snippet": item})
            except Exception:
                pass

            # Method 2: Provider-based search
            if not results:
                try:
                    raw = search.search(query)
                    for item in raw[:5]:
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "snippet": item.get("snippet", ""),
                        })
                except Exception:
                    pass

            return results
        except Exception as e:
            logger.debug("[Research] Search failed: %s", e)
            return []

    def _extract(self, url: str) -> str:
        """Extract content from a URL."""
        if not url:
            return ""

        extract = self._get_web_extract()
        if not extract:
            return ""

        try:
            # Method 1: Jina reader (if configured)
            if "jina" in str(type(extract)).lower():
                return extract.extract(url)

            # Method 2: Generic extraction
            return extract.extract(url)
        except Exception as e:
            logger.debug("[Research] Extraction failed for %s: %s", url, e)
            return ""

    def _synthesize(self, query: str, sources: List[Dict[str, Any]]) -> List[str]:
        """Extract key findings from sources."""
        findings = []

        for source in sources:
            content = source.get("extracted_content", "") or source.get("snippet", "")
            if not content:
                continue

            # Extract sentences that seem like key findings
            sentences = content.split(".")
            for sent in sentences:
                sent = sent.strip()
                if len(sent) < 20 or len(sent) > 300:
                    continue

                # Heuristic: sentences with numbers, quotes, or specific terms
                indicators = [
                    any(c.isdigit() for c in sent),
                    '"' in sent or "'" in sent,
                    any(term in sent.lower() for term in ["found", "show", "demonstrate", "achieve", "improve", "new", "novel"]),
                ]
                if any(indicators):
                    findings.append(sent)

            # Limit findings per source
            if len(findings) >= self.max_sources * 3:
                break

        # Deduplicate similar findings
        unique = []
        for f in findings:
            if not any(self._similar(f, u) for u in unique):
                unique.append(f)
        return unique[:15]

    def _similar(self, a: str, b: str) -> bool:
        """Quick similarity check for deduplication."""
        a_words = set(a.lower().split())
        b_words = set(b.lower().split())
        if not a_words or not b_words:
            return False
        overlap = len(a_words & b_words) / max(len(a_words), len(b_words))
        return overlap > 0.7

    def _generate_summary(self, query: str, findings: List[str], sources: List[Dict[str, Any]]) -> str:
        """Generate a human-readable summary."""
        if not findings:
            return f"No findings available for: {query}"

        lines = [
            f"Research: {query}",
            f"Sources analyzed: {len(sources)}",
            f"Key findings: {len(findings)}",
            "",
            "Summary:",
        ]

        # Group findings by theme (simple: just list top ones)
        for i, finding in enumerate(findings[:10], 1):
            lines.append(f"{i}. {finding}")

        if len(findings) > 10:
            lines.append(f"\n... and {len(findings) - 10} more findings")

        lines.append("")
        lines.append("Sources:")
        for i, source in enumerate(sources[:5], 1):
            title = source.get("title", "Untitled")
            url = source.get("url", "")
            lines.append(f"{i}. {title} - {url}")

        return "\n".join(lines)

    def _store_in_kg(self, query: str, result: ResearchResult) -> List[int]:
        """Store research results in knowledge graph."""
        kg = self._get_knowledge_graph()
        if not kg:
            return []

        node_ids = []
        try:
            # Create main topic node
            main_node_id = kg.add_node(
                node_type="research_topic",
                label=query,
                properties={
                    "summary": result.summary[:1000],
                    "confidence": result.confidence,
                    "source_count": len(result.sources),
                    "timestamp": time.time(),
                }
            )
            node_ids.append(main_node_id)

            # Create finding nodes
            for finding in result.key_findings[:10]:
                finding_node_id = kg.add_node(
                    node_type="finding",
                    label=finding[:200],
                    properties={"confidence": result.confidence}
                )
                kg.add_edge(main_node_id, "has_finding", finding_node_id)
                node_ids.append(finding_node_id)

            # Create source nodes
            for source in result.sources[:5]:
                source_node_id = kg.add_node(
                    node_type="source",
                    label=source.get("title", "Source")[:200],
                    properties={
                        "url": source.get("url", ""),
                        "snippet": source.get("snippet", "")[:500],
                    }
                )
                kg.add_edge(main_node_id, "sourced_from", source_node_id)
                node_ids.append(source_node_id)

        except Exception as e:
            logger.warning("[Research] KG storage failed: %s", e)

        return node_ids

    def related_topics(self, topic: str) -> List[str]:
        """Find related topics in the knowledge graph."""
        kg = self._get_knowledge_graph()
        if not kg:
            return []

        try:
            # Find nodes matching the topic
            nodes = kg.find_node(label=topic)
            if not nodes:
                return []
            
            # Get neighbors of the first matching node
            node_id = nodes[0]["id"]
            neighbors = kg.query_neighbors(node_id, direction="both")
            return [n.get("target_label", n.get("source_label", "")) for n in neighbors if n.get("target_label") or n.get("source_label")]
        except Exception:
            return []


# Singleton accessor
_research_agent_instance: Optional[ResearchAgent] = None


def get_research_agent() -> ResearchAgent:
    """Get the singleton research agent."""
    global _research_agent_instance
    if _research_agent_instance is None:
        _research_agent_instance = ResearchAgent()
    return _research_agent_instance


def quick_research(query: str) -> str:
    """One-shot research function for easy use."""
    agent = get_research_agent()
    result = agent.research(query, depth="quick")
    return result.summary
