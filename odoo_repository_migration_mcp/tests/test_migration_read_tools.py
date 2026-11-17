# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import McpMigrationCommon


class TestMigrationReadTools(McpMigrationCommon):
    def test_migration_get_module_status(self):
        result = self.env["odoo.module.branch"]._ai_migration_get_module_status(
            module="test_module_a"
        )
        self.assertIsNone(result["error"])
        self.assertEqual(len(result["migrations"]), 2)
        statuses = {m["status"]: m for m in result["migrations"]}
        self.assertEqual(set(statuses), {"migrate", "moved_to_generic"})
        migrate = statuses["migrate"]
        self.assertEqual(migrate["source"], "17.0")
        self.assertEqual(migrate["target"], "18.0")
        self.assertIsNone(migrate["pr_url"])
        self.assertEqual(migrate["last_source_scanned_commit"], "s1" * 10)
        self.assertFalse(migrate["renamed_to"])
        self.assertFalse(migrate["replaced_by"])
        self.assertEqual(
            statuses["moved_to_generic"]["pr_url"],
            "https://github.com/TestOCA/test-repo/pull/42",
        )

    def test_migration_get_module_status__filters(self):
        model = self.env["odoo.module.branch"]
        result = model._ai_migration_get_module_status(
            module="test_module_a", source_version="17.0"
        )
        self.assertEqual(len(result["migrations"]), 2)
        result = model._ai_migration_get_module_status(
            module="test_module_a", source_version="18.0"
        )
        self.assertEqual(result["migrations"], [])
        result = model._ai_migration_get_module_status(
            module="test_module_a", repository="TestOCA/test-repo"
        )
        self.assertEqual(len(result["migrations"]), 1)
        self.assertEqual(result["migrations"][0]["status"], "migrate")
        result = model._ai_migration_get_module_status(
            module="test_module_a", repository="TestProject/project-repo"
        )
        self.assertEqual(len(result["migrations"]), 1)
        self.assertEqual(result["migrations"][0]["status"], "moved_to_generic")
        # A migration with an existing PR on a generic repository
        result = model._ai_migration_get_module_status(module="test_module_b")
        self.assertEqual(len(result["migrations"]), 1)
        self.assertEqual(result["migrations"][0]["status"], "review_migration")
        self.assertEqual(
            result["migrations"][0]["pr_url"],
            "https://github.com/TestOCA/test-repo/pull/43",
        )

    def test_migration_get_module_status__unknown_module(self):
        result = self.env["odoo.module.branch"]._ai_migration_get_module_status(
            module="unknown_module"
        )
        self.assertIsNotNone(result["error"])
        result = self.env["odoo.module.branch"]._ai_migration_get_module_status()
        self.assertIsNotNone(result["error"])

    def test_migration_get_data(self):
        result = self.env["odoo.module.branch"]._ai_migration_get_data(
            module="test_module_a",
            source_version="17.0",
            target_version="18.0",
            repository="TestOCA/test-repo",
        )
        self.assertIsNone(result["error"])
        migration = result["migration"]
        self.assertEqual(migration["source_branch"], "17.0")
        self.assertEqual(migration["target_branch"], "18.0")
        self.assertEqual(migration["process"], "migrate")
        self.assertEqual(migration["state"], "migrate")
        self.assertEqual(migration["results"], {})
        self.assertIsNone(migration["pr_url"])
        self.assertEqual(migration["last_source_scanned_commit"], "s1" * 10)

    def test_migration_get_data__several_repositories(self):
        model = self.env["odoo.module.branch"]
        result = model._ai_migration_get_data(
            module="test_module_a",
            source_version="17.0",
            target_version="18.0",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("TestOCA/test-repo", result["error"])
        self.assertIn("TestProject/project-repo", result["error"])
        result = model._ai_migration_get_data(
            module="test_module_a",
            source_version="17.0",
            target_version="18.0",
            repository="TestProject/project-repo",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["migration"]["state"], "moved_to_generic")
        self.assertEqual(
            result["migration"]["pr_url"],
            "https://github.com/TestOCA/test-repo/pull/42",
        )

    def test_migration_get_data__no_data(self):
        model = self.env["odoo.module.branch"]
        result = model._ai_migration_get_data(
            module="test_module_c",
            source_version="17.0",
            target_version="18.0",
        )
        self.assertIsNotNone(result["error"])
        result = model._ai_migration_get_data(
            module="test_module_a",
            source_version="18.0",
            target_version="19.0",
        )
        self.assertIsNotNone(result["error"])
        result = model._ai_migration_get_data(module="test_module_a")
        self.assertIsNotNone(result["error"])

    def test_migration_list_timelines(self):
        result = self.env["odoo.module.branch.timeline"]._ai_migration_list_timelines()
        self.assertIsNone(result["error"])
        self.assertEqual(len(result["timelines"]), 2)
        timelines = {t["module"]: t for t in result["timelines"]}
        draft = timelines["test_module_a"]
        self.assertEqual(draft["timeline_type"], "renamed")
        self.assertEqual(draft["state"], "draft")
        self.assertEqual(draft["new_module"], "test_module_b")
        self.assertEqual(draft["version"], "17.0")
        self.assertEqual(draft["starting_version"], "18.0")
        self.assertIn("Renamed upstream, see the project repository.", draft["note"])
        self.assertIn("<p>", draft["note"])
        confirmed = timelines["test_module_c"]
        self.assertEqual(confirmed["timeline_type"], "replaced")
        self.assertEqual(confirmed["state"], "confirmed")
        self.assertEqual(confirmed["new_module"], "test_module_a")

    def test_migration_list_timelines__filters(self):
        model = self.env["odoo.module.branch.timeline"]
        result = model._ai_migration_list_timelines(module="test_module_a")
        self.assertEqual([t["module"] for t in result["timelines"]], ["test_module_a"])
        result = model._ai_migration_list_timelines(state="draft")
        self.assertEqual(len(result["timelines"]), 1)
        self.assertEqual(result["timelines"][0]["module"], "test_module_a")
        result = model._ai_migration_list_timelines(state="confirmed")
        self.assertEqual(len(result["timelines"]), 1)
        self.assertEqual(result["timelines"][0]["module"], "test_module_c")
        result = model._ai_migration_list_timelines(version="18.0")
        self.assertEqual(result["timelines"], [])
        result = model._ai_migration_list_timelines(
            repository="TestProject/project-repo"
        )
        self.assertEqual(result["timelines"], [])

    def test_migration_list_timelines__invalid_params(self):
        model = self.env["odoo.module.branch.timeline"]
        result = model._ai_migration_list_timelines(state="published")
        self.assertIsNotNone(result["error"])
        result = model._ai_migration_list_timelines(module="unknown_module")
        self.assertIsNotNone(result["error"])
