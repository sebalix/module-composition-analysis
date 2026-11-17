# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class OdooModuleBranchData(models.Model):
    _inherit = "odoo.module.branch.data"

    def _mcp_to_dict(self):
        """Convert the data element to a summary dictionary."""
        self.ensure_one()
        return {
            "element_type": "data",
            "name": self.name,
            "module": self.module_name,
            "version": self.odoo_version_id.name,
            "model": self.odoo_model_name,
            "org": self.org_id.name,
            "repository": self.repository_id.name,
            "xml_id": self.full_xml_id,
            "data_type": self.data_type,
        }

    def _mcp_get_details(self):
        """Convert the data element to a details dictionary."""
        self.ensure_one()
        return {
            "element_type": "data",
            "name": self.name,
            "module": self.module_name,
            "version": self.odoo_version_id.name,
            "model": self.odoo_model_name,
            "org": self.org_id.name,
            "repository": self.repository_id.name,
            "xml_id": self.full_xml_id,
            "data_type": self.data_type,
            "noupdate": self.noupdate,
            "loaded": self.loaded,
            "data_json": self.data_json,
            "data_xml": self.data_xml,
        }
