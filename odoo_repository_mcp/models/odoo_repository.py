# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from pydantic import BaseModel, Field

from odoo import models

from ..utils import mcp_tool


class RepositorySummary(BaseModel):
    """Repository scanned by the Odoo MCA."""

    org: str = Field(description="Organization owning the repository.")
    name: str = Field(description="Repository name.")
    branches: list[str] = Field(description="Odoo versions available.")
    specific: bool = Field(
        description="Whether the repository hosts project-specific modules."
    )


class RepoListRepositoriesInput(BaseModel):
    """Inputs of the `repo_list_repositories` tool."""

    org: str | None = Field(
        default=None, description="Filter by organization name (e.g. 'OCA')."
    )


class RepoListRepositoriesOutput(BaseModel):
    """Output of the `repo_list_repositories` tool."""

    error: str | None = None
    repositories: list[RepositorySummary]


class OdooRepository(models.Model):
    _inherit = "odoo.repository"

    # ------------------------------------------------------------------
    # Shared glue for the MCP tools
    # ------------------------------------------------------------------

    def _mcp_get_org(self, name):
        """Return the `odoo.repository.org` record matching a name."""
        org = self.env["odoo.repository.org"].search([("name", "=", name)], limit=1)
        if not org:
            raise ValueError(f"Unknown organization: '{name}'.")
        return org

    # ------------------------------------------------------------------
    # MCP tools
    # ------------------------------------------------------------------

    @mcp_tool(RepoListRepositoriesInput, RepoListRepositoriesOutput)
    def _ai_repo_list_repositories(self, org=None):
        """List the organizations and repositories scanned by the Odoo MCA."""
        domain = []
        if org:
            domain.append(("org_id", "=", self._mcp_get_org(org).id))
        return {
            "repositories": [
                {
                    "org": repository.org_id.name,
                    "name": repository.name,
                    "branches": repository.branch_ids.mapped("branch_id.name"),
                    "specific": repository.specific,
                }
                for repository in self.search(domain)
            ]
        }
