# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class OdooModuleBranchModelField(models.Model):
    _inherit = "odoo.module.branch.model.field"

    def _mcp_to_element_dict(self):
        """Convert the field element to a reference dictionary."""
        self.ensure_one()
        return {
            "element_type": "field",
            "module": self.module_name,
            "version": self.odoo_version_id.name,
            "model": self.odoo_model_name,
            "name": self.name,
        }

    def _mcp_get_next_version_element(self):
        """Return the next Odoo version counterpart of the field element."""
        self.ensure_one()
        return self.next_odoo_version_field_id
