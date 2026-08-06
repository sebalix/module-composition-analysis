import json

from .mcp_server import get_odoo_env, mcp


def _get_model():
    env = get_odoo_env()
    return env["odoo.module.branch"].sudo()


@mcp.tool()
def search_modules(
    query: str,
    limit: int = 20,
    branch: str = "",
) -> str:
    """Search Odoo modules by technical name, title, or summary.

    Args:
        query: Search text to match against module name, title or summary.
        limit: Maximum number of results to return (default 20, max 50).
        branch: Filter by Odoo version (e.g. "18.0"). Leave empty for all versions.
    """
    domain = [
        "|",
        "|",
        ("module_name", "ilike", query),
        ("title", "ilike", query),
        ("summary", "ilike", query),
    ]
    if branch:
        domain.append(("branch_name", "=", branch))
    limit = min(max(limit, 1), 50)
    records = _get_model().search_read(
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
    return json.dumps(records, default=str)


@mcp.tool()
def get_module_details(module_id: int) -> str:
    """Get detailed information about an Odoo module branch by its ID.

    Use the ID returned by search_modules. Returns full details including
    dependencies, versions, source lines of code, and repository information.

    Args:
        module_id: The ID of the module branch record (from search_modules).
    """
    record = _get_model().browse(module_id)
    if not record.exists():
        return json.dumps({"error": f"Module branch with ID {module_id} not found."})
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
