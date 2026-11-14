# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from unittest.mock import patch

from .common import CodeMigrationCommon


class TestOdooModuleBranchData(CodeMigrationCommon):
    """Scan the git fixture repository and check the data evolution features."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The fake commit hash set on the module branch by the common class
        # would break the git queries of the scanner ('bad revision' error):
        # reset it to let the scan run as a first scan
        cls.module_branch.last_scanned_commit = False

    def test_scan_data_next_version_state(self):
        """The next version state of a data element evolves with the scans."""
        self._run_odoo_repository_action_scan(self.branch.id)
        module_branch = self._get_module_branch()
        view = self._get_data(module_branch, "my_model_view_form")
        self.assertTrue(view)
        # The 16.0 branch is not scanned yet: unknown state
        self.assertEqual(view.next_version_state, "unknown")
        self.assertIn(
            view,
            self.env["odoo.module.branch.data"].search(
                [("next_version_state", "=", "unknown")]
            ),
        )
        # Create the module branch on 16.0: the record is considered removed
        # (the creation refreshes the previous module branches)
        module_branch2 = self._create_odoo_module_branch(
            self.module,
            self.branch2,
            specific=False,
            repository_branch_id=self.repo_branch2.id,
            last_scanned_commit="sha",
        )
        self.assertEqual(view.next_version_state, "removed")
        self.assertIn(
            view,
            self.env["odoo.module.branch.data"].search(
                [("next_version_state", "=", "removed")]
            ),
        )
        # Create the data record (same xml_id) on 16.0: available (the data
        # creation refreshes the previous module branches)
        self._create_odoo_module_branch_data(
            module_branch2, "ir.ui.view", "my_model_view_form"
        )
        self.assertEqual(view.next_version_state, "available")
        self.assertIn(
            view,
            self.env["odoo.module.branch.data"].search(
                [("next_version_state", "=", "available")]
            ),
        )
        self.assertNotIn(
            view,
            self.env["odoo.module.branch.data"].search(
                [("next_version_state", "=", "removed")]
            ),
        )

    def test_scan_data_next_version_state_module_rename(self):
        """The next version state follows the module renames."""
        # Module renamed starting from 16.0
        module_branch = self._get_module_branch()
        next_module = self.env["odoo.module"].create(
            {"name": f"{self.module_name}_renamed"}
        )
        self._create_module_timeline(module_branch, next_module, "renamed")
        self._run_odoo_repository_action_scan(self.branch.id)
        view = self._get_data(module_branch, "my_model_view_form")
        module_branch2 = self._create_odoo_module_branch(
            next_module,
            self.branch2,
            specific=False,
            repository_branch_id=self.repo_branch2.id,
            last_scanned_commit="sha",
        )
        self._create_odoo_module_branch_data(
            module_branch2, "ir.ui.view", "my_model_view_form"
        )
        self.assertEqual(view.next_version_state, "available")
        self.assertIn(
            view,
            self.env["odoo.module.branch.data"].search(
                [("next_version_state", "=", "available")]
            ),
        )

    def test_cron_refresh_code_elements_next_version_state(self):
        """The cron reclassifies the elements still in the 'unknown' state."""
        self._run_odoo_repository_action_scan(self.branch.id)
        module_branch = self._get_module_branch()
        view = self._get_data(module_branch, "my_model_view_form")
        self.assertEqual(view.next_version_state, "unknown")
        # Create the next version elements with the refresh hooks disabled,
        # as if they had been created before the installation of the module
        with patch.object(
            type(self.env["odoo.module.branch"]),
            "_refresh_next_version_state_of_previous_branches",
            lambda self: None,
        ):
            module_branch2 = self._create_odoo_module_branch(
                self.module,
                self.branch2,
                specific=False,
                repository_branch_id=self.repo_branch2.id,
                last_scanned_commit="sha",
            )
            self._create_odoo_module_branch_data(
                module_branch2, "ir.ui.view", "my_model_view_form"
            )
        self.assertEqual(view.next_version_state, "unknown")
        # The cron spawns the refresh jobs (executed inline here)
        self.env["odoo.module.branch"].with_context(
            queue_job__no_delay=True
        )._cron_refresh_code_elements_next_version_state()
        self.assertEqual(view.next_version_state, "available")

    def test_job_refresh_code_elements_next_version_state(self):
        """The job recomputes the next version state of the given records."""
        self._run_odoo_repository_action_scan(self.branch.id)
        module_branch = self._get_module_branch()
        view = self._get_data(module_branch, "my_model_view_form")
        self.assertEqual(view.next_version_state, "unknown")
        with patch.object(
            type(self.env["odoo.module.branch"]),
            "_refresh_next_version_state_of_previous_branches",
            lambda self: None,
        ):
            module_branch2 = self._create_odoo_module_branch(
                self.module,
                self.branch2,
                specific=False,
                repository_branch_id=self.repo_branch2.id,
                last_scanned_commit="sha",
            )
            self._create_odoo_module_branch_data(
                module_branch2, "ir.ui.view", "my_model_view_form"
            )
        self.assertEqual(view.next_version_state, "unknown")
        self.env["odoo.module.branch"]._job_refresh_code_elements_next_version_state(
            view
        )
        self.assertEqual(view.next_version_state, "available")
