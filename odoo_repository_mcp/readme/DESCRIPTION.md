This module is the server-side counterpart of the Odoo MCA MCP server.
It exposes Odoo MCA data through a tool registry and two HTTP endpoints
consumed by the standalone `mcp_server/`.

## How it works

The module provides:

- A **tool registry** (`tools/registry.py`) populated automatically via convention — no
  manual registration needed.
- A **discovery endpoint** (`GET /odoo-repository/mcp/tools`) that returns the list
  of available tools with their JSON Schema definitions.
- An **execution endpoint** (`POST /odoo-repository/mcp/execute`) that runs a tool
  by name and returns its result.

The standalone MCP server (located in `mcp_server/`) calls these endpoints at
startup to dynamically discover available tools, then proxies tool calls from
the MCP client (Claude Desktop, etc.) back to the execution endpoint.

This module has zero dependency on the `mcp` Python package — only the
standalone server needs it.

## Registering tools from another module

Any Odoo module that depends on `odoo_repository_mcp` can declare its own
MCP tools. No manual registration calls — just follow the naming conventions
and tools are discovered automatically.

### Convention

For each tool you need a **handler** method and an optional **properties**
static method on the `mcp.tool` model:

- `_handler_{tool_name}(self, arguments)` — method implementing the tool.
  Its **docstring** becomes the tool description shown to the AI.
- `_properties_{tool_name}(self)` — method returning a 2-tuple
  `(properties_dict, required_list)` defining the JSON Schema for the tool's
  input. If omitted, the tool accepts no arguments.

All `_handler_*` methods are discovered automatically via `_register_hook`.

### Step 1: depend on `odoo_repository_mcp`

```python
# my_module/__manifest__.py
{
    "name": "My Module",
    "depends": ["odoo_repository_mcp"],
    ...
}
```

### Step 2: define your tool

```python
# my_module/models/mcp_tool.py
import json

from odoo import models


class MCPTool(models.AbstractModel):
    _inherit = "mcp.tool"

    def _properties_my_search(self):
        return (
            {
                "query": {"type": "string", "description": "Search text."},
                "max_results": {"type": "integer", "description": "Max results."},
            },
            ["query"],
        )

    def _handler_my_search(self, arguments):
        """Search something useful across Odoo modules."""
        query = arguments["query"]
        max_results = arguments.get("max_results", 10)

        records = self.env["your.model"].sudo().search_read(
            [("name", "ilike", query)],
            fields=["id", "name", "description"],
            limit=max_results,
        )
        return json.dumps(records, default=str)
```

### Step 3: import your model

```python
# my_module/models/__init__.py
from . import mcp_tool
```

```python
# my_module/__init__.py
from . import models
```

That's it. The tool `my_search` is discovered and registered automatically.

### Overriding an existing tool handler

Because handlers are model methods, any module inheriting `mcp.tool` can
override them:

```python
class MCPTool(models.AbstractModel):
    _inherit = "mcp.tool"

    def _handler_search_modules(self, arguments):
        # customized version of the base handler
        result = super()._handler_search_modules(arguments)
        # post-process result...
        return result
```

The registry stores model and method name strings — it resolves to whichever
class provides the final override at call time.

### Handler reference

- `_handler_{tool_name}(self, arguments)` — instance method. Receives a `dict`
  of deserialized JSON arguments. The Odoo environment is available via
  `self.env`. Must return a `str` (JSON-encoded result).
- `_properties_{tool_name}(self)` — method. Must return a 2-tuple
  `(properties_dict, required_list)` where `properties_dict` follows JSON
  Schema ``properties`` syntax and `required_list` lists mandatory field names.
  If omitted, the tool accepts an empty object `{}`.

Example with no arguments:

```python
def _handler_get_time(self, arguments):
    """Return the current server time."""
    return json.dumps({"time": str(fields.Datetime.now())})
```

No `_properties_get_time` needed — the input schema defaults to `{}`.

## Testing

Once installed, verify tools are registered (replace the API key value):

```bash
curl http://localhost:8069/odoo-repository/mcp/tools \
  -H "API-KEY: your-api-key"
```

Test execution:

```bash
curl -X POST http://localhost:8069/odoo-repository/mcp/execute \
  -H "Content-Type: application/json" \
  -H "API-KEY: your-api-key" \
  -d '{"name":"search_modules","arguments":{"query":"base"}}'
```

## Authentication

Endpoints use `auth="api_key"`, provided by the `auth_api_key` OCA module.
Requests must include the API key in the `API-KEY` HTTP header.

### Setup (in Odoo)

1. Ensure the `auth_api_key` module is installed.
2. Enable debug mode, go to **Settings > Technical > API Keys**.
3. Create an API key for a user (e.g. admin). Copy the generated key.

### Setup (in the MCP server)

Pass the key via the `ODOO_API_KEY` environment variable:

```bash
export ODOO_API_KEY="your-api-key-here"
```

When `ODOO_API_KEY` is set, the MCP server uses it directly (skipping
session-based login). If not set, it falls back to `ODOO_USER`/`ODOO_PASSWORD`
and a session cookie.

### Testing with an API key

```bash
curl http://localhost:8069/odoo-repository/mcp/tools \
  -H "API-KEY: your-api-key-here"

curl -X POST http://localhost:8069/odoo-repository/mcp/execute \
  -H "Content-Type: application/json" \
  -H "API-KEY: your-api-key-here" \
  -d '{"name":"search_modules","arguments":{"query":"base"}}'
```

Requests without a valid API key are rejected with a 401 response.
