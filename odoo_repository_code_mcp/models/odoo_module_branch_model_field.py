# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class OdooModuleBranchModelField(models.Model):
    _inherit = "odoo.module.branch.model.field"

    def _mcp_to_dict(self):
        """Convert the field element to a summary dictionary."""
        self.ensure_one()
        return {
            "element_type": "field",
            "name": self.name,
            "module": self.module_name,
            "version": self.odoo_version_id.name,
            "model": self.odoo_model_name,
            "org": self.org_id.name,
            "repository": self.repository_id.name,
            "field_type": self.field_type,
            "comodel_name": self.comodel_name,
        }

    def _mcp_get_details(self):
        """Convert the field element to a details dictionary."""
        self.ensure_one()
        return {
            "element_type": "field",
            "name": self.name,
            "module": self.module_name,
            "version": self.odoo_version_id.name,
            "model": self.odoo_model_name,
            "org": self.org_id.name,
            "repository": self.repository_id.name,
            "field_type": self.field_type,
            "comodel_name": self.comodel_name,
            "is_relational": self.is_relational,
            "inverse_method": self.inverse_method,
            "search_method": self.search_method,
            "code": self.code,
        }
