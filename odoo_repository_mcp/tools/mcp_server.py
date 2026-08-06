from mcp.server import MCPServer

mcp = MCPServer(
    name="odoo-repository-mca",
    title="Odoo MCA Repository",
    description=(
        "Query Odoo modules data from the Module Composition Analysis database."
    ),
    version="1.0.0",
    log_level="WARNING",
)

_env = None


def set_odoo_env(env):
    global _env
    _env = env


def get_odoo_env():
    return _env
