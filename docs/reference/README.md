# Reference

| Page | Content |
|---|---|
| [rest-api.md](rest-api.md) | Endpoints, parameters, response shapes, examples |
| [mcp-tools.md](mcp-tools.md) | The four tools, parameters, results, error envelope, examples |
| [sse-protocol.md](sse-protocol.md) | Chat streaming events |
| [error-codes.md](error-codes.md) | Stable error codes, HTTP status, envelope mapping |
| [configuration.md](configuration.md) | Every `KPI_*` variable |

Drift gates: `scripts/check_tool_docs.py` compares the MCP tool list against
[mcp-tools.md](mcp-tools.md); the API OpenAPI snapshot lives next to the API tests.
