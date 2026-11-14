# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class OdooModuleBranchModelMethod(models.Model):
    _name = "odoo.module.branch.model.method"
    _inherit = ["odoo.module.branch.model.method", "odoo.code.element.mixin"]

    next_odoo_version_method_id = fields.Many2one(
        comodel_name="odoo.module.branch.model.method",
        compute="_compute_next_odoo_version_method_id",
        string="Next Odoo Version Method",
    )

    @api.depends(
        "module_branch_id",
        "module_branch_id.branch_id.next_id",
        "module_branch_id.timeline_ids.next_module_id",
        "module_branch_model_id.next_version_state",
        "module_branch_model_id.next_odoo_version_model_id",
    )
    def _compute_next_version_state(self):
        return super()._compute_next_version_state()

    def _get_next_version_state_from_lineage(self):
        """State of the method when no code timeline declares it.

        The method follows its model: it is searched on the next version
        record of the model (which follows the model renames and the module
        renames/replacements).
        """
        self.ensure_one()
        if self.module_branch_model_id.next_version_state == "unknown":
            return "unknown"
        next_model = self.module_branch_model_id.next_odoo_version_model_id
        if not next_model:
            # The model is not available in the next version: the method neither
            return "removed"
        exists = self.search_count(
            [
                ("module_branch_model_id", "=", next_model.id),
                ("name", "=", self.name),
            ]
        )
        return "available" if exists else "removed"

    @api.depends("odoo_version_id.next_id")
    def _compute_next_odoo_version_method_id(self):
        for rec in self:
            rec.next_odoo_version_method_id = False
            if not rec.odoo_version_id.next_id:
                continue
            rec.next_odoo_version_method_id = self.search(
                rec._get_next_odoo_version_method_domain(),
                order="odoo_version_id,global_dependency_level",
                limit=1,
            )

    def _get_next_odoo_version_method_domain(self):
        """Domain to find the same method on a later Odoo version.

        Hook for extension — follows the method renames (code timelines), and
        the next version record of its model (model renames and module
        renames/replacements included).
        """
        self.ensure_one()
        # The method has been renamed or removed (code timeline)
        code_timeline = self.env["odoo.code.timeline"].search(
            [
                ("element_type", "=", "method"),
                ("method_id", "=", self.id),
            ],
            limit=1,
        )
        if code_timeline:
            if code_timeline.state == "removed":
                # The method has been removed: no next version method
                return [("id", "=", False)]
            if code_timeline.next_method_id:
                return [("id", "=", code_timeline.next_method_id.id)]
        # Follow the model's next version record
        next_model = self.module_branch_model_id.next_odoo_version_model_id
        if not next_model:
            return [("id", "=", False)]
        return [
            ("module_branch_model_id", "=", next_model.id),
            ("name", "=", self.name),
        ]
