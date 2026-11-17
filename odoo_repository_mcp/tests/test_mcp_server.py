# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import json

from odoo import Command
from odoo.tests.common import HttpCase

from .common import McpCommon


class TestMcpServerHttp(McpCommon, HttpCase):
    """End-to-end tests through the MCP endpoint."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Use a dedicated server with only the tools of this module: other
        # MCP modules can be installed in the same database, and their own
        # tools may not be loadable yet when this module's tests run
        # (modules are tested one by one, in load order).
        cls.server = cls.env["mcp.server"].create(
            {
                "name": "Test Server",
                "tool_ids": [
                    Command.link(cls.env.ref(f"odoo_repository_mcp.{tool}_tool").id)
                    for tool in (
                        "module_search",
                        "module_get_details",
                        "module_get_dependencies",
                        "module_list_versions",
                        "repo_list_versions",
                        "repo_list_repositories",
                    )
                ],
            }
        )
        cls.key_user = cls.env["res.users"].create(
            {
                "name": "MCP Key User",
                "login": "mcp_key_user",
                "groups_id": [
                    Command.link(cls.env.ref("base.group_user").id),
                    Command.link(
                        cls.env.ref("odoo_repository.group_odoo_repository_user").id
                    ),
                ],
            }
        )
        cls.security_key = "test-mcp-security-key"
        cls.env["mcp.server.key"].create(
            {
                "name": "Test Key",
                "server_id": cls.server.id,
                "user_id": cls.key_user.id,
                "hashed_key": cls.env["mcp.server.key"]._hash_key(cls.security_key),
            }
        )
        # Refresh the cached key lookup so the new key is resolvable
        cls.env.registry.clear_cache()

    def _post(self, method, params=None):
        payload = {"jsonrpc": "2.0", "id": "1", "method": method}
        if params is not None:
            payload["params"] = params
        return self.url_open(
            f"/mcp/{self.server.key}",
            data=json.dumps(payload),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.security_key}",
            },
        )

    def test_tools_list(self):
        response = json.loads(self._post("tools/list").content.decode("utf-8"))
        self.assertIn("result", response)
        tools = {tool["name"] for tool in response["result"]["tools"]}
        self.assertEqual(
            tools,
            {
                "module_search",
                "module_get_details",
                "module_get_dependencies",
                "module_list_versions",
                "repo_list_versions",
                "repo_list_repositories",
            },
        )

    def test_call_module_search(self):
        response = json.loads(
            self._post(
                "tools/call",
                {"name": "module_search", "arguments": {"name": "test_module_a"}},
            ).content.decode("utf-8")
        )
        self.assertNotIn("error", response)
        content = response["result"]["structuredContent"]
        self.assertEqual(content["total"], 3)
        self.assertEqual(len(content["modules"]), 3)

    def test_call_module_search_error(self):
        response = json.loads(
            self._post(
                "tools/call",
                {"name": "module_search", "arguments": {"version": "99.0"}},
            ).content.decode("utf-8")
        )
        self.assertNotIn("error", response)
        content = response["result"]["structuredContent"]
        self.assertIn("Unknown Odoo version", content["error"])
