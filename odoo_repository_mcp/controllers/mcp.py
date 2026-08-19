import json

from odoo import http
from odoo.http import request

from ..tools.registry import (
    TOOL_REGISTRY,
    execute_tool,
    get_tools_schema,
)


class OdooRepositoryMCP(http.Controller):
    @http.route(
        "/odoo-repository/mcp/tools",
        type="http",
        auth="api_key",
        csrf=False,
        methods=["GET"],
    )
    def list_tools(self):
        tools = get_tools_schema()
        return request.make_response(
            json.dumps(tools), {"Content-Type": "application/json"}
        )

    @http.route(
        "/odoo-repository/mcp/execute",
        type="http",
        auth="api_key",
        csrf=False,
        methods=["POST"],
    )
    def execute(self):
        body = json.loads(request.httprequest.get_data())
        name = body["name"]
        arguments = body.get("arguments", {})
        if name not in TOOL_REGISTRY:
            return request.make_response(
                json.dumps({"error": f"Unknown tool: {name}"}),
                {"Content-Type": "application/json"},
                status=404,
            )
        try:
            result = execute_tool(name, request.env, arguments)
            return request.make_response(result, {"Content-Type": "application/json"})
        except Exception as exc:
            return request.make_response(
                json.dumps({"error": str(exc)}),
                {"Content-Type": "application/json"},
                status=500,
            )
