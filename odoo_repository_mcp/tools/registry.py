"""MCP Tool Registry.

Convention over configuration: tools are discovered automatically from methods
on models inheriting ``mcp.tool``. See ``models/mcp_tool.py`` for details.
"""

TOOL_REGISTRY = {}


def register_tool(name, description, input_schema, model_name, method_name):
    TOOL_REGISTRY[name] = (description, input_schema, model_name, method_name)


def get_tools_schema():
    return [
        {
            "name": name,
            "description": desc,
            "inputSchema": schema,
        }
        for name, (desc, schema, _model, _method) in TOOL_REGISTRY.items()
    ]


def execute_tool(name, env, arguments):
    _desc, _schema, model_name, method_name = TOOL_REGISTRY[name]
    model = env[model_name].sudo()
    handler = getattr(model, method_name)
    return handler(arguments)
