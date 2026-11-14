# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class OdooModuleBranchModelMethod(models.Model):
    _name = "odoo.module.branch.model.method"
    _inherit = ["odoo.module.branch.model.method", "odoo.code.model.element.mixin"]

    next_odoo_version_method_id = fields.Many2one(
        comodel_name="odoo.module.branch.model.method",
        compute="_compute_next_odoo_version_method_id",
        string="Next Odoo Version Method",
    )
    timeline_ids = fields.One2many(
        comodel_name="odoo.code.timeline",
        inverse_name="method_id",
        string="Timelines",
    )
    timeline_id = fields.Many2one(
        comodel_name="odoo.code.timeline",
        string="Timeline",
        compute="_compute_timeline_id",
        help="Confirmed timeline declaring what this element became in the next "
        "version.",
    )
    model_timeline_id = fields.Many2one(
        comodel_name="odoo.code.timeline",
        related="module_branch_model_id.timeline_id",
        string="Model timeline",
        readonly=True,
    )

    @api.depends("timeline_ids.state")
    def _compute_timeline_id(self):
        for rec in self:
            rec.timeline_id = rec.timeline_ids.filtered(
                lambda timeline: timeline.state == "confirmed"
            )[:1]

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

        Follows the method renames (code timelines), and the next version record
        of its model (model renames and module renames/replacements included).
        """
        self.ensure_one()
        # The method has been renamed or removed
        code_timeline = self.env["odoo.code.timeline"].search(
            [
                ("state", "=", "confirmed"),
                ("element_type", "=", "method"),
                ("method_id", "=", self.id),
            ],
            limit=1,
        )
        if code_timeline:
            if code_timeline.timeline_type == "removed":
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
