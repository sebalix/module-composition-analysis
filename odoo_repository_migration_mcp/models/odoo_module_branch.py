# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from pydantic import BaseModel, Field

from odoo import models

from odoo.addons.odoo_repository_mcp.utils import NullableStr, mcp_tool


class MigrationStatus(BaseModel):
    """Migration status of a module for a migration path."""

    source: str = Field(description="Source Odoo version.")
    target: str = Field(description="Target Odoo version.")
    status: str = Field(
        description=(
            "Migration status: fully_ported, migrate, port_commits, "
            "review_migration, replaced, removed, moved_to_standard, "
            "moved_to_oca or moved_to_generic."
        )
    )
    renamed_to: NullableStr = None
    replaced_by: NullableStr = None
    last_source_scanned_commit: NullableStr = None
    last_target_scanned_commit: NullableStr = None
    pr_url: NullableStr = None


class MigrationStatusInput(BaseModel):
    """Inputs of the `migration_get_module_status` tool."""

    module: str = Field(description="Module technical name.")
    source_version: str | None = Field(
        default=None,
        description=(
            "Filter by source Odoo version (e.g. '17.0'). "
            "All the known migration paths otherwise."
        ),
    )
    target_version: str | None = Field(
        default=None, description="Filter by target Odoo version (e.g. '18.0')."
    )
    repository: str | None = Field(
        default=None, description="Filter by repository ('name' or 'org/name')."
    )


class MigrationStatusOutput(BaseModel):
    """Output of the `migration_get_module_status` tool."""

    error: str | None = None
    migrations: list[MigrationStatus]


class MigrationData(BaseModel):
    """Migration scan data of a module for a migration path."""

    source_branch: str
    target_branch: str
    process: NullableStr = None
    results: dict | None = None
    last_source_scanned_commit: NullableStr = None
    last_target_scanned_commit: NullableStr = None
    state: str
    pr_url: NullableStr = None


class MigrationDataInput(BaseModel):
    """Inputs of the `migration_get_data` tool."""

    module: str = Field(description="Module technical name.")
    source_version: str = Field(description="Source Odoo version (e.g. '17.0').")
    target_version: str = Field(description="Target Odoo version (e.g. '18.0').")
    repository: str | None = Field(
        default=None,
        description=(
            "Restrict to one repository ('name' or 'org/name'). "
            "Required when several repositories host the module."
        ),
    )


class MigrationDataOutput(BaseModel):
    """Output of the `migration_get_data` tool."""

    error: str | None = None
    migration: MigrationData


class OdooModuleBranch(models.Model):
    _inherit = "odoo.module.branch"

    @mcp_tool(MigrationStatusInput, MigrationStatusOutput)
    def _ai_migration_get_module_status(
        self, module=None, source_version=None, target_version=None, repository=None
    ):
        """Get the migration status of a module for the known migration
        paths."""
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
                for migration in migrations
            ]
        }

    @mcp_tool(MigrationDataInput, MigrationDataOutput)
    def _ai_migration_get_data(
        self, module=None, source_version=None, target_version=None, repository=None
    ):
        """Get the migration scan data of a module for a migration path."""
        module_ = self._mcp_get_module(module)
        domain = [
            ("module_branch_id.module_id", "=", module_.id),
            ("source_branch_id", "=", self._mcp_get_branch(source_version).id),
            ("target_branch_id", "=", self._mcp_get_branch(target_version).id),
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
            repositories = ", ".join(migrations.mapped("repository_id.display_name"))
            raise ValueError(
                f"Module '{module}' has migration data in several repositories "
                f"from '{source_version}' to '{target_version}': {repositories}. "
                "Please specify the 'repository' input."
            )
        migration = migrations
        data = migration._to_dict()
        data["state"] = migration.state
        data["pr_url"] = migration.pr_url
        return {"migration": data}
