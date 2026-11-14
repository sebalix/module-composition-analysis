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

    The lineage resolution ('_get_next_version_state_from_lineage') relies on
    the next version of the module; the elements attached to a model (fields,
    methods) override it to resolve through the state of their model instead
    (see 'odoo.code.model.element.mixin'): keep in mind that changes brought
    here (e.g. the repository readiness checks) reach these elements through
    'module_branch_model_id.next_version_state'.
    """

    _name = "odoo.code.element.mixin"
    _description = "Odoo Code Element Mixin"

    next_version_state = fields.Selection(
        selection=[
            ("unknown", "Unknown"),
            ("available", "Available"),
            ("absent", "Absent"),
        ],
        compute="_compute_next_version_state",
        store=True,
        help="Whether this element is present in the next scanned Odoo "
        "version of the module.",
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
            [
                ("state", "=", "confirmed"),
                (self._get_code_timeline_element_field(), "=", self.id),
            ],
            limit=1,
        )
        if timeline:
            if timeline.timeline_type == "removed":
                return "absent"
            if timeline._get_next_element():
                return "available"
        return self._get_next_version_state_from_lineage()

    def _get_next_version_state_from_lineage(self):
        """State of the element when no code timeline declares it, based on
        the next version of its module."""
        self.ensure_one()
        next_module_branch = self.module_branch_id.next_odoo_version_module_branch_id
        if not next_module_branch:
            # No next version module branch: either the next Odoo version has
            # not been scanned yet in the repository (unknown state), or it
            # has been scanned without this module (absent state, e.g. a
            # community module that has not been migrated by the community).
            next_branch = self.module_branch_id.branch_id.next_id
            if not next_branch or not self.module_branch_id.repository_id:
                return "unknown"
            repository_branches = self.env["odoo.repository.branch"].search(
                [
                    ("repository_id", "=", self.module_branch_id.repository_id.id),
                    ("branch_id.sequence", ">=", next_branch.sequence),
                ]
            )
            if not repository_branches:
                # The repository has no branch for a version following the
                # element's one (e.g. a repository with manual branches for
                # which the next version branch has not been created yet):
                # no module branch can exist for this version, the state can
                # only be 'unknown'
                return "unknown"
            next_version_scanned = any(
                branch.last_scanned_commit for branch in repository_branches
            )
            return "absent" if next_version_scanned else "unknown"
        exists = self.env[self._name].search_count(
            [("module_branch_id", "=", next_module_branch.id)]
            + self._get_next_version_identity_domain()
        )
        return "available" if exists else "absent"

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
        # the state of the elements of the previous module branches.
        # It is deferred to the end of the import when scanning (see
        # '<odoo.module.branch>._post_import_code' override)
        if not self.env.context.get("defer_code_element_refresh"):
            records.module_branch_id._refresh_next_version_state_of_previous_branches()
        return records

    def write(self, vals):
        changing = self.browse()
        if "active" in vals:
            changing = self.filtered(lambda r: r.active != vals["active"])
        res = super().write(vals)
        if changing and not self.env.context.get("defer_code_element_refresh"):
            changing.module_branch_id._refresh_next_version_state_of_previous_branches()
        return res

    def unlink(self):
        module_branches = self.module_branch_id
        res = super().unlink()
        if not self.env.context.get("defer_code_element_refresh"):
            module_branches._refresh_next_version_state_of_previous_branches()
        return res
