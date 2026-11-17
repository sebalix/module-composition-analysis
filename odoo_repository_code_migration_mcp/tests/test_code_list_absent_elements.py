# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import McpCodeMigrationCommon


class TestCodeListAbsentElements(McpCodeMigrationCommon):
    def test_list(self):
        result = self.env["odoo.module.branch"]._ai_code_list_absent_elements(
            module="test_module_a", version="17.0"
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["next_version"], "18.0")
        self.assertEqual(result["total"], 6)
        by_key = {
            (element["element_type"], element["name"]): element
            for element in result["elements"]
        }
        gone_field = by_key[("field", "gone_field")]
        self.assertEqual(gone_field["module"], "test_module_a")
        self.assertEqual(gone_field["version"], "17.0")
        self.assertEqual(gone_field["model"], "res.partner")
        self.assertEqual(gone_field["org"], "TestOCA")
        self.assertEqual(gone_field["repository"], "test-repo")
        self.assertIsNone(gone_field["timeline_type"])
        self.assertIsNone(gone_field["timeline_state"])
        draft = by_key[("field", "draft_field")]
        self.assertEqual(draft["timeline_type"], "moved")
        self.assertEqual(draft["timeline_state"], "draft")
        removed = by_key[("method", "_removed_method")]
        self.assertEqual(removed["timeline_type"], "removed")
        self.assertEqual(removed["timeline_state"], "confirmed")
        model = by_key[("model", "gone.model")]
        self.assertIsNone(model["model"])

    def test_list__element_type_filter(self):
        model = self.env["odoo.module.branch"]
        result = model._ai_code_list_absent_elements(
            module="test_module_a", version="17.0", element_type="field"
        )
        self.assertEqual(result["total"], 2)
        self.assertEqual(
            {element["name"] for element in result["elements"]},
            {"gone_field", "draft_field"},
        )
        result = model._ai_code_list_absent_elements(
            module="test_module_a", version="17.0", element_type="method"
        )
        self.assertEqual(result["total"], 2)

    def test_list__model_filter(self):
        result = self.env["odoo.module.branch"]._ai_code_list_absent_elements(
            module="test_module_a", version="17.0", model="res.partner"
        )
        self.assertEqual(result["total"], 5)

    def test_list__pagination(self):
        model = self.env["odoo.module.branch"]
        result = model._ai_code_list_absent_elements(
            module="test_module_a", version="17.0", limit=2
        )
        self.assertEqual(result["total"], 6)
        self.assertEqual(len(result["elements"]), 2)
        result = model._ai_code_list_absent_elements(
            module="test_module_a", version="17.0", limit=2, offset=4
        )
        self.assertEqual(result["total"], 6)
        self.assertEqual(len(result["elements"]), 2)

    def test_list__repository_filter(self):
        model = self.env["odoo.module.branch"]
        result = model._ai_code_list_absent_elements(
            module="test_module_a",
            version="17.0",
            repository="TestOCA/test-repo",
        )
        self.assertEqual(result["total"], 6)
        result = model._ai_code_list_absent_elements(
            module="test_module_a",
            version="17.0",
            repository="TestProject/project-repo",
        )
        self.assertIsNotNone(result["error"])

    def test_list__no_next_version(self):
        result = self.env["odoo.module.branch"]._ai_code_list_absent_elements(
            module="test_module_a", version="18.0"
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("No Odoo version known after", result["error"])

    def test_list__unknown_module(self):
        result = self.env["odoo.module.branch"]._ai_code_list_absent_elements(
            module="unknown_module", version="17.0"
        )
        self.assertIsNotNone(result["error"])
