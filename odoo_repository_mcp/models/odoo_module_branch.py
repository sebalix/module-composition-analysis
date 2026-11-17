# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models

from odoo.addons.ai_tool.tools import aitool


def _to_json_data(data):
    """Convert Odoo data to JSON-friendly data (``False`` becomes ``None``)."""
    if isinstance(data, dict):
        return {key: _to_json_data(value) for key, value in data.items()}
    if isinstance(data, list | tuple):
        return [_to_json_data(value) for value in data]
    return None if data is False else data


class OdooModuleBranch(models.Model):
    _inherit = "odoo.module.branch"

    # ------------------------------------------------------------------
    # Shared glue for the MCP tools
    # ------------------------------------------------------------------

    def _mcp_get_branch(self, name):
        """Return the `odoo.branch` record matching a version name."""
        branch = self.env["odoo.branch"].search([("name", "=", name)], limit=1)
        if not branch:
            raise ValueError(f"Unknown Odoo version: '{name}'.")
        return branch

    def _mcp_get_module(self, name):
        """Return the `odoo.module` record matching a technical name."""
        module = self.env["odoo.module"].search([("name", "=", name)], limit=1)
        if not module:
            raise ValueError(f"Unknown module: '{name}'.")
        return module

    def _mcp_get_repository(self, name):
        """Return the `odoo.repository` record matching 'org/name' or 'name'."""
        repository = self.env["odoo.repository"]
        if "/" in name:
            org_name, _, repo_name = name.partition("/")
            repository = self.env["odoo.repository"]._find_from_org_and_name(
                org_name, repo_name
            )
        else:
            repositories = self.env["odoo.repository"].search([("name", "=", name)])
            if len(repositories) > 1:
                orgs = ", ".join(repositories.mapped("org_id.name"))
                raise ValueError(
                    f"Repository name '{name}' is ambiguous "
                    f"(used by organizations: {orgs}). "
                    "Use the 'org/name' format to disambiguate."
                )
            repository = repositories[:1]
        if not repository:
            raise ValueError(f"Unknown repository: '{name}'.")
        return repository

    def _mcp_get_category(self, name):
        """Return the `odoo.module.category` record matching a name."""
        category = self.env["odoo.module.category"].search(
            [("name", "=", name)], limit=1
        )
        if not category:
            raise ValueError(f"Unknown module category: '{name}'.")
        return category

    def _mcp_get_author(self, name):
        """Return the `odoo.author` record matching a name."""
        author = self.env["odoo.author"].search([("name", "=", name)], limit=1)
        if not author:
            raise ValueError(f"Unknown author: '{name}'.")
        return author

    def _mcp_get_module_branches(self, module, branch, repository=None):
        """Return the `odoo.module.branch` records of a module on a version.

        Orphaned modules (not bound to a repository yet) are excluded, as
        they carry no scanned data.
        """
        domain = [
            ("module_id", "=", module.id),
            ("branch_id", "=", branch.id),
        ]
        if repository:
            domain.append(
                ("repository_id", "=", self._mcp_get_repository(repository).id)
            )
        else:
            domain.append(("repository_id", "!=", False))
        return self.search(domain)

    def _mcp_get_pagination(self, limit=None, offset=None):
        """Return the sanitized 'limit'/'offset' pagination values."""
        try:
            limit = int(limit) if limit is not None else 20
            offset = int(offset) if offset is not None else 0
        except (TypeError, ValueError):
            raise ValueError("'limit' and 'offset' must be integers.") from None
        if limit < 1:
            raise ValueError("'limit' must be greater than 0.")
        if offset < 0:
            raise ValueError("'offset' must be greater than or equal to 0.")
        return limit, offset

    def _mcp_to_dict(self):
        """Convert module data to a summary dictionary (for search results)."""
        self.ensure_one()
        return _to_json_data(
            {
                "module": self.module_name,
                "version": self.branch_id.name,
                "org": self.org_id.name,
                "repository": self.repository_id.name,
                "title": self.title,
                "summary": self.summary,
                "category": self.category_id.name,
                "license": self.license_id.name,
                "authors": self.author_ids.mapped("name"),
                "development_status": self.development_status_id.name,
                "application": self.application,
                "installable": self.installable,
                "auto_install": self.auto_install,
                "removed": self.removed,
                "specific": self.specific,
                "is_standard": self.is_standard,
                "is_enterprise": self.is_enterprise,
                "is_community": self.is_community,
            }
        )

    def _mcp_to_dict_short(self):
        """Convert module data to a minimal dictionary (for dependency lists)."""
        self.ensure_one()
        return _to_json_data(
            {
                "module": self.module_name,
                "version": self.branch_id.name,
                "org": self.org_id.name,
                "repository": self.repository_id.name,
                "title": self.title,
            }
        )

    def _mcp_get_recursive_reverse_dependencies(self, domain=None, _visited=None):
        """Return all the reverse dependencies recursively.

        A domain can be applied to restrict the modules to return, e.g:

        >>> mod._mcp_get_recursive_reverse_dependencies(
        ...     [("org_id.name", "=", "OCA")]
        ... )

        This is the mirror of `_get_recursive_dependencies` for reverse
        dependencies.
        """
        # NOTE: Circular dependencies are allowed
        if not domain:
            domain = []
        if _visited is None:
            _visited = set()
        current_ids = set(self.ids)
        if current_ids.issubset(_visited):
            return self.browse()
        _visited |= current_ids
        # Apply domain and exclude self
        dependencies = (self.reverse_dependency_ids - self).filtered_domain(domain)
        dependency_ids = set(dependencies.ids)
        for dependency in dependencies:
            dependency_ids |= set(
                dependency._mcp_get_recursive_reverse_dependencies(domain, _visited)
                .filtered_domain(domain)
                .ids
            )
        return self.browse(dependency_ids)

    # ------------------------------------------------------------------
    # MCP tools
    # ------------------------------------------------------------------

    @aitool(
        input_schema={
            "name": {
                "type": "string",
                "description": "Module technical name (searched with 'ilike').",
            },
            "version": {
                "type": "string",
                "description": "Odoo version (e.g. '18.0').",
            },
            "org": {
                "type": "string",
                "description": "Organization owning the repository (e.g. 'OCA').",
            },
            "repository": {
                "type": "string",
                "description": "Repository name ('name' or 'org/name').",
            },
            "category": {
                "type": "string",
                "description": "Module category (e.g. 'Tools').",
            },
            "author": {
                "type": "string",
                "description": "Module author name.",
            },
            "limit": {
                "type": "integer",
                "description": "Number of modules to return (default: 20).",
            },
            "offset": {
                "type": "integer",
                "description": "Index of the first module to return (default: 0).",
            },
        },
        output_schema={
            "error": {"type": "string"},
            "total": {"type": "integer"},
            "modules": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "module": {"type": "string"},
                        "version": {"type": "string"},
                        "org": {"type": "string"},
                        "repository": {"type": "string"},
                        "title": {"type": "string"},
                        "summary": {"type": "string"},
                        "category": {"type": "string"},
                        "license": {"type": "string"},
                        "authors": {"type": "array", "items": {"type": "string"}},
                        "development_status": {"type": "string"},
                        "application": {"type": "boolean"},
                        "installable": {"type": "boolean"},
                        "auto_install": {"type": "boolean"},
                        "removed": {"type": "boolean"},
                        "specific": {"type": "boolean"},
                        "is_standard": {"type": "boolean"},
                        "is_enterprise": {"type": "boolean"},
                        "is_community": {"type": "boolean"},
                    },
                },
            },
        },
    )
    def _ai_module_search(
        self,
        name=None,
        version=None,
        org=None,
        repository=None,
        category=None,
        author=None,
        limit=None,
        offset=None,
    ):
        """Search the modules collected from the scanned repositories."""
        try:
            domain = [
                ("repository_id", "!=", False),
                ("branch_id", "!=", False),
            ]
            if name:
                domain.append(("module_name", "ilike", name))
            if version:
                domain.append(("branch_id", "=", self._mcp_get_branch(version).id))
            if org:
                domain.append(
                    ("org_id", "=", self.env["odoo.repository"]._mcp_get_org(org).id)
                )
            if repository:
                domain.append(
                    ("repository_id", "=", self._mcp_get_repository(repository).id)
                )
            if category:
                domain.append(("category_id", "=", self._mcp_get_category(category).id))
            if author:
                domain.append(("author_ids", "=", self._mcp_get_author(author).id))
            limit, offset = self._mcp_get_pagination(limit, offset)
            total = self.search_count(domain)
            module_branches = self.search(domain, limit=limit, offset=offset)
            return {
                "total": total,
                "modules": [mb._mcp_to_dict() for mb in module_branches],
            }
        except ValueError as error:
            return {"error": str(error)}

    @aitool(
        input_schema={
            "module": {
                "type": "string",
                "description": "Module technical name.",
            },
            "version": {
                "type": "string",
                "description": "Odoo version (e.g. '18.0').",
            },
            "repository": {
                "type": "string",
                "description": (
                    "Restrict to one repository ('name' or 'org/name'). "
                    "All the repositories hosting the module otherwise."
                ),
            },
        },
        required_inputs=["module", "version"],
        output_schema={
            "error": {"type": "string"},
            "modules": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "module": {"type": "string"},
                        # Odoo version (key kept as 'branch' to align with
                        # the odoo_repository exchange format)
                        "branch": {"type": "string"},
                        "repository": {"type": "object"},
                        "title": {"type": "string"},
                        "summary": {"type": "string"},
                        "authors": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "maintainers": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "depends": {"type": "array", "items": {"type": "string"}},
                        "category": {"type": "string"},
                        "license": {"type": "string"},
                        "version": {"type": "string"},
                        "versions": {
                            "type": "array",
                            "items": {"type": "object"},
                        },
                        "development_status": {"type": "string"},
                        "application": {"type": "boolean"},
                        "installable": {"type": "boolean"},
                        "auto_install": {"type": "boolean"},
                        "external_dependencies": {"type": "object"},
                        "is_standard": {"type": "boolean"},
                        "is_enterprise": {"type": "boolean"},
                        "is_community": {"type": "boolean"},
                        "sloc_python": {"type": "integer"},
                        "sloc_xml": {"type": "integer"},
                        "sloc_js": {"type": "integer"},
                        "sloc_css": {"type": "integer"},
                        "last_scanned_commit": {"type": "string"},
                        "addons_path": {"type": "string"},
                        "pr_url": {"type": "string"},
                        "url": {"type": "string"},
                    },
                },
            },
        },
    )
    def _ai_module_get_details(self, module=None, version=None, repository=None):
        """Get the full details of a module for a given Odoo version.

        The same module can be hosted by several repositories: one entry
        is returned per hosting repository.
        """
        try:
            if not module or not version:
                raise ValueError("'module' and 'version' are required inputs.")
            branch = self._mcp_get_branch(version)
            module_ = self._mcp_get_module(module)
            module_branches = self._mcp_get_module_branches(
                module_, branch, repository=repository
            )
            if not module_branches:
                raise ValueError(
                    f"Module '{module}' not found for Odoo version '{version}'."
                )
            modules = []
            for module_branch in module_branches:
                data = module_branch._to_dict()
                data["url"] = module_branch.url
                modules.append(_to_json_data(data))
            return {"modules": modules}
        except ValueError as error:
            return {"error": str(error)}

    @aitool(
        input_schema={
            "module": {
                "type": "string",
                "description": "Module technical name.",
            },
            "version": {
                "type": "string",
                "description": "Odoo version (e.g. '18.0').",
            },
            "repository": {
                "type": "string",
                "description": (
                    "Restrict to one repository ('name' or 'org/name'). "
                    "Required when several repositories host the module."
                ),
            },
            "direction": {
                "type": "string",
                "enum": ["depends", "reverse"],
                "description": (
                    "'depends' (default) for the dependencies of the module, "
                    "'reverse' for the modules depending on it."
                ),
            },
            "scope": {
                "type": "string",
                "enum": ["direct", "recursive"],
                "description": "'direct' (default) or 'recursive'.",
            },
            "org": {
                "type": "string",
                "description": "Filter the modules by organization (e.g. 'OCA').",
            },
            "limit": {
                "type": "integer",
                "description": "Number of modules to return (default: 20).",
            },
            "offset": {
                "type": "integer",
                "description": "Index of the first module to return (default: 0).",
            },
        },
        required_inputs=["module", "version"],
        output_schema={
            "error": {"type": "string"},
            "total": {"type": "integer"},
            "dependencies": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "module": {"type": "string"},
                        "version": {"type": "string"},
                        "org": {"type": "string"},
                        "repository": {"type": "string"},
                        "title": {"type": "string"},
                    },
                },
            },
        },
    )
    def _ai_module_get_dependencies(
        self,
        module=None,
        version=None,
        repository=None,
        direction=None,
        scope=None,
        org=None,
        limit=None,
        offset=None,
    ):
        """Get the dependencies of a module for a given Odoo version."""
        try:
            if not module or not version:
                raise ValueError("'module' and 'version' are required inputs.")
            if direction not in (None, "depends", "reverse"):
                raise ValueError(
                    f"Invalid 'direction' value: '{direction}' "
                    "(expected 'depends' or 'reverse')."
                )
            if scope not in (None, "direct", "recursive"):
                raise ValueError(
                    f"Invalid 'scope' value: '{scope}' "
                    "(expected 'direct' or 'recursive')."
                )
            direction = direction or "depends"
            scope = scope or "direct"
            branch = self._mcp_get_branch(version)
            module_ = self._mcp_get_module(module)
            module_branches = self._mcp_get_module_branches(
                module_, branch, repository=repository
            )
            if not module_branches:
                raise ValueError(
                    f"Module '{module}' not found for Odoo version '{version}'."
                )
            if len(module_branches) > 1:
                repositories = ", ".join(
                    module_branches.mapped("repository_id.display_name")
                )
                raise ValueError(
                    f"Module '{module}' is hosted by several repositories "
                    f"for Odoo version '{version}': {repositories}. "
                    "Please specify the 'repository' input."
                )
            module_branch = module_branches
            if direction == "reverse":
                if scope == "recursive":
                    dependencies = (
                        module_branch._mcp_get_recursive_reverse_dependencies()
                    )
                else:
                    dependencies = module_branch.reverse_dependency_ids
            elif scope == "recursive":
                dependencies = module_branch._get_recursive_dependencies()
            else:
                dependencies = module_branch.dependency_ids
            if org:
                dependencies = dependencies.filtered_domain(
                    [("org_id", "=", self.env["odoo.repository"]._mcp_get_org(org).id)]
                )
            dependencies = dependencies.sorted("module_name")
            limit, offset = self._mcp_get_pagination(limit, offset)
            return {
                "total": len(dependencies),
                "dependencies": [
                    dependency._mcp_to_dict_short()
                    for dependency in dependencies[offset : offset + limit]
                ],
            }
        except ValueError as error:
            return {"error": str(error)}

    @aitool(
        input_schema={
            "module": {
                "type": "string",
                "description": "Module technical name.",
            },
        },
        required_inputs=["module"],
        output_schema={
            "error": {"type": "string"},
            "versions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "version": {"type": "string"},
                        "org": {"type": "string"},
                        "repository": {"type": "string"},
                        "manifest_version": {"type": "string"},
                        "commit": {"type": "string"},
                        "has_migration_script": {"type": "boolean"},
                    },
                },
            },
        },
    )
    def _ai_module_list_versions(self, module=None):
        """List the versions of a module across the Odoo versions and
        repositories."""
        try:
            if not module:
                raise ValueError("'module' is a required input.")
            module_ = self._mcp_get_module(module)
            module_branches = self.search(
                [
                    ("module_id", "=", module_.id),
                    ("repository_id", "!=", False),
                ]
            )
            versions = []
            for module_branch in module_branches:
                for version in module_branch.version_ids:
                    versions.append(
                        {
                            "version": module_branch.branch_id.name,
                            "org": module_branch.org_id.name,
                            "repository": module_branch.repository_id.name,
                            "manifest_version": version.manifest_value,
                            "commit": version.commit,
                            "has_migration_script": version.has_migration_script,
                        }
                    )
            return {"versions": _to_json_data(versions)}
        except ValueError as error:
            return {"error": str(error)}
