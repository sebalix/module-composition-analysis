# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class OdooModuleBranchModelField(models.Model):
    _name = "odoo.module.branch.model.field"
    _inherit = ["odoo.module.branch.model.field", "odoo.code.element.mixin"]

    next_odoo_version_field_id = fields.Many2one(
        comodel_name="odoo.module.branch.model.field",
        compute="_compute_next_odoo_version_field_id",
        string="Next Odoo Version Field",
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
        """State of the field when no code timeline declares it.

        The field follows its model: it is searched on the next version
        record of the model (which follows the model renames and the module
        renames/replacements).
        """
        self.ensure_one()
        if self.module_branch_model_id.next_version_state == "unknown":
            return "unknown"
        next_model = self.module_branch_model_id.next_odoo_version_model_id
        if not next_model:
            # The model is not available in the next version: the field neither
            return "removed"
        exists = self.search_count(
            [
                ("module_branch_model_id", "=", next_model.id),
                ("name", "=", self.name),
            ]
        )
        return "available" if exists else "removed"

    @api.depends("odoo_version_id.next_id")
    def _compute_next_odoo_version_field_id(self):
        for rec in self:
            rec.next_odoo_version_field_id = False
            if not rec.odoo_version_id.next_id:
                continue
            rec.next_odoo_version_field_id = self.search(
                rec._get_next_odoo_version_field_domain(),
                order="odoo_version_id,global_dependency_level",
                limit=1,
            )

    def _get_next_odoo_version_field_domain(self):
        """Domain to find the same field on a later Odoo version.

        Hook for extension — follows the field renames (code timelines), and
        the next version record of its model (model renames and module
        renames/replacements included).
        """
        self.ensure_one()
        # The field has been renamed or removed (code timeline)
        code_timeline = self.env["odoo.code.timeline"].search(
            [
                ("element_type", "=", "field"),
                ("field_id", "=", self.id),
            ],
            limit=1,
        )
        if code_timeline:
            if code_timeline.state == "removed":
                # The field has been removed: no next version field
                return [("id", "=", False)]
            if code_timeline.next_field_id:
                return [("id", "=", code_timeline.next_field_id.id)]
        # Follow the model's next version record
        next_model = self.module_branch_model_id.next_odoo_version_model_id
        if not next_model:
            return [("id", "=", False)]
        return [
            ("module_branch_model_id", "=", next_model.id),
            ("name", "=", self.name),
        ]
