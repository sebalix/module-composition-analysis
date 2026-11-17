# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import McpCodeCommon


class TestCodeSearchElements(McpCodeCommon):
    def test_search__models(self):
        result = self.env["odoo.module.branch"]._ai_code_search_elements(
            element_type="model"
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["total"], 3)
        names = {element["name"] for element in result["elements"]}
        self.assertEqual(names, {"res.partner", "sale.order"})
        partner = next(
            element
            for element in result["elements"]
            if element["name"] == "res.partner" and element["repository"] == "test-repo"
        )
        self.assertEqual(partner["element_type"], "model")
        self.assertEqual(partner["module"], "test_module_a")
        self.assertEqual(partner["version"], "18.0")
        self.assertEqual(partner["model_type"], "Model")
        self.assertIsNone(partner["model"])

    def test_search__fields(self):
        result = self.env["odoo.module.branch"]._ai_code_search_elements(
            element_type="field"
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["total"], 2)
        partner_id = next(
            element for element in result["elements"] if element["name"] == "partner_id"
        )
        self.assertEqual(partner_id["element_type"], "field")
        self.assertEqual(partner_id["model"], "res.partner")
        self.assertEqual(partner_id["field_type"], "Many2one")
        self.assertEqual(partner_id["comodel_name"], "res.partner")

    def test_search__methods(self):
        result = self.env["odoo.module.branch"]._ai_code_search_elements(
            element_type="method"
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["total"], 1)
        method = result["elements"][0]
        self.assertEqual(method["name"], "_compute_display_name")
        self.assertEqual(method["signature"], "_compute_display_name(self)")

    def test_search__data(self):
        result = self.env["odoo.module.branch"]._ai_code_search_elements(
            element_type="data"
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["total"], 1)
        data = result["elements"][0]
        self.assertEqual(data["name"], "Partner record")
        self.assertEqual(data["xml_id"], "test_module_a.partner_test")
        self.assertEqual(data["data_type"], "data")
        self.assertEqual(data["model"], "res.partner")

    def test_search__filters(self):
        model = self.env["odoo.module.branch"]
        result = model._ai_code_search_elements(element_type="model", version="17.0")
        self.assertEqual(result["total"], 0)
        result = model._ai_code_search_elements(
            element_type="model", model="res.partner"
        )
        self.assertEqual(result["total"], 2)
        result = model._ai_code_search_elements(element_type="model", name="sale")
        self.assertEqual(result["total"], 1)
        result = model._ai_code_search_elements(element_type="field", name="partner")
        self.assertEqual(result["total"], 1)
        result = model._ai_code_search_elements(
            element_type="data", name="partner_test"
        )
        self.assertEqual(result["total"], 1)
        result = model._ai_code_search_elements(
            element_type="model", repository="TestProject/project-repo"
        )
        self.assertEqual(result["total"], 1)

    def test_search__pagination(self):
        model = self.env["odoo.module.branch"]
        result = model._ai_code_search_elements(element_type="model", limit=2)
        self.assertEqual(result["total"], 3)
        self.assertEqual(len(result["elements"]), 2)
        result = model._ai_code_search_elements(element_type="model", limit=2, offset=2)
        self.assertEqual(result["total"], 3)
        self.assertEqual(len(result["elements"]), 1)

    def test_search__invalid_params(self):
        model = self.env["odoo.module.branch"]
        result = model._ai_code_search_elements(element_type="foo")
        self.assertIsNotNone(result["error"])
        result = model._ai_code_search_elements(element_type="model", version="99.0")
        self.assertIsNotNone(result["error"])
        result = model._ai_code_search_elements(element_type="model", limit=0)
        self.assertIsNotNone(result["error"])
        # An unknown module is a plain filter: no error, no result
        result = model._ai_code_search_elements(
            element_type="model", module="unknown_module"
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["total"], 0)
