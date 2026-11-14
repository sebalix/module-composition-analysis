# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, models


class OdooModuleBranch(models.Model):
    _inherit = "odoo.module.branch"

    def _import_code(self, data):
        # The per-element refreshes of the next version states are deferred
        # to the end of the import (one refresh per module instead of one
        # per element, see '_post_import_code' override)
        self = self.with_context(defer_code_element_refresh=True)
        return super()._import_code(data)

    def _post_import_code(self):
        res = super()._post_import_code()
        self._refresh_next_version_state_of_previous_branches()
        return res

    def _get_code_element_models(self):
        """Return the models of the code elements having a next version state."""
        return list(self.env["odoo.code.timeline"]._ELEMENT_COMODELS.values())

    def _get_previous_module_branches(self):
        """Return the module branches having the current one as next module
        branch (same module on an earlier version, or module renamed to the
        current one by an active timeline).
        """
        self.ensure_one()
        return (
            self.env["odoo.module.branch"].search(
                [
                    ("module_id", "=", self.module_id.id),
                    ("branch_sequence", "<", self.branch_sequence),
                ]
            )
            | self.env["odoo.module.branch.timeline"]
            .search(
                [
                    ("next_module_id", "=", self.module_id.id),
                    ("active", "=", True),
                    ("state", "=", "confirmed"),
                    ("module_branch_id.branch_sequence", "<", self.branch_sequence),
                ]
            )
            .module_branch_id
        )

    def _refresh_next_version_state(self):
        """Recompute 'next_version_state' on code elements of current modules."""
        if not self:
            return
        # The next module branch values may be cached (computed before the
        # current module branch existed)
        self.invalidate_recordset(["next_odoo_version_module_branch_id"])
        for model_name in self._get_code_element_models():
            records = self.env[model_name].search(
                [("module_branch_id", "in", self.ids)]
            )
            if records:
                records.env.add_to_compute(
                    records._fields["next_version_state"], records
                )
        self.env.flush_all()

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
        previous_module_branches._refresh_next_version_state()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # The new module branches are the next version of existing ones: the
        # elements of these ones are now (at least) considered as removed
        records._refresh_next_version_state_of_previous_branches()
        return records

    @api.model
    def _cron_refresh_code_elements_next_version_state(self):
        """Cron: spawn jobs refreshing the 'next_version_state' of the code
        elements still classified as 'unknown' (not yet classified).

        The elements of the last Odoo version are skipped: they cannot be
        classified as long as the next Odoo version doesn't exist. They will
        be included again automatically once a new version is created.
        """
        last_branch = self.env["odoo.branch"].search([], order="sequence DESC", limit=1)
        if not last_branch:
            return
        # Only the module branches whose repository has a branch for a later
        # version can progress: derive the candidates from the repository
        # structure (small) instead of filtering the element recordsets (huge)
        ready_module_branches = self._get_next_version_ready_module_branches()
        if not ready_module_branches:
            return
        for model_name in self._get_code_element_models():
            model = self.env[model_name]
            records = model.search(
                [
                    ("module_branch_id", "in", ready_module_branches.ids),
                    ("next_version_state", "=", "unknown"),
                    (
                        "module_branch_id.branch_id.sequence",
                        "<",
                        last_branch.sequence,
                    ),
                ]
            )
            for index in range(0, len(records), 1000):
                chunk = records[index : index + 1000]
                self.with_delay(
                    max_retries=1
                )._job_refresh_code_elements_next_version_state(chunk)

    @api.model
    def _get_next_version_ready_module_branches(self):
        """Return the module branches whose repository has a branch for a
        version following their own one.

        Only the elements of these module branches can leave the 'unknown'
        state (e.g. a repository with manual branches for which the next
        version branch has not been created yet cannot progress): the
        candidates are derived from the repository structure (small dataset)
        instead of filtering the element recordsets (huge dataset).
        """
        ready_module_branch_ids = []
        for repository in self.env["odoo.repository"].search([]):
            # Every version followed by another one in the same repository
            # can progress (the repository's last version cannot)
            branches = repository.branch_ids.sorted(lambda rb: rb.branch_id.sequence)[
                :-1
            ]
            if branches:
                ready_module_branch_ids.extend(
                    self.search(
                        [
                            ("repository_id", "=", repository.id),
                            ("branch_id", "in", branches.branch_id.ids),
                        ]
                    ).ids
                )
        return self.browse(ready_module_branch_ids)

    def _job_refresh_code_elements_next_version_state(self, records):
        """Job: recompute the 'next_version_state' of the given records."""
        # The next module branch values may be cached (computed before the
        # next version was scanned)
        records.module_branch_id.invalidate_recordset(
            ["next_odoo_version_module_branch_id"]
        )
        records.env.add_to_compute(records._fields["next_version_state"], records)
        records.env.flush_all()
