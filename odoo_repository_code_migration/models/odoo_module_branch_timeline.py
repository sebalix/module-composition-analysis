# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class OdooModuleBranchTimeline(models.Model):
    _inherit = "odoo.module.branch.timeline"

    def write(self, vals):
        res = super().write(vals)
        if "active" in vals or "state" in vals:
            # Archiving/unarchiving or confirming a module timeline changes
            # the next version resolution of the module branch: refresh the
            # state of its code elements
            self.module_branch_id._refresh_next_version_state()
        return res
