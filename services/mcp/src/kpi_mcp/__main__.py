"""`python -m kpi_mcp --transport stdio|http`."""

from __future__ import annotations

import argparse
import sys

from kpi_core.obs.logging import configure_logging
from kpi_mcp.server import build_default_server
from kpi_mcp.settings import McpSettings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="kpi_mcp")
    parser.add_argument("--transport", choices=["stdio", "http"], default=None)
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args(argv)
    settings = McpSettings()
    transport = args.transport or settings.mcp_transport
    configure_logging(settings.service_name, settings.log_level)  # stderr only: stdio stays clean
    mcp = build_default_server(settings.model_copy(update={"mcp_transport": transport}))
    if transport == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(
            transport="http",
            host=args.host or settings.mcp_host,
            port=args.port or settings.mcp_port,
            path=settings.mcp_path,
            show_banner=False,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
