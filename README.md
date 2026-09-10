# Zairus KPI Intelligent Platform

Work in progress: an AI-native platform for exploring quarterly KPI estimates, where every
answer an LLM gives is backed by visible, audited tool calls.

Planned pieces:

- `packages/kpi_core` — domain layer (models, services, repositories, errors)
- `services/api` — REST API and the chat agent
- `services/mcp` — MCP server for AI clients
- `apps/` — chat UI and website

`make help` lists the available commands.
