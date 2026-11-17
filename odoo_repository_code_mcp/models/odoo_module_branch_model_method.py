# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class OdooModuleBranchModelMethod(models.Model):
    _inherit = "odoo.module.branch.model.method"

    def _mcp_to_dict(self):
        """Convert the method element to a summary dictionary."""
        self.ensure_one()
        return {
            "element_type": "method",
            "name": self.name,
            "module": self.module_name,
            "version": self.odoo_version_id.name,
            "model": self.odoo_model_name,
            "org": self.org_id.name,
            "repository": self.repository_id.name,
            "signature": self.signature,
        }

    def _mcp_get_details(self):
        """Convert the method element to a details dictionary."""
        self.ensure_one()
        return {
            "element_type": "method",
            "name": self.name,
            "module": self.module_name,
            "version": self.odoo_version_id.name,
            "model": self.odoo_model_name,
            "org": self.org_id.name,
            "repository": self.repository_id.name,
            "signature": self.signature,
            "code": self.code,
        }
