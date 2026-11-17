# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models

from odoo.addons.ai_tool.tools import aitool
from odoo.addons.odoo_repository_mcp.models.odoo_module_branch import _to_json_data


class OdooModuleBranch(models.Model):
    _inherit = "odoo.module.branch"

    @aitool(
        input_schema={
            "module": {
                "type": "string",
                "description": "Module technical name.",
            },
            "source_version": {
                "type": "string",
                "description": (
                    "Filter by source Odoo version (e.g. '17.0'). "
                    "All the known migration paths otherwise."
                ),
            },
            "target_version": {
                "type": "string",
                "description": "Filter by target Odoo version (e.g. '18.0').",
            },
            "repository": {
                "type": "string",
                "description": "Filter by repository ('name' or 'org/name').",
            },
        },
        required_inputs=["module"],
        output_schema={
            "error": {"type": "string"},
            "migrations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "source": {"type": "string"},
                        "target": {"type": "string"},
                        "status": {"type": "string"},
                        "renamed_to": {"type": "string"},
                        "replaced_by": {"type": "string"},
                        "last_source_scanned_commit": {"type": "string"},
                        "last_target_scanned_commit": {"type": "string"},
                        "pr_url": {"type": "string"},
                    },
                },
            },
        },
    )
    def _ai_migration_get_module_status(
        self, module=None, source_version=None, target_version=None, repository=None
    ):
        """Get the migration status of a module for the known migration
        paths."""
        try:
            if not module:
                raise ValueError("'module' is a required input.")
            module_ = self._mcp_get_module(module)
            domain = [("module_branch_id.module_id", "=", module_.id)]
            if source_version:
                domain.append(
                    ("source_branch_id", "=", self._mcp_get_branch(source_version).id)
                )
            if target_version:
                domain.append(
                    ("target_branch_id", "=", self._mcp_get_branch(target_version).id)
                )
            if repository:
                domain.append(
                    ("repository_id", "=", self._mcp_get_repository(repository).id)
                )
            migrations = self.env["odoo.module.branch.migration"].search(domain)
            return {
                "migrations": [
                    _to_json_data(
                        {
                            "source": migration.source_branch_id.name,
                            "target": migration.target_branch_id.name,
                            "status": migration.state,
                            "renamed_to": migration.renamed_to_module_id.name,
                            "replaced_by": migration.replaced_by_module_id.name,
                            "last_source_scanned_commit": (
                                migration.last_source_scanned_commit
                            ),
                            "last_target_scanned_commit": (
                                migration.last_target_scanned_commit
                            ),
                            "pr_url": migration.pr_url,
                        }
                    )
                    for migration in migrations
                ]
            }
        except ValueError as error:
            return {"error": str(error)}

    @aitool(
        input_schema={
            "module": {
                "type": "string",
                "description": "Module technical name.",
            },
            "source_version": {
                "type": "string",
                "description": "Source Odoo version (e.g. '17.0').",
            },
            "target_version": {
                "type": "string",
                "description": "Target Odoo version (e.g. '18.0').",
            },
            "repository": {
                "type": "string",
                "description": (
                    "Restrict to one repository ('name' or 'org/name'). "
                    "Required when several repositories host the module."
                ),
            },
        },
        required_inputs=["module", "source_version", "target_version"],
        output_schema={
            "error": {"type": "string"},
            "migration": {
                "type": "object",
                "properties": {
                    "source_branch": {"type": "string"},
                    "target_branch": {"type": "string"},
                    "process": {"type": "string"},
                    "results": {"type": "object"},
                    "last_source_scanned_commit": {"type": "string"},
                    "last_target_scanned_commit": {"type": "string"},
                    "state": {"type": "string"},
                    "pr_url": {"type": "string"},
                },
            },
        },
    )
    def _ai_migration_get_data(
        self, module=None, source_version=None, target_version=None, repository=None
    ):
        """Get the migration scan data of a module for a migration path."""
        try:
            if not module or not source_version or not target_version:
                raise ValueError(
                    "'module', 'source_version' and 'target_version' "
                    "are required inputs."
                )
            module_ = self._mcp_get_module(module)
            domain = [
                ("module_branch_id.module_id", "=", module_.id),
                (
                    "source_branch_id",
                    "=",
                    self._mcp_get_branch(source_version).id,
                ),
                (
                    "target_branch_id",
                    "=",
                    self._mcp_get_branch(target_version).id,
                ),
            ]
            if repository:
                domain.append(
                    ("repository_id", "=", self._mcp_get_repository(repository).id)
                )
            migrations = self.env["odoo.module.branch.migration"].search(domain)
            if not migrations:
                raise ValueError(
                    f"No migration data for module '{module}' from "
                    f"'{source_version}' to '{target_version}'."
                )
            if len(migrations) > 1:
                repositories = ", ".join(
                    migrations.mapped("repository_id.display_name")
                )
                raise ValueError(
                    f"Module '{module}' has migration data in several "
                    f"repositories from '{source_version}' to "
                    f"'{target_version}': {repositories}. "
                    "Please specify the 'repository' input."
                )
            migration = migrations
            data = migration._to_dict()
            data["state"] = migration.state
            data["pr_url"] = migration.pr_url
            return {"migration": _to_json_data(data)}
        except ValueError as error:
            return {"error": str(error)}
