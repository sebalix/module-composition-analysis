# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, models


class OdooModuleBranch(models.Model):
    _inherit = "odoo.module.branch"

    def _get_code_element_models(self):
        """Return the models of the code elements having a next version state."""
        return list(self.env["odoo.code.timeline"]._ELEMENT_COMODELS.values())

    def _get_previous_module_branches(self):
        """Return the module branches having the current one as next module
        branch (same module on an earlier version, or module renamed to the
        current one by a timeline)."""
        self.ensure_one()
        return self.env["odoo.module.branch"].search(
            [
                ("module_id", "=", self.module_id.id),
                ("branch_sequence", "<", self.branch_sequence),
            ]
        ) | self.env["odoo.module.branch"].search(
            [
                ("timeline_ids.next_module_id", "=", self.module_id.id),
                ("branch_sequence", "<", self.branch_sequence),
            ]
        )

    def _refresh_next_version_state_of_previous_branches(self):
        """Recompute the 'next_version_state' of the code elements of the
        module branches having these ones as next module branch.

        Called when the code of a module branch changes (scan, new module
        branch): the elements of the previous versions may then be
        available or removed in the current version.
        """
        if not self:
            return
        previous_module_branches = self.env["odoo.module.branch"]
        for rec in self:
            previous_module_branches |= rec._get_previous_module_branches()
        if not previous_module_branches:
            return
        # The next module branch values may be cached (computed before the
        # current module branch existed)
        previous_module_branches.invalidate_recordset(
            ["next_odoo_version_module_branch_id"]
        )
        for model_name in self._get_code_element_models():
            records = self.env[model_name].search(
                [("module_branch_id", "in", previous_module_branches.ids)]
            )
            if records:
                records.env.add_to_compute(
                    records._fields["next_version_state"], records
                )
        self.env.flush_all()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # The new module branches are the next version of existing ones: the
        # elements of these ones are now (at least) considered as removed
        records._refresh_next_version_state_of_previous_branches()
        return records

    def _cron_refresh_code_elements_next_version_state(self):
        """Cron: spawn jobs refreshing the 'next_version_state' of the code
        elements still classified as 'unknown' (not yet classified)."""
        for model_name in self._get_code_element_models():
            model = self.env[model_name]
            records = model.search([("next_version_state", "=", "unknown")])
            for index in range(0, len(records), 1000):
                chunk = records[index : index + 1000]
                self.with_delay(
                    max_retries=1
                )._job_refresh_code_elements_next_version_state(chunk)

    def _job_refresh_code_elements_next_version_state(self, records):
        """Job: recompute the 'next_version_state' of the given records."""
        # The next module branch values may be cached (computed before the
        # next version was scanned)
        records.module_branch_id.invalidate_recordset(
            ["next_odoo_version_module_branch_id"]
        )
        records.env.add_to_compute(records._fields["next_version_state"], records)
        records.env.flush_all()
