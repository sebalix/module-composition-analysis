# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class OdooModuleBranchModel(models.Model):
    _name = "odoo.module.branch.model"
    _inherit = ["odoo.module.branch.model", "odoo.code.element.mixin"]

    def _get_next_version_identity_domain(self):
        """Domain matching the same model in the next module branch."""
        self.ensure_one()
        return [("odoo_model_id", "=", self.odoo_model_id.id)]

    def _get_next_odoo_version_model_domain(self):
        """Domain to find the same model on a later Odoo version.

        Follow module renames/replacements (via module timelines), and model
        renames (via code timelines).
        """
        self.ensure_one()
        # The model has been renamed or removed (code timeline)
        code_timeline = self.env["odoo.code.timeline"].search(
            [
                ("element_type", "=", "model"),
                ("model_id", "=", self.id),
            ],
            limit=1,
        )
        if code_timeline:
            if code_timeline.state == "removed":
                # The model has been removed: no next version model
                return [("id", "=", False)]
            if code_timeline.next_model_id:
                return [("id", "=", code_timeline.next_model_id.id)]
        # Follow module renames/replacements
        next_module_branch = self.module_branch_id.next_odoo_version_module_branch_id
        if next_module_branch:
            return [
                ("module_branch_id", "=", next_module_branch.id),
                ("odoo_model_id", "=", self.odoo_model_id.id),
            ]
        return [
            ("odoo_version_sequence", ">=", self.odoo_version_id.next_id.sequence),
            ("odoo_model_id", "=", self.odoo_model_id.id),
        ]
