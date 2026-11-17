# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import McpMigrationCommon


class TestTimelineWriteTools(McpMigrationCommon):
    def test_migration_create_timeline(self):
        timeline_model = self.env["odoo.module.branch.timeline"]
        result = timeline_model._ai_migration_create_timeline(
            module="test_module_b",
            version="18.0",
            new_module="test_module_c",
            note="Renamed upstream, see the commit abc123.",
        )
        self.assertNotIn("error", result)
        timeline = result["timeline"]
        self.assertEqual(timeline["module"], "test_module_b")
        self.assertEqual(timeline["version"], "18.0")
        self.assertEqual(timeline["timeline_type"], "renamed")
        # Proposals are always created as draft
        self.assertEqual(timeline["state"], "draft")
        self.assertEqual(timeline["new_module"], "test_module_c")
        self.assertEqual(timeline["starting_version"], "19.0")
        self.assertTrue(timeline["id"])
        record = timeline_model.browse(timeline["id"])
        self.assertEqual(record.state, "draft")
        self.assertIn("Renamed upstream, see the commit abc123.", record.note)

    def test_migration_create_timeline__replaced(self):
        result = self.env["odoo.module.branch.timeline"]._ai_migration_create_timeline(
            module="test_module_b",
            version="18.0",
            new_module="test_module_c",
            timeline_type="replaced",
        )
        self.assertNotIn("error", result)
        self.assertEqual(result["timeline"]["timeline_type"], "replaced")

    def test_migration_create_timeline__already_exists(self):
        result = self.env["odoo.module.branch.timeline"]._ai_migration_create_timeline(
            module="test_module_a",
            version="17.0",
            new_module="test_module_c",
            repository="TestOCA/test-repo",
        )
        self.assertIn("error", result)
        self.assertIn("already exists", result["error"])

    def test_migration_create_timeline__unknown_modules(self):
        model = self.env["odoo.module.branch.timeline"]
        result = model._ai_migration_create_timeline(
            module="unknown_module",
            version="17.0",
            new_module="test_module_c",
        )
        self.assertIn("error", result)
        result = model._ai_migration_create_timeline(
            module="test_module_c",
            version="18.0",
            new_module="test_module_c",
        )
        self.assertIn("error", result)
        self.assertIn("not found", result["error"])
        result = model._ai_migration_create_timeline(
            module="test_module_b",
            version="18.0",
            new_module="unknown_module",
        )
        self.assertIn("error", result)
        self.assertIn("Unknown module", result["error"])
        result = model._ai_migration_create_timeline(
            module="test_module_b",
            new_module="test_module_c",
        )
        self.assertIn("error", result)

    def test_migration_create_timeline__several_repositories(self):
        model = self.env["odoo.module.branch.timeline"]
        result = model._ai_migration_create_timeline(
            module="test_module_a",
            version="17.0",
            new_module="test_module_c",
        )
        self.assertIn("error", result)
        self.assertIn("TestOCA/test-repo", result["error"])
        self.assertIn("TestProject/project-repo", result["error"])
        # The 'repository' input disambiguates
        result = model._ai_migration_create_timeline(
            module="test_module_a",
            version="17.0",
            new_module="test_module_c",
            repository="TestProject/project-repo",
        )
        self.assertNotIn("error", result)
        self.assertEqual(result["timeline"]["version"], "17.0")

    def test_migration_create_timeline__invalid_type(self):
        result = self.env["odoo.module.branch.timeline"]._ai_migration_create_timeline(
            module="test_module_b",
            version="18.0",
            new_module="test_module_c",
            timeline_type="forked",
        )
        self.assertIn("error", result)

    def test_migration_update_timeline(self):
        timeline_model = self.env["odoo.module.branch.timeline"]
        result = timeline_model._ai_migration_update_timeline(
            module="test_module_a",
            version="17.0",
            new_module="test_module_c",
            timeline_type="replaced",
            note="Updated note.",
            repository="TestOCA/test-repo",
        )
        self.assertNotIn("error", result)
        timeline = result["timeline"]
        self.assertEqual(timeline["new_module"], "test_module_c")
        self.assertEqual(timeline["timeline_type"], "replaced")
        self.assertEqual(timeline["note"], "Updated note.")
        self.assertEqual(timeline["state"], "draft")

    def test_migration_update_timeline__confirmed_readonly(self):
        result = self.env["odoo.module.branch.timeline"]._ai_migration_update_timeline(
            module="test_module_c",
            version="17.0",
            new_module="test_module_b",
        )
        self.assertIn("error", result)
        self.assertIn("confirmed", result["error"])
        # The timeline has not been modified
        self.assertEqual(self.timeline_confirmed.next_module_id, self.module_a)

    def test_migration_update_timeline__invalid(self):
        model = self.env["odoo.module.branch.timeline"]
        # No field to update
        result = model._ai_migration_update_timeline(
            module="test_module_a",
            version="17.0",
            repository="TestOCA/test-repo",
        )
        self.assertIn("error", result)
        # Same module
        result = model._ai_migration_update_timeline(
            module="test_module_a",
            version="17.0",
            new_module="test_module_a",
            repository="TestOCA/test-repo",
        )
        self.assertIn("error", result)
        # Unknown new module
        result = model._ai_migration_update_timeline(
            module="test_module_a",
            version="17.0",
            new_module="unknown_module",
            repository="TestOCA/test-repo",
        )
        self.assertIn("error", result)
        # Unknown timeline
        result = model._ai_migration_update_timeline(
            module="test_module_b",
            version="18.0",
            new_module="test_module_c",
        )
        self.assertIn("error", result)

    def test_migration_delete_timeline(self):
        timeline_model = self.env["odoo.module.branch.timeline"]
        result = timeline_model._ai_migration_delete_timeline(
            module="test_module_a",
            version="17.0",
            repository="TestOCA/test-repo",
        )
        self.assertNotIn("error", result)
        self.assertTrue(result["deleted"])
        self.assertFalse(self.timeline_draft.exists())

    def test_migration_delete_timeline__confirmed_readonly(self):
        result = self.env["odoo.module.branch.timeline"]._ai_migration_delete_timeline(
            module="test_module_c",
            version="17.0",
        )
        self.assertIn("error", result)
        self.assertIn("confirmed", result["error"])
        self.assertTrue(self.timeline_confirmed.exists())

    def test_migration_delete_timeline__not_found(self):
        result = self.env["odoo.module.branch.timeline"]._ai_migration_delete_timeline(
            module="test_module_b",
            version="18.0",
        )
        self.assertIn("error", result)
