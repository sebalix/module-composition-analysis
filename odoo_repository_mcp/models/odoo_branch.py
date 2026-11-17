# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from pydantic import BaseModel, Field

from odoo import models

from ..utils import NoInputs, NullableStr, mcp_tool


class VersionInfo(BaseModel):
    """Odoo version known to the database."""

    name: str = Field(description="Odoo version (e.g. '18.0').")
    next: NullableStr = None
    previous: NullableStr = None


class RepoVersionsOutput(BaseModel):
    """Output of the `repo_list_versions` tool."""

    error: str | None = None
    versions: list[VersionInfo]


class OdooBranch(models.Model):
    _inherit = "odoo.branch"

    @mcp_tool(NoInputs, RepoVersionsOutput)
    def _ai_repo_list_versions(self):
        """List the Odoo versions known to the database."""
        return {
            "versions": [
                {
                    "name": branch.name,
                    "next": branch.next_id.name,
                    "previous": branch.previous_id.name,
                }
                for branch in self.search([])
            ]
        }
