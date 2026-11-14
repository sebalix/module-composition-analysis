# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class OdooCodeElementMixin(models.AbstractModel):
    """Mixin shared by the code elements having a 'next_version_state'.

    The state is stored (searchable) and refreshed:
    - on creation (usually 'unknown': the next version is not scanned yet),
    - when the module structure changes (branch or module timelines), through
      the compute dependencies,
    - when the code of the next version changes (scan), by the hook on the
      module branch,
    - by a daily cron reclassifying the elements still in the 'unknown' state
      (safety net).
    """

    _name = "odoo.code.element.mixin"
    _description = "Odoo Code Element Mixin"

    next_version_state = fields.Selection(
        selection=[
            ("unknown", "Unknown"),
            ("available", "Available"),
            ("removed", "Removed"),
        ],
        compute="_compute_next_version_state",
        store=True,
        help="Whether this element still exists in the next Odoo version "
        "of the module.",
    )

    @api.depends(
        "module_branch_id",
        "module_branch_id.branch_id.next_id",
        "module_branch_id.timeline_ids.next_module_id",
    )
    def _compute_next_version_state(self):
        for rec in self:
            rec.next_version_state = rec._get_next_version_state()

    def _get_next_version_state(self):
        self.ensure_one()
        # Renamed/removed declaration (code timeline): the state is known
        # even if the next version of the module is not scanned yet, as the
        # timeline targets an existing element
        timeline = self.env["odoo.code.timeline"].search(
            [(self._get_code_timeline_element_field(), "=", self.id)], limit=1
        )
        if timeline:
            if timeline.state == "removed":
                return "removed"
            if timeline._get_next_element():
                return "available"
        return self._get_next_version_state_from_lineage()

    def _get_next_version_state_from_lineage(self):
        """State of the element when no code timeline declares it, based on
        the next version of its module."""
        self.ensure_one()
        next_module_branch = self.module_branch_id.next_odoo_version_module_branch_id
        if not next_module_branch:
            return "unknown"
        exists = self.env[self._name].search_count(
            [("module_branch_id", "=", next_module_branch.id)]
            + self._get_next_version_identity_domain()
        )
        return "available" if exists else "removed"

    def _get_next_version_identity_domain(self):
        """Domain matching the same element in the next module branch."""
        self.ensure_one()
        raise NotImplementedError()

    def _get_code_timeline_element_field(self):
        """Return the field of 'odoo.code.timeline' linking this element."""
        self.ensure_one()
        element_type = self.env["odoo.code.timeline"]._get_element_type(self._name)
        return f"{element_type}_id"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # The new elements may complete the next version of a module: refresh
        # the state of the elements of the previous module branches
        records.module_branch_id._refresh_next_version_state_of_previous_branches()
        return records

    def write(self, vals):
        res = super().write(vals)
        if "active" in vals:
            # Archiving/unarchiving an element changes the state of the
            # elements of the previous module branches
            self.module_branch_id._refresh_next_version_state_of_previous_branches()
        return res
