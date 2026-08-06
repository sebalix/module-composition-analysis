import json
import secrets
import time

import anyio
from mcp_types.version import HANDSHAKE_PROTOCOL_VERSIONS, LATEST_HANDSHAKE_VERSION

from odoo import http
from odoo.http import request

from odoo.addons.odoo_repository_mcp.tools import mcp, set_odoo_env

MCP_SESSION_ID_HEADER = "Mcp-Session-Id"
SESSION_TTL = 3600
JSONRPC_ERROR_CODES = {
    "INVALID_REQUEST": -32600,
    "METHOD_NOT_FOUND": -32601,
    "INTERNAL_ERROR": -32603,
}

_sessions = {}


_pending_session = None


def _session_id():
    return secrets.token_hex(16)


def _jsonrpc_error(code, message, msg_id=None):
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def _jsonrpc_response(result, msg_id):
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _session_gc():
    now = time.monotonic()
    expired = [sid for sid, s in _sessions.items() if s["expires"] <= now]
    for sid in expired:
        del _sessions[sid]


def _acquire_session():
    sid = request.httprequest.headers.get(MCP_SESSION_ID_HEADER)
    if sid and sid in _sessions:
        _sessions[sid]["expires"] = time.monotonic() + SESSION_TTL
        return _sessions[sid]
    return None


class OdooRepositoryMCP(http.Controller):
    @http.route(
        "/odoo-repository/mcp",
        type="http",
        auth="user",
        csrf=False,
        methods=["POST"],
    )
    def mcp_endpoint(self, **kwargs):
        global _pending_session
        _pending_session = None
        body = request.httprequest.get_data()
        if not body:
            return self._make_response(
                _jsonrpc_error(JSONRPC_ERROR_CODES["INVALID_REQUEST"], "Empty body")
            )
        try:
            raw = json.loads(body)
        except json.JSONDecodeError as exc:
            return self._make_response(
                _jsonrpc_error(
                    JSONRPC_ERROR_CODES["INVALID_REQUEST"], f"Invalid JSON: {exc}"
                )
            )
        _session_gc()
        session = _acquire_session()
        if isinstance(raw, list):
            results = [self._dispatch(msg, session) for msg in raw]
            results = [r for r in results if r is not None]
        else:
            results = self._dispatch(raw, session)
        headers = {"Content-Type": "application/json"}
        if _pending_session:
            headers[MCP_SESSION_ID_HEADER] = _pending_session
        elif session:
            headers[MCP_SESSION_ID_HEADER] = session["session_id"]
        return self._make_response(
            json.dumps(results) if isinstance(results, list) else json.dumps(results),
            headers,
        )

    def _dispatch(self, raw, session):
        method = raw.get("method")
        msg_id = raw.get("id")

        if method is None:
            return _jsonrpc_error(
                JSONRPC_ERROR_CODES["INVALID_REQUEST"],
                "Missing method",
                msg_id,
            )

        if msg_id is None:
            if method == "notifications/initialized" and session:
                session["initialized"] = True
            return None

        if method == "initialize":
            return self._handle_initialize(raw, msg_id)

        if not session or not session.get("initialized"):
            return _jsonrpc_error(
                JSONRPC_ERROR_CODES["INVALID_REQUEST"],
                "Not initialized",
                msg_id,
            )

        if method == "tools/list":
            return self._handle_list_tools(msg_id)

        if method == "tools/call":
            return self._handle_call_tool(raw.get("params", {}), msg_id)

        return _jsonrpc_error(
            JSONRPC_ERROR_CODES["METHOD_NOT_FOUND"],
            f"Method not found: {method}",
            msg_id,
        )

    def _handle_initialize(self, raw, msg_id):
        params = raw.get("params", {}) or {}
        client_version = params.get("protocolVersion", LATEST_HANDSHAKE_VERSION)
        if client_version in HANDSHAKE_PROTOCOL_VERSIONS:
            negotiated = client_version
        else:
            negotiated = LATEST_HANDSHAKE_VERSION
        global _pending_session
        sid = _session_id()
        _pending_session = sid
        _sessions[sid] = {
            "session_id": sid,
            "protocol_version": negotiated,
            "initialized": False,
            "expires": time.monotonic() + SESSION_TTL,
        }
        result = {
            "protocolVersion": negotiated,
            "capabilities": {
                "tools": {"listChanged": False},
            },
            "serverInfo": {
                "name": "odoo-repository-mca",
                "title": "Odoo MCA Repository MCP Server",
                "version": "1.0.0",
            },
        }
        return _jsonrpc_response(result, msg_id)

    def _handle_list_tools(self, msg_id):
        try:
            tools = anyio.run(mcp.list_tools)
        except Exception as exc:
            return _jsonrpc_error(
                JSONRPC_ERROR_CODES["INTERNAL_ERROR"],
                str(exc),
                msg_id,
            )
        tool_list = []
        for tool in tools:
            tool_list.append(
                tool.model_dump(by_alias=True, mode="json", exclude_none=True)
            )
        return _jsonrpc_response(
            {"tools": tool_list, "resultType": "complete"},
            msg_id,
        )

    def _handle_call_tool(self, params, msg_id):
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        if not tool_name:
            return _jsonrpc_error(
                JSONRPC_ERROR_CODES["INVALID_REQUEST"],
                "Missing tool name",
                msg_id,
            )
        set_odoo_env(request.env)
        try:
            result = anyio.run(mcp.call_tool, tool_name, arguments)
        except Exception as exc:
            return _jsonrpc_error(
                JSONRPC_ERROR_CODES["INTERNAL_ERROR"],
                str(exc),
                msg_id,
            )
        finally:
            set_odoo_env(None)
        return _jsonrpc_response(
            result.model_dump(by_alias=True, mode="json", exclude_none=True),
            msg_id,
        )

    def _make_response(self, body, headers=None):
        response = request.make_response(body)
        if headers:
            if isinstance(headers, dict):
                for key, value in headers.items():
                    response.headers[key] = value
            else:
                for key, value in headers:
                    response.headers[key] = value
        return response
