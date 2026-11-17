# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import McpCodeMigrationCommon

SOURCE_URL = (
    "https://github.com/oca/OpenUpgrade/blob/18.0/openupgrade_scripts/scripts"
    "/test_module/18.0.1.0.0/pre-migration.py"
)
HTML_NOTE = (
    "<p>[HIGHLY-CONFIDENT] Renamed.</p>"
    f'<p>Source: <a href="{SOURCE_URL}">commit</a></p>'
)


class TestCodeTimelineWriteTools(McpCodeMigrationCommon):
    def test_create__renamed_field(self):
        result = self.env["odoo.code.timeline"]._ai_code_create_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="name",
            next_name="name",
            note="Renamed upstream, see the commit abc123.",
        )
        self.assertIsNone(result["error"])
        timeline = result["timeline"]
        self.assertEqual(timeline["element_type"], "field")
        self.assertEqual(timeline["module"], "test_module_a")
        self.assertEqual(timeline["version"], "17.0")
        self.assertEqual(timeline["model"], "res.partner")
        self.assertEqual(timeline["name"], "name")
        self.assertEqual(timeline["timeline_type"], "moved")
        # Proposals are always created as draft
        self.assertEqual(timeline["state"], "draft")
        self.assertEqual(timeline["next"]["name"], "name")
        self.assertEqual(timeline["next"]["version"], "18.0")
        self.assertEqual(timeline["starting_version"], "18.0")
        self.assertIn("Renamed upstream, see the commit abc123.", timeline["note"])
        self.assertIn("<p>", timeline["note"])
        record = self.env["odoo.code.timeline"].browse(timeline["id"])
        self.assertEqual(record.state, "draft")

    def test_create__html_note(self):
        result = self.env["odoo.code.timeline"]._ai_code_create_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="name",
            next_name="name",
            note=HTML_NOTE,
        )
        self.assertIsNone(result["error"])
        self.assertIn("[HIGHLY-CONFIDENT] Renamed.", result["timeline"]["note"])
        self.assertIn(f'<a href="{SOURCE_URL}">commit</a>', result["timeline"]["note"])
        record = self.env["odoo.code.timeline"].browse(result["timeline"]["id"])
        self.assertIn(f'<a href="{SOURCE_URL}">', str(record.note))

    def test_tool_schema_note_examples(self):
        model = self.env["odoo.code.timeline"]
        for method_name in (
            "_ai_code_create_timeline",
            "_ai_code_update_timeline",
        ):
            schema = getattr(model, method_name)._ai_tool["input_schema"]
            note_schema = schema["properties"]["note"]
            self.assertIn("examples", note_schema)
            example = note_schema["examples"][0]
            self.assertIn("<br/>Source:", example)
            self.assertIn("<a href=", example)
            self.assertIn('">https://', example)

    def test_create__removed_method(self):
        result = self.env["odoo.code.timeline"]._ai_code_create_timeline(
            element_type="method",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="_compute_x",
            timeline_type="removed",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["timeline"]["timeline_type"], "removed")
        self.assertIsNone(result["timeline"]["next"])

    def test_create__model_renamed(self):
        result = self.env["odoo.code.timeline"]._ai_code_create_timeline(
            element_type="model",
            version="17.0",
            module="test_module_a",
            name="res.partner",
            next_name="new.model",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["timeline"]["next"]["name"], "new.model")

    def test_create__data_renamed(self):
        result = self.env["odoo.code.timeline"]._ai_code_create_timeline(
            element_type="data",
            version="17.0",
            module="test_module_a",
            name="kept_record",
            next_name="new_record",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["timeline"]["next"]["name"], "test_module_a.new_record")

    def test_create__confirmed(self):
        timeline_model = self.env["odoo.code.timeline"]
        result = timeline_model._ai_code_create_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="name",
            timeline_type="removed",
            note=SOURCE_URL,
            confirm=True,
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["timeline"]["state"], "confirmed")
        record = timeline_model.browse(result["timeline"]["id"])
        self.assertEqual(record.state, "confirmed")
        # The element next version state is refreshed right away
        self.field_name_17.invalidate_recordset(["next_version_state"])
        self.assertEqual(self.field_name_17.next_version_state, "absent")

    def test_create__confirmed_requires_source(self):
        model = self.env["odoo.code.timeline"]
        # No note at all
        result = model._ai_code_create_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="name",
            timeline_type="removed",
            confirm=True,
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("source of truth", result["error"])
        # A note without any URL
        result = model._ai_code_create_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="name",
            timeline_type="removed",
            note="Removed upstream.",
            confirm=True,
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("source of truth", result["error"])
        # No timeline has been created
        self.assertFalse(model.search([("field_id", "=", self.field_name_17.id)]))

    def test_create__already_exists(self):
        result = self.env["odoo.code.timeline"]._ai_code_create_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="old_name",
            next_name="new_name",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("already exists", result["error"])

    def test_create__missing_target(self):
        result = self.env["odoo.code.timeline"]._ai_code_create_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="name",
            next_name="unknown_field",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("was not found", result["error"])

    def test_create__invalid_params(self):
        model = self.env["odoo.code.timeline"]
        # A removal takes no target
        result = model._ai_code_create_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="name",
            timeline_type="removed",
            next_name="name",
        )
        self.assertIsNotNone(result["error"])
        # A rename requires a target
        result = model._ai_code_create_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="name",
            timeline_type="moved",
        )
        self.assertIsNotNone(result["error"])
        # A field requires its model
        result = model._ai_code_create_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            name="name",
            next_name="name",
        )
        self.assertIsNotNone(result["error"])
        # Unknown element
        result = model._ai_code_create_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="unknown_field",
            next_name="name",
        )
        self.assertIsNotNone(result["error"])

    def test_update(self):
        result = self.env["odoo.code.timeline"]._ai_code_update_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="draft_field",
            timeline_type="removed",
            note="Updated note.",
        )
        self.assertIsNone(result["error"])
        timeline = result["timeline"]
        self.assertEqual(timeline["timeline_type"], "removed")
        self.assertIsNone(timeline["next"])
        self.assertIn("Updated note.", timeline["note"])
        self.assertIn("<p>", timeline["note"])
        self.assertEqual(timeline["state"], "draft")

    def test_update__next_name(self):
        result = self.env["odoo.code.timeline"]._ai_code_update_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="draft_field",
            next_name="new_name",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["timeline"]["next"]["name"], "new_name")

    def test_update__confirmed(self):
        timeline_model = self.env["odoo.code.timeline"]
        result = timeline_model._ai_code_update_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="draft_field",
            note=SOURCE_URL,
            confirm=True,
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["timeline"]["state"], "confirmed")
        self.assertIn(SOURCE_URL, result["timeline"]["note"])
        self.assertIn("<p>", result["timeline"]["note"])
        self.assertEqual(self.timeline_draft.state, "confirmed")
        # The element next version state is refreshed: the draft renames
        # 'draft_field' into an existing field
        self.field_draft_17.invalidate_recordset(["next_version_state"])
        self.assertEqual(self.field_draft_17.next_version_state, "available")

    def test_update__confirmed_requires_source(self):
        model = self.env["odoo.code.timeline"]
        # A note without any URL
        result = model._ai_code_update_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="draft_field",
            note="Confirmed through MCP.",
            confirm=True,
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("source of truth", result["error"])
        # Confirming alone requires the stored note to carry a source
        # (the draft has no note)
        result = model._ai_code_update_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="draft_field",
            confirm=True,
        )
        self.assertIsNotNone(result["error"])
        self.assertEqual(self.timeline_draft.state, "draft")

    def test_update__confirmed_from_existing_note(self):
        timeline_model = self.env["odoo.code.timeline"]
        # Document the sources first: the proposal stays a draft
        result = timeline_model._ai_code_update_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="draft_field",
            note=SOURCE_URL,
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["timeline"]["state"], "draft")
        # Then confirm it without touching the note
        result = timeline_model._ai_code_update_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="draft_field",
            confirm=True,
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["timeline"]["state"], "confirmed")

    def test_update__confirmed_note_html(self):
        result = self.env["odoo.code.timeline"]._ai_code_update_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="old_name",
            note=HTML_NOTE,
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["timeline"]["state"], "confirmed")
        self.assertIn(f'<a href="{SOURCE_URL}">', result["timeline"]["note"])
        self.assertIn(f'<a href="{SOURCE_URL}">', str(self.timeline_field.note))

    def test_update__confirmed_note_requires_source(self):
        result = self.env["odoo.code.timeline"]._ai_code_update_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="old_name",
            note="<p>No source here.</p>",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("source of truth", result["error"])
        self.assertNotIn("No source here", str(self.timeline_field.note))

    def test_update__confirmed_semantic_readonly(self):
        result = self.env["odoo.code.timeline"]._ai_code_update_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="old_name",
            timeline_type="removed",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("confirmed", result["error"])
        self.assertIn("note", result["error"])
        self.assertEqual(self.timeline_field.timeline_type, "moved")

    def test_update__invalid(self):
        model = self.env["odoo.code.timeline"]
        # No field to update
        result = model._ai_code_update_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="draft_field",
        )
        self.assertIsNotNone(result["error"])
        # A removal takes no target
        result = model._ai_code_update_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="draft_field",
            timeline_type="removed",
            next_name="new_name",
        )
        self.assertIsNotNone(result["error"])
        # Unknown timeline
        result = model._ai_code_update_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="name",
            note="x",
        )
        self.assertIsNotNone(result["error"])

    def test_delete(self):
        result = self.env["odoo.code.timeline"]._ai_code_delete_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="draft_field",
        )
        self.assertIsNone(result["error"])
        self.assertTrue(result["deleted"])
        self.assertFalse(self.timeline_draft.exists())

    def test_delete__confirmed_readonly(self):
        result = self.env["odoo.code.timeline"]._ai_code_delete_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="old_name",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("confirmed", result["error"])
        self.assertTrue(self.timeline_field.exists())

    def test_delete__not_found(self):
        result = self.env["odoo.code.timeline"]._ai_code_delete_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="name",
        )
        self.assertIsNotNone(result["error"])
