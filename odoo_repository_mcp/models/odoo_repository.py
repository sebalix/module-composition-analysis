# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models

from odoo.addons.ai_tool.tools import aitool


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

    @aitool(
        input_schema={
            "org": {
                "type": "string",
                "description": "Filter by organization name (e.g. 'OCA').",
            },
        },
        output_schema={
            "error": {"type": "string"},
            "repositories": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "org": {"type": "string"},
                        "name": {"type": "string"},
                        "branches": {"type": "array", "items": {"type": "string"}},
                        "specific": {"type": "boolean"},
                    },
                },
            },
        },
    )
    def _ai_repo_list_repositories(self, org=None):
        """List the organizations and repositories scanned by the Odoo MCA."""
        try:
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
        except ValueError as error:
            return {"error": str(error)}
