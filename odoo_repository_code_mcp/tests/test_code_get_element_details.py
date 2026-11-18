# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import McpCodeCommon


class TestCodeGetElementDetails(McpCodeCommon):
    def test_details__model(self):
        result = self.env["odoo.module.branch"]._ai_code_get_element_details(
            element_type="model",
            version="18.0",
            module="test_module_a",
            name="res.partner",
            repository="TestOCA/test-repo",
        )
        self.assertIsNone(result["error"])
        element = result["element"]
        self.assertEqual(element["element_type"], "model")
        self.assertEqual(element["name"], "res.partner")
        self.assertEqual(element["module"], "test_module_a")
        self.assertEqual(element["version"], "18.0")
        self.assertEqual(element["model_type"], "Model")
        self.assertEqual(element["order"], "name")
        self.assertEqual(element["inherit"], ["models.Model"])
        self.assertEqual(
            {field["name"] for field in element["fields"]},
            {"partner_id", "name"},
        )
        self.assertEqual(
            {method["name"] for method in element["methods"]},
            {"_compute_display_name"},
        )

    def test_details__field(self):
        result = self.env["odoo.module.branch"]._ai_code_get_element_details(
            element_type="field",
            version="18.0",
            module="test_module_a",
            model="res.partner",
            name="partner_id",
        )
        self.assertIsNone(result["error"])
        element = result["element"]
        self.assertEqual(element["element_type"], "field")
        self.assertEqual(element["model"], "res.partner")
        self.assertEqual(element["field_type"], "Many2one")
        self.assertEqual(element["comodel_name"], "res.partner")
        self.assertTrue(element["is_relational"])
        self.assertIn("fields.Many2one", element["code"])

    def test_details__method(self):
        result = self.env["odoo.module.branch"]._ai_code_get_element_details(
            element_type="method",
            version="18.0",
            module="test_module_a",
            model="res.partner",
            name="_compute_display_name",
        )
        self.assertIsNone(result["error"])
        element = result["element"]
        self.assertEqual(element["element_type"], "method")
        self.assertEqual(element["signature"], "_compute_display_name(self)")
        self.assertIn("def _compute_display_name", element["code"])
        self.assertIn("api.depends", element["code"])

    def test_details__data(self):
        result = self.env["odoo.module.branch"]._ai_code_get_element_details(
            element_type="data",
            version="18.0",
            module="test_module_a",
            name="partner_test",
        )
        self.assertIsNone(result["error"])
        element = result["element"]
        self.assertEqual(element["element_type"], "data")
        self.assertEqual(element["xml_id"], "test_module_a.partner_test")
        self.assertEqual(element["data_type"], "data")
        self.assertTrue(element["noupdate"])
        self.assertTrue(element["loaded"])
        self.assertFalse(element["is_override"])
        self.assertIsNone(element["overridden_xml_id"])
        self.assertIn("res.partner", element["data_json"])
        self.assertIn("<record", element["data_xml"])

    def test_details__data_override(self):
        self.env["odoo.module.branch.data"].create(
            {
                "module_branch_id": self.module_branch_a18.id,
                "odoo_model_version_id": self.model_version_partner.id,
                "name": "Overridden record",
                "xml_id": "base.some_record",
                "data_type": "data",
            }
        )
        result = self.env["odoo.module.branch"]._ai_code_get_element_details(
            element_type="data",
            version="18.0",
            module="test_module_a",
            name="base.some_record",
        )
        self.assertIsNone(result["error"])
        element = result["element"]
        self.assertTrue(element["is_override"])
        self.assertEqual(element["overridden_xml_id"], "base.some_record")

    def test_details__not_found(self):
        model = self.env["odoo.module.branch"]
        result = model._ai_code_get_element_details(
            element_type="model",
            version="18.0",
            module="test_module_a",
            name="unknown.model",
        )
        self.assertIsNotNone(result["error"])
        result = model._ai_code_get_element_details(
            element_type="model",
            version="17.0",
            module="test_module_a",
            name="res.partner",
        )
        self.assertIsNotNone(result["error"])

    def test_details__missing_model(self):
        result = self.env["odoo.module.branch"]._ai_code_get_element_details(
            element_type="field",
            version="18.0",
            module="test_module_a",
            name="partner_id",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("model", result["error"])

    def test_details__several_repositories(self):
        model = self.env["odoo.module.branch"]
        result = model._ai_code_get_element_details(
            element_type="model",
            version="18.0",
            module="test_module_a",
            name="res.partner",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("TestOCA/test-repo", result["error"])
        self.assertIn("TestProject/project-repo", result["error"])
        # The 'repository' input disambiguates
        result = model._ai_code_get_element_details(
            element_type="model",
            version="18.0",
            module="test_module_a",
            name="res.partner",
            repository="TestProject/project-repo",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["element"]["fields"], [])
