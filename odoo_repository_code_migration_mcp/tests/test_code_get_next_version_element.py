# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import McpCodeMigrationCommon


class TestCodeGetNextVersionElement(McpCodeMigrationCommon):
    def test_next__field_renamed(self):
        result = self.env["odoo.module.branch"]._ai_code_get_next_version_element(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="old_name",
        )
        self.assertIsNone(result["error"])
        self.assertTrue(result["found"])
        self.assertEqual(result["state"], "available")
        self.assertEqual(
            result["next"],
            {
                "element_type": "field",
                "module": "test_module_a",
                "version": "18.0",
                "model": "res.partner",
                "name": "new_name",
            },
        )

    def test_next__field_same_name(self):
        result = self.env["odoo.module.branch"]._ai_code_get_next_version_element(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="name",
        )
        self.assertIsNone(result["error"])
        self.assertTrue(result["found"])
        self.assertEqual(result["state"], "available")
        self.assertEqual(result["next"]["name"], "name")
        self.assertEqual(result["next"]["version"], "18.0")

    def test_next__method_removed(self):
        result = self.env["odoo.module.branch"]._ai_code_get_next_version_element(
            element_type="method",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="_removed_method",
        )
        self.assertIsNone(result["error"])
        self.assertFalse(result["found"])
        self.assertEqual(result["state"], "absent")
        self.assertIsNone(result["next"])

    def test_next__draft_proposal(self):
        result = self.env["odoo.module.branch"]._ai_code_get_next_version_element(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="draft_field",
        )
        self.assertIsNone(result["error"])
        self.assertFalse(result["found"])
        self.assertEqual(result["state"], "absent")
        self.assertIsNone(result["next"])
        self.assertEqual(result["proposal"]["timeline_type"], "moved")
        self.assertEqual(result["proposal"]["next"]["name"], "draft_field_new")
        self.assertEqual(result["proposal"]["next"]["version"], "18.0")

    def test_next__model_renamed(self):
        result = self.env["odoo.module.branch"]._ai_code_get_next_version_element(
            element_type="model",
            version="17.0",
            module="test_module_a",
            name="old.model",
        )
        self.assertIsNone(result["error"])
        self.assertTrue(result["found"])
        self.assertEqual(result["next"]["name"], "new.model")
        self.assertEqual(result["next"]["version"], "18.0")
        self.assertIsNone(result["next"]["model"])

    def test_next__data_renamed(self):
        result = self.env["odoo.module.branch"]._ai_code_get_next_version_element(
            element_type="data",
            version="17.0",
            module="test_module_a",
            name="old_record",
        )
        self.assertIsNone(result["error"])
        self.assertTrue(result["found"])
        self.assertEqual(result["next"]["name"], "test_module_a.new_record")

    def test_next__not_found(self):
        result = self.env["odoo.module.branch"]._ai_code_get_next_version_element(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="unknown_field",
        )
        self.assertIsNotNone(result["error"])

    def test_next__missing_model(self):
        result = self.env["odoo.module.branch"]._ai_code_get_next_version_element(
            element_type="field",
            version="17.0",
            module="test_module_a",
            name="name",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("model", result["error"])

    def test_next__several_repositories(self):
        model = self.env["odoo.module.branch"]
        result = model._ai_code_get_next_version_element(
            element_type="model",
            version="18.0",
            module="test_module_a",
            name="res.partner",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("TestOCA/test-repo", result["error"])
        self.assertIn("TestProject/project-repo", result["error"])
        result = model._ai_code_get_next_version_element(
            element_type="model",
            version="18.0",
            module="test_module_a",
            name="res.partner",
            repository="TestOCA/test-repo",
        )
        self.assertIsNone(result["error"])
