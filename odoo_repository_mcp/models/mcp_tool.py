import inspect
import json

from odoo import api, models

from ..tools.registry import register_tool

_HANDLER_PREFIX = "_handler_"
_PROPERTIES_PREFIX = "_properties_"


def _discover_tools(model_class):
    for attr_name in sorted(dir(model_class)):
        if not attr_name.startswith(_HANDLER_PREFIX):
            continue
        tool_name = attr_name[len(_HANDLER_PREFIX) :]
        handler = getattr(model_class, attr_name)
        if not callable(handler):
            continue
        description = inspect.getdoc(handler) or tool_name
        properties, required = _get_properties(model_class, tool_name)
        register_tool(
            name=tool_name,
            description=description,
            input_schema={
                "type": "object",
                "properties": properties,
                "required": required,
            },
            model_name=model_class._name,
            method_name=attr_name,
        )


def _get_properties(model_class, tool_name):
    method_name = f"{_PROPERTIES_PREFIX}{tool_name}"
    method = getattr(model_class, method_name, None)
    if method is None:
        return ({}, [])
    result = method(model_class)
    if isinstance(result, tuple) and len(result) == 2:
        return result
    return ({}, [])


class MCPTool(models.AbstractModel):
    _name = "mcp.tool"
    _description = "MCP Tool Handlers"

    @api.model
    def _register_hook(self):
        super()._register_hook()
        _discover_tools(type(self))

    def _properties_search_modules(self):
        return (
            {
                "query": {
                    "type": "string",
                    "description": "Search text for module name, title or summary.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results (default 20, max 50).",
                },
                "branch": {
                    "type": "string",
                    "description": (
                        "Filter by Odoo version, e.g. '18.0'. Leave empty for all."
                    ),
                },
            },
            ["query"],
        )

    def _handler_search_modules(self, arguments):
        """Search Odoo modules by technical name, title, or summary."""
        query = arguments["query"]
        limit = min(max(arguments.get("limit", 20), 1), 50)
        branch = arguments.get("branch", "")
        domain = [
            "|",
            "|",
            ("module_name", "ilike", query),
            ("title", "ilike", query),
            ("summary", "ilike", query),
        ]
        if branch:
            domain.append(("branch_name", "=", branch))
        records = (
            self.env["odoo.module.branch"]
            .sudo()
            .search_read(
                domain,
                fields=[
                    "id",
                    "module_name",
                    "title",
                    "summary",
                    "branch_name",
                    "repository_id",
                    "org_id",
                    "license_id",
                    "is_standard",
                    "is_enterprise",
                    "is_community",
                    "application",
                    "installable",
                ],
                limit=limit,
            )
        )
        return json.dumps(records, default=str)

    def _properties_get_module_details(self):
        return (
            {
                "module_id": {
                    "type": "integer",
                    "description": (
                        "The ID of the module branch record (from search_modules)."
                    ),
                },
            },
            ["module_id"],
        )

    def _handler_get_module_details(self, arguments):
        """Get detailed information about an Odoo module branch by its ID."""
        record = self.env["odoo.module.branch"].sudo().browse(arguments["module_id"])
        if not record.exists():
            return json.dumps(
                {"error": f"Module branch with ID {arguments['module_id']} not found."}
            )
        return json.dumps(
            {
                "id": record.id,
                "module_name": record.module_name,
                "title": record.title,
                "summary": record.summary,
                "version": record.version,
                "branch_name": record.branch_name,
                "repository_name": record.repository_id.name,
                "repository_url": record.repository_id.repo_url,
                "organization": record.org_id.name,
                "category": record.category_id.name,
                "license": record.license_id.name,
                "development_status": record.development_status_id.name,
                "authors": record.author_ids.mapped("name"),
                "maintainers": record.maintainer_ids.mapped("name"),
                "dependencies": record.dependency_ids.mapped("display_name"),
                "reverse_dependencies": record.reverse_dependency_ids.mapped(
                    "display_name"
                ),
                "dependency_level_global": record.global_dependency_level,
                "dependency_level_non_standard": record.non_std_dependency_level,
                "is_standard": record.is_standard,
                "is_enterprise": record.is_enterprise,
                "is_community": record.is_community,
                "application": record.application,
                "installable": record.installable,
                "auto_install": record.auto_install,
                "removed": record.removed,
                "pr_url": record.pr_url,
                "sloc_python": record.sloc_python,
                "sloc_xml": record.sloc_xml,
                "sloc_js": record.sloc_js,
                "sloc_css": record.sloc_css,
                "python_dependencies": record.python_dependency_ids.mapped("name"),
                "url": record.url,
            },
            default=str,
        )
