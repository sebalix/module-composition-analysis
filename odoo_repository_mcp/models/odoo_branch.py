# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models

from odoo.addons.ai_tool.tools import aitool


class OdooBranch(models.Model):
    _inherit = "odoo.branch"

    @aitool(
        input_schema={},
        output_schema={
            "error": {"type": "string"},
            "versions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "next": {"type": "string"},
                        "previous": {"type": "string"},
                    },
                },
            },
        },
    )
    def _ai_repo_list_versions(self):
        """List the Odoo versions known to the database."""
        return {
            "versions": [
                {
                    "name": branch.name,
                    "next": branch.next_id.name or None,
                    "previous": branch.previous_id.name or None,
                }
                for branch in self.search([])
            ]
        }
