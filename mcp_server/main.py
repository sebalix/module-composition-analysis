"""Odoo MCA MCP Server.

Exposes Odoo MCA module data as MCP tools discovered dynamically from Odoo.
Uses stdio transport — meant to be launched by an MCP client (e.g. Claude Desktop).

Config via environment variables:
    ODOO_URL      — Odoo base URL (default: http://localhost:8069)
    ODOO_DB       — Odoo database name (required)
    ODOO_USER     — Odoo username (default: admin)
    ODOO_PASSWORD — Odoo password (required)
"""

import asyncio
import logging
import os

import mcp_types as types
from mcp.server.lowlevel.server import Server
from mcp.server.stdio import stdio_server
from odoo_client import OdooClient

_logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=os.sys.stderr,
)


def build_server(odoo: OdooClient) -> Server:
    server = Server(
        name="odoo-repository-mca",
        title="Odoo MCA Repository",
        version="1.0.0",
        description=(
            "Query Odoo modules data from the Module Composition Analysis database."
        ),
    )

    async def on_list_tools(ctx, params):
        tool_defs = odoo.get_tools()
        _logger.info("Discovered %d tools from Odoo", len(tool_defs))
        return types.ListToolsResult(
            tools=[
                types.Tool(
                    name=t["name"],
                    description=t["description"],
                    inputSchema=t["inputSchema"],
                )
                for t in tool_defs
            ]
        )

    async def on_call_tool(ctx, params):
        name = params.name
        arguments = params.arguments or {}
        _logger.info("Calling tool %r", name)
        result_text = odoo.execute_tool(name, arguments)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=result_text)],
        )

    server.add_request_handler(
        "tools/list", types.PaginatedRequestParams, on_list_tools
    )
    server.add_request_handler("tools/call", types.CallToolRequestParams, on_call_tool)
    return server


async def main():
    odoo = OdooClient()
    odoo.login()

    server = build_server(odoo)

    _logger.info("MCP server ready (stdio)")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
