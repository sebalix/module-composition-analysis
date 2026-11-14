# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, models


class OdooCodeModelElementMixin(models.AbstractModel):
    """Mixin shared by the code elements attached to a model (fields, methods).

    Their next version resolution is relative to their model: the waiting
    logic (repository branches, scans) is owned by the state of their model
    (see 'odoo.code.element.mixin'), and the element is searched on the next
    version record of the model (which follows the model renames and the
    module renames/replacements).
    """

    _name = "odoo.code.model.element.mixin"
    _description = "Odoo Code Model Element Mixin"
    _inherit = "odoo.code.element.mixin"

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
        """State of the element when no code timeline declares it.

        The element follows its model: it is searched on the next version
        record of the model (which follows the model renames and the module
        renames/replacements).
        """
        self.ensure_one()
        if self.module_branch_model_id.next_version_state == "unknown":
            return "unknown"
        next_model = self.module_branch_model_id.next_odoo_version_model_id
        if not next_model:
            # The model is not available in the next version: the element
            # neither
            return "absent"
        exists = self.search_count(
            [
                ("module_branch_model_id", "=", next_model.id),
                ("name", "=", self.name),
            ]
        )
        return "available" if exists else "absent"
