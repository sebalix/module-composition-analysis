# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import McpCodeMigrationCommon


class TestCodeGetElementHistory(McpCodeMigrationCommon):
    def test_history__field_chain(self):
        result = self.env["odoo.module.branch"]._ai_code_get_element_history(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="old_name",
        )
        self.assertIsNone(result["error"])
        history = result["history"]
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["name"], "old_name")
        self.assertEqual(history[0]["version"], "17.0")
        self.assertEqual(history[0]["timeline_type"], "moved")
        self.assertEqual(history[0]["state"], "confirmed")
        self.assertEqual(history[1]["name"], "new_name")
        self.assertEqual(history[1]["version"], "18.0")
        self.assertIsNone(history[1]["timeline_type"])
        self.assertIsNone(history[1]["state"])

    def test_history__from_the_newest(self):
        # Querying the newest element returns the same chain
        result = self.env["odoo.module.branch"]._ai_code_get_element_history(
            element_type="field",
            version="18.0",
            module="test_module_a",
            model="res.partner",
            name="new_name",
        )
        self.assertIsNone(result["error"])
        names = [entry["name"] for entry in result["history"]]
        self.assertEqual(names, ["old_name", "new_name"])

    def test_history__method_removed(self):
        result = self.env["odoo.module.branch"]._ai_code_get_element_history(
            element_type="method",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="_removed_method",
        )
        self.assertIsNone(result["error"])
        history = result["history"]
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["timeline_type"], "removed")
        self.assertEqual(history[0]["state"], "confirmed")

    def test_history__model_chain(self):
        result = self.env["odoo.module.branch"]._ai_code_get_element_history(
            element_type="model",
            version="17.0",
            module="test_module_a",
            name="old.model",
        )
        self.assertIsNone(result["error"])
        names = [entry["name"] for entry in result["history"]]
        self.assertEqual(names, ["old.model", "new.model"])

    def test_history__data_chain(self):
        result = self.env["odoo.module.branch"]._ai_code_get_element_history(
            element_type="data",
            version="17.0",
            module="test_module_a",
            name="old_record",
        )
        self.assertIsNone(result["error"])
        names = [entry["name"] for entry in result["history"]]
        self.assertEqual(
            names, ["test_module_a.old_record", "test_module_a.new_record"]
        )

    def test_history__single_element(self):
        # An element without any timeline
        result = self.env["odoo.module.branch"]._ai_code_get_element_history(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="name",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(len(result["history"]), 1)
        self.assertIsNone(result["history"][0]["timeline_type"])

    def test_history__not_found(self):
        result = self.env["odoo.module.branch"]._ai_code_get_element_history(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="unknown_field",
        )
        self.assertIsNotNone(result["error"])
