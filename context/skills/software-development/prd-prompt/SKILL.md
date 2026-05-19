---
name: prd-prompt
description: Product Requirements Document (PRD) generation prompt for AI agents. Senior PM quality PRDs with user stories, acceptance criteria, and technical constraints.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
prerequisites:
  commands: [python3]
---

# PRD Prompt for AI Agents

Based on the "Senior PM / PRD Prompt" pattern from AI agent architecture research.

## Purpose

Generate production-quality PRDs that AI agents can actually use to build software. Not vague brainstorms — specific, actionable specifications.

## The Prompt Template

```markdown
# PRD Generation Prompt

You are a Senior Product Manager with 10 years of experience building software products.
Generate a comprehensive PRD for the following feature/product.

## Input
- Product: {{product_name}}
- Feature: {{feature_name}}
- Target Users: {{user_personas}}
- Business Goal: {{business_objective}}
- Constraints: {{technical_constraints}}

## Output Structure

### 1. Overview (2-3 paragraphs)
What this feature does, why it matters, and how it fits the product strategy.

### 2. User Stories
At least 5 user stories in standard format:
- As a [user type], I want [goal], so that [benefit]
- Acceptance criteria for each

### 3. Functional Requirements
Numbered list of specific behaviors:
- FR-001: System shall...
- FR-002: User can...
- Each requirement must be testable

### 4. Non-Functional Requirements
- Performance: response time, throughput
- Security: auth, data protection
- Reliability: uptime, error handling
- Scalability: concurrent users, data volume

### 5. User Flow
Step-by-step flow with edge cases:
1. User opens...
2. System displays...
3. User selects...
4. Edge case: If user has no X, show Y

### 6. Technical Constraints
- API dependencies
- Database schema changes
- Third-party integrations
- Browser/device support

### 7. Success Metrics
- Primary metric (the one that matters)
- Secondary metrics (supporting indicators)
- Measurement method

### 8. Open Questions
What we don't know yet and need to validate.

## Rules
- Every requirement must have an ID (FR-001, NFR-001, etc.)
- Every user story must have acceptance criteria
- No vague language ("should", "might", "consider") — use "shall", "must", "will"
- Include at least 3 edge cases
- Specify error states explicitly
```

## Example Usage

```python
delegate_task(
    goal="Generate PRD for Twitter cookie API skill",
    model="claude-sonnet-4",
    context="""
Product: Hermes Agent
Feature: X/Twitter Cookie API Skill
Target Users: Hermes Agent users who need to monitor Twitter
Business Goal: Enable authenticated Twitter access without official API costs
Constraints: Must use user's cookies, read-only, no posting

Generate a full PRD using the Senior PM template.
"""
)
```

## Why This Works

1. **Structured output** — AI fills in sections, not free-form brainstorming
2. **Testable requirements** — Every FR has an ID and is verifiable
3. **Edge cases included** — Forces thinking about failure modes
4. **Metrics defined** — Success is measurable, not subjective
5. **Constraints explicit** — Technical boundaries are clear upfront

## Integration with Hermes

Use this prompt when:
- Planning new skills or features
- Defining agent behavior specifications
- Writing project plans that need concrete deliverables
- Communicating requirements to subagents

## Anti-Patterns to Avoid

- ❌ "Build a Twitter integration" — too vague
- ✅ "Build read-only tweet fetching via cookie auth with rate limiting and error handling"
- ❌ "Make it fast" — not measurable
- ✅ "API response time < 500ms p95, search results in < 2s"
- ❌ "Handle errors gracefully" — not specific
- ✅ "On auth failure (401), refresh cookies once, then notify user to re-authenticate"
