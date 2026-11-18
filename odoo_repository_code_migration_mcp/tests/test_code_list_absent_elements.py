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
        self.assertEqual(
            result["counts"],
            {"uncovered": 4, "draft": 1, "removed": 1, "moved": 0},
        )
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
        self.assertIsNone(gone_field["timeline"])
        draft = by_key[("field", "draft_field")]
        self.assertEqual(draft["timeline"]["type"], "moved")
        self.assertEqual(draft["timeline"]["state"], "draft")
        self.assertEqual(draft["timeline"]["target"]["name"], "draft_field_new")
        removed = by_key[("method", "_removed_method")]
        self.assertEqual(removed["timeline"]["type"], "removed")
        self.assertEqual(removed["timeline"]["state"], "confirmed")
        self.assertIsNone(removed["timeline"]["target"])
        model = by_key[("model", "gone.model")]
        self.assertIsNone(model["model"])
        self.assertEqual(model["next_defined_in"], [])
        data = by_key[("data", "test_module_a.gone_record")]
        self.assertEqual(data["data_type"], "data")
        self.assertFalse(data["noupdate"])
        self.assertFalse(data["is_override"])
        self.assertIsNone(data["overridden_xml_id"])

    def test_list__timeline_filters(self):
        model = self.env["odoo.module.branch"]
        result = model._ai_code_list_absent_elements(
            module="test_module_a", version="17.0", timeline_state="none"
        )
        self.assertEqual(result["total"], 4)
        self.assertEqual(
            {element["timeline"] for element in result["elements"]},
            {None},
        )
        self.assertEqual(
            result["counts"],
            {"uncovered": 4, "draft": 1, "removed": 1, "moved": 0},
        )
        result = model._ai_code_list_absent_elements(
            module="test_module_a", version="17.0", timeline_state="draft"
        )
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["elements"][0]["timeline"]["state"], "draft")
        result = model._ai_code_list_absent_elements(
            module="test_module_a", version="17.0", timeline_state="confirmed"
        )
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["elements"][0]["timeline"]["state"], "confirmed")
        result = model._ai_code_list_absent_elements(
            module="test_module_a", version="17.0", timeline_type="removed"
        )
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["elements"][0]["timeline"]["type"], "removed")

    def test_list__data_classification(self):
        model = self.env["odoo.module.branch"]
        self._create_data(
            self.module_branch_a17,
            self.model_version_partner_17,
            "Demo record",
            "demo_record",
            data_type="demo",
        )
        self._create_data(
            self.module_branch_a17,
            self.model_version_partner_17,
            "Noupdate record",
            "noupdate_record",
            noupdate=True,
        )
        self._create_data(
            self.module_branch_a17,
            self.model_version_partner_17,
            "Override record",
            "base.some_record",
        )
        self._create_data(
            self.module_branch_a17,
            self.model_version_partner_17,
            "Not loaded record",
            "not_loaded_record",
            loaded=False,
        )
        result = model._ai_code_list_absent_elements(
            module="test_module_a", version="17.0", element_type="data"
        )
        self.assertEqual(result["total"], 4)
        self.assertNotIn(
            "test_module_a.not_loaded_record",
            {element["name"] for element in result["elements"]},
        )
        result = model._ai_code_list_absent_elements(
            module="test_module_a",
            version="17.0",
            element_type="data",
            data_type="demo",
        )
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["elements"][0]["data_type"], "demo")
        result = model._ai_code_list_absent_elements(
            module="test_module_a",
            version="17.0",
            element_type="data",
            data_type="data",
        )
        self.assertEqual(result["total"], 3)
        result = model._ai_code_list_absent_elements(
            module="test_module_a",
            version="17.0",
            element_type="data",
            noupdate=True,
        )
        self.assertEqual(result["total"], 1)
        result = model._ai_code_list_absent_elements(
            module="test_module_a",
            version="17.0",
            element_type="data",
            is_override=True,
        )
        self.assertEqual(result["total"], 1)
        element = result["elements"][0]
        self.assertEqual(element["name"], "base.some_record")
        self.assertTrue(element["is_override"])
        self.assertEqual(element["overridden_xml_id"], "base.some_record")
        # A data filter restricts the search to data elements
        result = model._ai_code_list_absent_elements(
            module="test_module_a", version="17.0", data_type="demo"
        )
        self.assertEqual(result["total"], 1)
        result = model._ai_code_list_absent_elements(
            module="test_module_a",
            version="17.0",
            element_type="field",
            data_type="demo",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("data elements", result["error"])

    def test_list__next_defined_in(self):
        module = self.env["odoo.module"].create({"name": "test_base_module"})
        module_branch = self._create_module_branch(
            module, self.branch18, self.repo_branch_oca_18
        )
        model_version = self.env["odoo.model.version"].create(
            {
                "odoo_model_id": self.odoo_model_gone.id,
                "odoo_version_id": self.branch18.id,
            }
        )
        self._create_model_branch(module_branch, model_version)
        result = self.env["odoo.module.branch"]._ai_code_list_absent_elements(
            module="test_module_a", version="17.0", element_type="model"
        )
        model_row = next(
            element for element in result["elements"] if element["name"] == "gone.model"
        )
        self.assertEqual(model_row["next_defined_in"], ["test_base_module"])

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
