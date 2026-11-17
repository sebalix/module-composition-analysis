# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import McpMigrationCommon

SOURCE_URL = (
    "https://github.com/OCA/OpenUpgrade/blob/18.0/openupgrade_scripts/scripts"
    "/test_module/18.0.1.0.0/pre-migration.py"
)
HTML_NOTE = (
    "<p>[HIGHLY-CONFIDENT] Renamed.</p>"
    f'<p>Source: <a href="{SOURCE_URL}">commit</a></p>'
)


class TestTimelineWriteTools(McpMigrationCommon):
    def test_migration_create_timeline(self):
        timeline_model = self.env["odoo.module.branch.timeline"]
        result = timeline_model._ai_migration_create_timeline(
            module="test_module_b",
            version="18.0",
            new_module="test_module_c",
            note="Renamed upstream, see the commit abc123.",
        )
        self.assertIsNone(result["error"])
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

    def test_migration_create_timeline__html_note(self):
        timeline_model = self.env["odoo.module.branch.timeline"]
        result = timeline_model._ai_migration_create_timeline(
            module="test_module_b",
            version="18.0",
            new_module="test_module_c",
            note=HTML_NOTE,
        )
        self.assertIsNone(result["error"])
        self.assertIn("[HIGHLY-CONFIDENT] Renamed.", result["timeline"]["note"])
        self.assertIn(f'<a href="{SOURCE_URL}">commit</a>', result["timeline"]["note"])
        record = timeline_model.browse(result["timeline"]["id"])
        self.assertIn(f'<a href="{SOURCE_URL}">', str(record.note))

    def test_tool_schema_note_examples(self):
        model = self.env["odoo.module.branch.timeline"]
        for method_name in (
            "_ai_migration_create_timeline",
            "_ai_migration_update_timeline",
        ):
            schema = getattr(model, method_name)._ai_tool["input_schema"]
            note_schema = schema["properties"]["note"]
            self.assertIn("examples", note_schema)
            example = note_schema["examples"][0]
            self.assertIn("<br/>Source:", example)
            self.assertIn("<a href=", example)
            self.assertIn('">https://', example)

    def test_migration_create_timeline__replaced(self):
        result = self.env["odoo.module.branch.timeline"]._ai_migration_create_timeline(
            module="test_module_b",
            version="18.0",
            new_module="test_module_c",
            timeline_type="replaced",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["timeline"]["timeline_type"], "replaced")

    def test_migration_create_timeline__confirmed(self):
        timeline_model = self.env["odoo.module.branch.timeline"]
        result = timeline_model._ai_migration_create_timeline(
            module="test_module_b",
            version="18.0",
            new_module="test_module_c",
            note=SOURCE_URL,
            confirm=True,
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["timeline"]["state"], "confirmed")
        record = timeline_model.browse(result["timeline"]["id"])
        self.assertEqual(record.state, "confirmed")

    def test_migration_create_timeline__confirmed_requires_source(self):
        model = self.env["odoo.module.branch.timeline"]
        # No note at all
        result = model._ai_migration_create_timeline(
            module="test_module_b",
            version="18.0",
            new_module="test_module_c",
            confirm=True,
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("source of truth", result["error"])
        # A note without any URL
        result = model._ai_migration_create_timeline(
            module="test_module_b",
            version="18.0",
            new_module="test_module_c",
            note="Renamed upstream.",
            confirm=True,
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("source of truth", result["error"])
        # No timeline has been created
        self.assertFalse(
            model.search([("module_branch_id", "=", self.module_branch_b18.id)])
        )

    def test_migration_create_timeline__already_exists(self):
        result = self.env["odoo.module.branch.timeline"]._ai_migration_create_timeline(
            module="test_module_a",
            version="17.0",
            new_module="test_module_c",
            repository="TestOCA/test-repo",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("already exists", result["error"])

    def test_migration_create_timeline__unknown_modules(self):
        model = self.env["odoo.module.branch.timeline"]
        result = model._ai_migration_create_timeline(
            module="unknown_module",
            version="17.0",
            new_module="test_module_c",
        )
        self.assertIsNotNone(result["error"])
        result = model._ai_migration_create_timeline(
            module="test_module_c",
            version="18.0",
            new_module="test_module_c",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("not found", result["error"])
        result = model._ai_migration_create_timeline(
            module="test_module_b",
            version="18.0",
            new_module="unknown_module",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("Unknown module", result["error"])
        result = model._ai_migration_create_timeline(
            module="test_module_b",
            new_module="test_module_c",
        )
        self.assertIsNotNone(result["error"])

    def test_migration_create_timeline__several_repositories(self):
        model = self.env["odoo.module.branch.timeline"]
        result = model._ai_migration_create_timeline(
            module="test_module_a",
            version="17.0",
            new_module="test_module_c",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("TestOCA/test-repo", result["error"])
        self.assertIn("TestProject/project-repo", result["error"])
        # The 'repository' input disambiguates
        result = model._ai_migration_create_timeline(
            module="test_module_a",
            version="17.0",
            new_module="test_module_c",
            repository="TestProject/project-repo",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["timeline"]["version"], "17.0")

    def test_migration_create_timeline__invalid_type(self):
        result = self.env["odoo.module.branch.timeline"]._ai_migration_create_timeline(
            module="test_module_b",
            version="18.0",
            new_module="test_module_c",
            timeline_type="forked",
        )
        self.assertIsNotNone(result["error"])

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
        self.assertIsNone(result["error"])
        timeline = result["timeline"]
        self.assertEqual(timeline["new_module"], "test_module_c")
        self.assertEqual(timeline["timeline_type"], "replaced")
        self.assertIn("Updated note.", timeline["note"])
        self.assertIn("<p>", timeline["note"])
        self.assertEqual(timeline["state"], "draft")

    def test_migration_update_timeline__confirmed(self):
        timeline_model = self.env["odoo.module.branch.timeline"]
        result = timeline_model._ai_migration_update_timeline(
            module="test_module_a",
            version="17.0",
            note=SOURCE_URL,
            confirm=True,
            repository="TestOCA/test-repo",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["timeline"]["state"], "confirmed")
        self.assertIn(SOURCE_URL, result["timeline"]["note"])
        self.assertIn("<p>", result["timeline"]["note"])
        self.assertEqual(self.timeline_draft.state, "confirmed")

    def test_migration_update_timeline__confirmed_requires_source(self):
        model = self.env["odoo.module.branch.timeline"]
        # A note without any URL
        result = model._ai_migration_update_timeline(
            module="test_module_a",
            version="17.0",
            note="Confirmed through MCP.",
            confirm=True,
            repository="TestOCA/test-repo",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("source of truth", result["error"])
        # Confirming alone requires the stored note to carry a source
        result = model._ai_migration_update_timeline(
            module="test_module_a",
            version="17.0",
            confirm=True,
            repository="TestOCA/test-repo",
        )
        self.assertIsNotNone(result["error"])
        self.assertEqual(self.timeline_draft.state, "draft")

    def test_migration_update_timeline__confirmed_from_existing_note(self):
        timeline_model = self.env["odoo.module.branch.timeline"]
        # Document the sources first: the proposal stays a draft
        result = timeline_model._ai_migration_update_timeline(
            module="test_module_a",
            version="17.0",
            note=SOURCE_URL,
            repository="TestOCA/test-repo",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["timeline"]["state"], "draft")
        # Then confirm it without touching the note
        result = timeline_model._ai_migration_update_timeline(
            module="test_module_a",
            version="17.0",
            confirm=True,
            repository="TestOCA/test-repo",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["timeline"]["state"], "confirmed")

    def test_migration_update_timeline__confirmed_semantic_readonly(self):
        result = self.env["odoo.module.branch.timeline"]._ai_migration_update_timeline(
            module="test_module_c",
            version="17.0",
            new_module="test_module_b",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("confirmed", result["error"])
        self.assertIn("note", result["error"])
        # The timeline has not been modified
        self.assertEqual(self.timeline_confirmed.next_module_id, self.module_a)

    def test_migration_update_timeline__confirmed_note_html(self):
        result = self.env["odoo.module.branch.timeline"]._ai_migration_update_timeline(
            module="test_module_c",
            version="17.0",
            note=HTML_NOTE,
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["timeline"]["state"], "confirmed")
        self.assertIn("[HIGHLY-CONFIDENT] Renamed.", result["timeline"]["note"])
        self.assertIn(f'<a href="{SOURCE_URL}">commit</a>', result["timeline"]["note"])
        self.assertIn(f'<a href="{SOURCE_URL}">', str(self.timeline_confirmed.note))

    def test_migration_update_timeline__confirmed_note_requires_source(self):
        result = self.env["odoo.module.branch.timeline"]._ai_migration_update_timeline(
            module="test_module_c",
            version="17.0",
            note="<p>No source here.</p>",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("source of truth", result["error"])
        self.assertNotIn("No source here", str(self.timeline_confirmed.note))

    def test_migration_update_timeline__confirmed_note_keeps_migration_data(self):
        timeline_model = self.env["odoo.module.branch.timeline"]
        # Confirm the A/17 draft timeline, then annotate its note
        result = timeline_model._ai_migration_update_timeline(
            module="test_module_a",
            version="17.0",
            note=SOURCE_URL,
            confirm=True,
            repository="TestOCA/test-repo",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(self.timeline_draft.state, "confirmed")
        self.migration.last_target_scanned_commit = "keep-target"
        self.migration.process = "migrate"
        self.migration.results = {"keep": True}
        result = timeline_model._ai_migration_update_timeline(
            module="test_module_a",
            version="17.0",
            note=HTML_NOTE,
            repository="TestOCA/test-repo",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(self.migration.last_target_scanned_commit, "keep-target")
        self.assertEqual(self.migration.process, "migrate")
        self.assertEqual(self.migration.results, {"keep": True})

    def test_migration_update_timeline__invalid(self):
        model = self.env["odoo.module.branch.timeline"]
        # No field to update
        result = model._ai_migration_update_timeline(
            module="test_module_a",
            version="17.0",
            repository="TestOCA/test-repo",
        )
        self.assertIsNotNone(result["error"])
        # Same module
        result = model._ai_migration_update_timeline(
            module="test_module_a",
            version="17.0",
            new_module="test_module_a",
            repository="TestOCA/test-repo",
        )
        self.assertIsNotNone(result["error"])
        # Unknown new module
        result = model._ai_migration_update_timeline(
            module="test_module_a",
            version="17.0",
            new_module="unknown_module",
            repository="TestOCA/test-repo",
        )
        self.assertIsNotNone(result["error"])
        # Unknown timeline
        result = model._ai_migration_update_timeline(
            module="test_module_b",
            version="18.0",
            new_module="test_module_c",
        )
        self.assertIsNotNone(result["error"])

    def test_migration_delete_timeline(self):
        timeline_model = self.env["odoo.module.branch.timeline"]
        result = timeline_model._ai_migration_delete_timeline(
            module="test_module_a",
            version="17.0",
            repository="TestOCA/test-repo",
        )
        self.assertIsNone(result["error"])
        self.assertTrue(result["deleted"])
        self.assertFalse(self.timeline_draft.exists())

    def test_migration_delete_timeline__confirmed_readonly(self):
        result = self.env["odoo.module.branch.timeline"]._ai_migration_delete_timeline(
            module="test_module_c",
            version="17.0",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("confirmed", result["error"])
        self.assertTrue(self.timeline_confirmed.exists())

    def test_migration_delete_timeline__not_found(self):
        result = self.env["odoo.module.branch.timeline"]._ai_migration_delete_timeline(
            module="test_module_b",
            version="18.0",
        )
        self.assertIsNotNone(result["error"])
