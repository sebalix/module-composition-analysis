# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class OdooModuleBranchModel(models.Model):
    _inherit = "odoo.module.branch.model"

    def _mcp_to_dict(self):
        """Convert the model element to a summary dictionary."""
        self.ensure_one()
        return {
            "element_type": "model",
            "name": self.odoo_model_name,
            "module": self.module_name,
            "version": self.odoo_version_id.name,
            "model": None,
            "org": self.org_id.name,
            "repository": self.repository_id.name,
            "model_type": self.model_type,
        }

    def _mcp_get_details(self):
        """Convert the model element to a details dictionary."""
        self.ensure_one()
        data = self._to_dict()
        return {
            "element_type": "model",
            "name": self.odoo_model_name,
            "module": self.module_name,
            "version": self.odoo_version_id.name,
            "model": None,
            "org": self.org_id.name,
            "repository": self.repository_id.name,
            "model_type": data["type"],
            "order": data["order"],
            "inherit": data["inherit"],
            "inherits": data["inherits"],
            "fields": data["fields"],
            "methods": data["methods"],
        }
