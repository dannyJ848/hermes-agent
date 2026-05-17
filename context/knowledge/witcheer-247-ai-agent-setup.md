# witcheer-247-ai-agent-setup

*Researched: 2026-04-01 22:25 CDT*

# Witcheer's 24/7 AI Agent Setup — Full Breakdown

**Source:** [@witcheer on X](https://x.com/witcheer/status/2037530350763524482) — "Living With an AI agent - My Full Setup After 2 Months" (443K views, 5K bookmarks)

## Hardware
- Mac Mini M4, 16GB RAM, ~$600
- Runs 24/7 in living room
- Total disk: ~120MB (agent framework) + 6.6GB (local LLM models)
- No cloud server, no GPU cluster, no AWS bill

## The Three-Model Stack
1. **Interactive Chat: GLM-5 via Z.AI** ($21/month coding plan)
   - Cheapest model with tool calling that actually works
   - Reasoning token trap: GLM-5 always generates thinking tokens, fills context fast
   - After 15-20 exchanges, agent slows to crawl from re-processing thousands of reasoning tokens
   
2. **Cron Jobs: GLM-4.7 via Z.AI** (same plan, cheaper model)
   - All 18 automated jobs run on GLM-4.7 to preserve interactive quota
   - Z.AI rate limit: 600 prompts per 5 hours on coding plan
   
3. **Compression: Qwen3.5 via local Ollama**
   - Runs locally for context compression (summarizing old messages)
   - Originally used cloud API → death spiral (compression uses quota → more cron jobs → more compression → rate limit hit)
   - Moving to local Ollama solved the death spiral

## Agent Framework: Hermes Agent
- Open-source Python by NousResearch
- Interface: Telegram bot
- Runs as macOS launchd service (starts on boot, restarts on crash)
- Features: terminal access, file I/O, web search, web fetch, code execution, cron scheduler, skills system, memory system, MCP support
- Limitations: single model fallback only, no automatic session cleanup, writing quality is model-limited

## The 18 Cron Jobs (Autonomous Research Pipeline)
- Runs between 7am yesterday and 7am today
- Searches web, fetches articles, runs shell scripts against 8 different APIs
- Writes findings to memory files
- Drafts content for Telegram channel
- Scores drafts against voice rules
- Logs everything to structured context system

## 35 Shell Scripts
- Automation layer connecting different APIs
- Used for: fetching, scraping, transforming, notifying

## 6 Custom Skills
- On-demand capabilities loaded when needed
- Markdown files teaching the agent new procedures

## ALIVE Context System (Key Innovation)
- Structured context system that makes every session smarter than the last
- Tomorrow's research benefits from today's findings
- Cross-references against actual projects and deadlines
- The compound knowledge effect: each session builds on all previous sessions

## Voice Feedback Loop
- System for teaching the AI your writing style
- Scores drafts against personal voice rules
- Corrects writing to match user's natural style

## Lessons from 2 Months
- Reasoning tokens are the silent killer of long sessions
- Local compression (Ollama) is essential to avoid API quota death spiral
- Using cheaper model (GLM-4.7) for cron jobs preserves interactive quota
- $21/month is viable for a full 24/7 agent setup
- Framework limitations: single fallback, manual session cleanup needed

## Relevance to SOMA
1. **Same model stack**: We use GLM-5.1 (interactive) + could add GLM-4.7 for cron jobs
2. **ALIVE context system**: SOMA needs exactly this — medical knowledge that compounds across sessions
3. **Voice feedback loop**: For bilingual (EN/ES) medical content, matching the right tone is critical
4. **Local compression**: We should set up Ollama for context compression to avoid API quota issues
5. **Rate limit awareness**: 600 prompts/5 hours means we need to be strategic about cron job frequency
6. **launchd service**: We already do this, but adding crash recovery and health monitoring would improve reliability


## Sources

- https://x.com/witcheer/status/2037530350763524482
- https://x.com/witcheer/article/2037528582298194123
