# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from unittest.mock import patch

from .common import CodeMigrationCommon


class TestOdooCodeElementMixin(CodeMigrationCommon):
    """Test the 'next_version_state' logic shared by the code elements."""

    def test_next_version_state_next_version_not_scanned(self):
        """The next version of the repository is not scanned: 'unknown'."""
        model = self._create_odoo_module_branch_model(
            self.module_branch, "my_module.model_a"
        )
        self.assertFalse(self.module_branch.next_odoo_version_module_branch_id)
        self.assertEqual(model.next_version_state, "unknown")

    def test_next_version_state_next_version_scanned_without_module(self):
        """The next version of the repository is scanned without the module.

        The element is 'absent' (e.g. a community module that has not been
        migrated by the community).
        """
        model = self._create_odoo_module_branch_model(
            self.module_branch, "my_module.model_a"
        )
        self.assertEqual(model.next_version_state, "unknown")
        # The next version of the repository is scanned, but without any
        # module (the repository branch exists and has been scanned)
        self.repo_branch2.last_scanned_commit = "sha"
        self.assertFalse(self.module_branch.next_odoo_version_module_branch_id)
        # The stored state is not refreshed by the scan of the repository
        # branch (no dependency change): the cron reclassifies it
        self.assertEqual(model.next_version_state, "unknown")
        self.env["odoo.module.branch"].with_context(
            queue_job__no_delay=True
        )._cron_refresh_code_elements_next_version_state()
        self.assertEqual(model.next_version_state, "absent")

    def test_next_version_state_next_version_branch_not_scanned(self):
        """The repository branch exists on the next version but has never
        been scanned: 'unknown'."""
        model = self._create_odoo_module_branch_model(
            self.module_branch, "my_module.model_a"
        )
        self.assertFalse(self.repo_branch2.last_scanned_commit)
        self.assertEqual(model.next_version_state, "unknown")
        self.env["odoo.module.branch"].with_context(
            queue_job__no_delay=True
        )._cron_refresh_code_elements_next_version_state()
        self.assertEqual(model.next_version_state, "unknown")

    def test_next_version_state_next_version_repository_branch_missing(self):
        """The repository has no branch for a version following the
        element's one (e.g. manual branches not created yet): the state can
        only be 'unknown', and the cron does not refresh it."""
        module_manual = self.module.copy({"name": "my_module_manual"})
        repo_branch = self._create_odoo_repository_branch(
            self.gen_repository, self.branch
        )
        module_branch = self._create_odoo_module_branch(
            module_manual,
            self.branch,
            specific=False,
            repository_branch_id=repo_branch.id,
            last_scanned_commit="sha",
        )
        model = self._create_odoo_module_branch_model(
            module_branch, "my_module.model_a"
        )
        # An element of the main repository, which has its next version
        # branch: used to check that the cron filter is not too large
        model_ready = self._create_odoo_module_branch_model(
            self.module_branch, "my_module.model_b"
        )
        self.assertFalse(
            self.env["odoo.repository.branch"].search_count(
                [
                    ("repository_id", "=", self.gen_repository.id),
                    ("branch_id.sequence", ">=", self.branch2.sequence),
                ]
            )
        )
        self.assertEqual(model.next_version_state, "unknown")
        # The cron does not refresh the elements that cannot progress
        refreshed_ids = []

        def _job_refresh_code_elements_next_version_state(self, records):
            refreshed_ids.extend(records.ids)

        with patch.object(
            type(self.env["odoo.module.branch"]),
            "_job_refresh_code_elements_next_version_state",
            _job_refresh_code_elements_next_version_state,
        ):
            self.env["odoo.module.branch"].with_context(
                queue_job__no_delay=True
            )._cron_refresh_code_elements_next_version_state()
        self.assertNotIn(model.id, refreshed_ids)
        self.assertEqual(model.next_version_state, "unknown")
        # The elements able to progress are still refreshed
        self.assertIn(model_ready.id, refreshed_ids)

    def test_next_version_state_next_version_repository_branch_created(self):
        """Once the repository branch for the next version is created and the
        module scanned on it, the elements are classified."""
        module_manual = self.module.copy({"name": "my_module_manual"})
        repo_branch = self._create_odoo_repository_branch(
            self.gen_repository, self.branch
        )
        module_branch = self._create_odoo_module_branch(
            module_manual,
            self.branch,
            specific=False,
            repository_branch_id=repo_branch.id,
            last_scanned_commit="sha",
        )
        model = self._create_odoo_module_branch_model(
            module_branch, "my_module.model_a"
        )
        self.assertEqual(model.next_version_state, "unknown")
        # The repository branch for the next version is created (manual
        # branches scenario): no change until the module is scanned on it
        repo_branch2 = self._create_odoo_repository_branch(
            self.gen_repository, self.branch2
        )
        self.assertEqual(model.next_version_state, "unknown")
        module_branch2 = self._create_odoo_module_branch(
            module_manual,
            self.branch2,
            specific=False,
            repository_branch_id=repo_branch2.id,
            last_scanned_commit="sha",
        )
        # The module branch creation refreshed the previous module branches:
        # the element is 'absent' (the next version is scanned without it)
        self.assertEqual(model.next_version_state, "absent")
        # The element is scanned on the next version: 'available'
        self._create_odoo_module_branch_model(module_branch2, "my_module.model_a")
        self.assertEqual(model.next_version_state, "available")

    def test_next_version_state_removed_timeline_without_next_repository_branch(self):
        """A 'removed' code timeline sets 'absent' even when the repository
        has no branch for the next version (manual declaration, independent
        of the scans)."""
        module_manual = self.module.copy({"name": "my_module_manual"})
        repo_branch = self._create_odoo_repository_branch(
            self.gen_repository, self.branch
        )
        module_branch = self._create_odoo_module_branch(
            module_manual,
            self.branch,
            specific=False,
            repository_branch_id=repo_branch.id,
            last_scanned_commit="sha",
        )
        model = self._create_odoo_module_branch_model(
            module_branch, "my_module.model_a"
        )
        self.assertEqual(model.next_version_state, "unknown")
        self._create_code_timeline(model, timeline_type="removed")
        self.assertEqual(model.next_version_state, "absent")

    def test_cron_skip_elements_of_last_version(self):
        """The cron skips the elements of the last Odoo version: they cannot
        be classified as long as the next Odoo version doesn't exist."""
        last_branch = self.env["odoo.branch"].search([], order="sequence DESC", limit=1)
        # The last version module is a different one: my_module has no later
        # branch, so its elements cannot be classified before the cron runs
        # (they stay 'unknown'), while the elements of the last version
        # cannot be classified at all (no next version)
        module_last = self.module.copy({"name": "module_last"})
        module_branch_last = self._create_odoo_module_branch(
            module_last,
            last_branch,
            specific=False,
            last_scanned_commit="sha",
        )
        model_last = self._create_odoo_module_branch_model(
            module_branch_last, "my_module.model_z"
        )
        model_first = self._create_odoo_module_branch_model(
            self.module_branch, "my_module.model_w"
        )
        self.assertEqual(model_last.next_version_state, "unknown")
        self.assertEqual(model_first.next_version_state, "unknown")
        refreshed_ids = []

        def _job_refresh_code_elements_next_version_state(self, records):
            refreshed_ids.extend(records.ids)

        with patch.object(
            type(self.env["odoo.module.branch"]),
            "_job_refresh_code_elements_next_version_state",
            _job_refresh_code_elements_next_version_state,
        ):
            self.env["odoo.module.branch"].with_context(
                queue_job__no_delay=True
            )._cron_refresh_code_elements_next_version_state()
        # The element of the last version is not refreshed
        self.assertNotIn(model_last.id, refreshed_ids)
        # The element of an earlier version is refreshed
        self.assertIn(model_first.id, refreshed_ids)

    def test_next_version_state_next_version_scanned_with_module(self):
        """The next version of the module is scanned without the element: 'absent'."""
        model = self._create_odoo_module_branch_model(
            self.module_branch, "my_module.model_a"
        )
        module_branch2 = self._create_odoo_module_branch(
            self.module,
            self.branch2,
            specific=False,
            repository_branch_id=self.repo_branch2.id,
            last_scanned_commit="sha",
        )
        self.assertEqual(model.next_version_state, "absent")
        # The model is scanned on the next version: 'available'
        model2 = self._create_odoo_module_branch_model(
            module_branch2, "my_module.model_a"
        )
        self.assertEqual(model.next_version_state, "available")
        self.assertEqual(model.next_odoo_version_model_id, model2)

    def test_next_version_state_element_archived(self):
        """Archiving/unarchiving an element of the next version updates the
        state of the previous version's element."""
        model = self._create_odoo_module_branch_model(
            self.module_branch, "my_module.model_a"
        )
        module_branch2 = self._create_odoo_module_branch(
            self.module,
            self.branch2,
            specific=False,
            repository_branch_id=self.repo_branch2.id,
            last_scanned_commit="sha",
        )
        model2 = self._create_odoo_module_branch_model(
            module_branch2, "my_module.model_a"
        )
        self.assertEqual(model.next_version_state, "available")
        # The element disappears from the next version: archived
        model2.active = False
        self.assertEqual(model.next_version_state, "absent")
        # The element is back
        model2.active = True
        self.assertEqual(model.next_version_state, "available")
