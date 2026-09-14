from __future__ import annotations

from fastapi import APIRouter, Request

from kpi_api.agent.tools import McpToolGateway, to_anthropic_tool
from kpi_api.schemas.chat import ToolInfo, ToolList
from kpi_core.errors import UpstreamUnavailable

router = APIRouter(prefix="/v1/meta", tags=["meta"])


@router.get(
    "/tools", response_model=ToolList, summary="The MCP tools exactly as the chat agent sees them"
)
async def tools(request: Request) -> ToolList:
    gateway: McpToolGateway = request.app.state.mcp_gateway
    try:
        specs = await gateway.list_tools()
    except Exception as exc:
        raise UpstreamUnavailable("MCP server unreachable", reason=type(exc).__name__) from exc
    items = []
    for spec in specs:
        converted = to_anthropic_tool(spec)
        items.append(
            ToolInfo(
                name=spec.name,
                description=spec.description,
                input_schema=converted["input_schema"],
                strict=bool(converted.get("strict", False)),
            )
        )
    return ToolList(items=items)
