# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class OdooModuleBranchData(models.Model):
    _name = "odoo.module.branch.data"
    _inherit = ["odoo.module.branch.data", "odoo.code.element.mixin"]

    next_odoo_version_data_id = fields.Many2one(
        comodel_name="odoo.module.branch.data",
        compute="_compute_next_odoo_version_data_id",
        string="Next Odoo Version Data",
    )

    def _get_next_version_identity_domain(self):
        """Domain matching the same data in the next module branch."""
        self.ensure_one()
        return [("xml_id", "=", self.xml_id)]

    @api.depends("odoo_version_id.next_id")
    def _compute_next_odoo_version_data_id(self):
        for rec in self:
            rec.next_odoo_version_data_id = False
            if not rec.odoo_version_id.next_id:
                continue
            rec.next_odoo_version_data_id = self.search(
                rec._get_next_odoo_version_data_domain(),
                order="odoo_version_id,global_dependency_level",
                limit=1,
            )

    def _get_next_odoo_version_data_domain(self):
        """Domain to find the same data on a later Odoo version.

        Hook for extension — follows module renames/replacements and data
        renames.
        """
        self.ensure_one()
        # The data has been renamed or removed (code timeline)
        code_timeline = self.env["odoo.code.timeline"].search(
            [
                ("element_type", "=", "data"),
                ("data_id", "=", self.id),
            ],
            limit=1,
        )
        if code_timeline:
            if code_timeline.state == "removed":
                # The data has been removed: no next version data
                return [("id", "=", False)]
            if code_timeline.next_data_id:
                return [("id", "=", code_timeline.next_data_id.id)]
        # Follow module renames/replacements
        next_module_branch = self.module_branch_id.next_odoo_version_module_branch_id
        if next_module_branch:
            return [
                ("module_branch_id", "=", next_module_branch.id),
                ("xml_id", "=", self.xml_id),
            ]
        return [
            (
                "module_branch_id.branch_id.sequence",
                ">=",
                self.odoo_version_id.next_id.sequence,
            ),
            ("module_id", "=", self.module_id.id),
            ("xml_id", "=", self.xml_id),
        ]
