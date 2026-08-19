"""HTTP client for Odoo endpoints."""

import json
import logging
import os

import requests  # noqa: UP035

_logger = logging.getLogger(__name__)


class OdooClient:
    def __init__(self):
        self.base_url = os.environ.get("ODOO_URL", "http://localhost:8069").rstrip("/")
        self.db = os.environ.get("ODOO_DB", "")
        self.user = os.environ.get("ODOO_USER", "admin")
        self.password = os.environ.get("ODOO_PASSWORD", "")
        self.api_key = os.environ.get("ODOO_API_KEY", "")
        self._session = None

    def login(self):
        self._session = requests.Session()
        if self.api_key:
            self._session.headers["API-KEY"] = self.api_key
            _logger.info(
                "Using API key authentication for %s on %s", self.user, self.db
            )
        else:
            url = f"{self.base_url}/web/session/authenticate"
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "db": self.db,
                    "login": self.user,
                    "password": self.password,
                },
            }
            resp = self._session.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if data.get("error"):
                raise RuntimeError(f"Login failed: {data['error']}")
            _logger.info("Logged into Odoo as %s on %s", self.user, self.db)

    def get_tools(self):
        url = f"{self.base_url}/odoo-repository/mcp/tools"
        resp = self._session.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def execute_tool(self, name, arguments):
        url = f"{self.base_url}/odoo-repository/mcp/execute"
        resp = self._session.post(
            url,
            data=json.dumps({"name": name, "arguments": arguments}),
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        body = resp.json()
        if isinstance(body, dict) and "error" in body:
            raise RuntimeError(body["error"])
        return resp.text
