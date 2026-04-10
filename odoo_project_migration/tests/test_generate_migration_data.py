# Copyright 2026 Sébastien Alix
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.odoo_project.tests.common import ProjectCommon
from odoo.addons.odoo_repository_migration.tests.common import MigrationCommon


class TestOdooProjectGenerateMigrationData(ProjectCommon, MigrationCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mig_path_model = cls.env["odoo.migration.path"]
        cls.module_branch_model = cls.env["odoo.module.branch"]
        cls.generate_mig_data_model = cls.env["odoo.project.generate.migration.data"]
        cls.ModuleMigration = cls.env["odoo.project.module.migration"]
        cls.migration_path = cls.mig_path_model.create(
            {
                "name": "16.0 -> 17.0",
                "source_branch_id": cls.branch.id,
                "target_branch_id": cls.branch2.id,
            }
        )

    def setUp(self):
        super().setUp()
        # Create a module branch for testing
        self.module_branch = self.module_branch_model.create(
            {
                "name": "module1",
                "branch_name": "16.0",
            }
        )
        # Add module to project
        self.project.write(
            {
                "project_module_ids": [
                    (
                        0,
                        0,
                        {
                            "module_branch_id": self.module_branch.id,
                        },
                    )
                ]
            }
        )

    def test_generate_migration_data(self):
        # Create wizard
        wizard = self.generate_mig_data_model.create(
            {
                "odoo_project_id": self.project.id,
                "migration_path_id": self.migration_path.id,
            }
        )

        # Execute wizard
        result = wizard.action_generate_data()

        # Check result
        self.assertEqual(result["type"], "ir.actions.act_window")
        self.assertIn("domain", result)
        self.assertIn(
            ("migration_path_id", "=", self.migration_path.id), result["domain"]
        )

        # Check created module migrations
        module_migrations = self.ModuleMigration.search(
            [
                ("odoo_project_id", "=", self.project.id),
                ("migration_path_id", "=", self.migration_path.id),
            ]
        )
        self.assertEqual(len(module_migrations), 1)
        self.assertEqual(module_migrations.source_module_branch_id, self.module_branch)

    def test_generate_migration_data_existing_data_removed(self):
        # Create existing module migration
        self.ModuleMigration.create(
            {
                "odoo_project_id": self.project.id,
                "migration_path_id": self.migration_path.id,
                "source_module_branch_id": self.module_branch.id,
            }
        )

        # Create wizard
        wizard = self.generate_mig_data_model.create(
            {
                "odoo_project_id": self.project.id,
                "migration_path_id": self.migration_path.id,
            }
        )

        # Execute wizard
        wizard.action_generate_data()

        # Check that existing data was removed and new data created
        module_migrations = self.ModuleMigration.search(
            [
                ("odoo_project_id", "=", self.project.id),
                ("migration_path_id", "=", self.migration_path.id),
            ]
        )
        self.assertEqual(len(module_migrations), 1)
        self.assertEqual(module_migrations.source_module_branch_id, self.module_branch)
