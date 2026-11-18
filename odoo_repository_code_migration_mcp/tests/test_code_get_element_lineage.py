# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import McpCodeMigrationCommon


class TestCodeGetElementLineage(McpCodeMigrationCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_lineage_data()

    @classmethod
    def _setup_lineage_data(cls):
        cls.branch14 = cls._activate_odoo_branch("14.0")
        cls.branch16 = cls._activate_odoo_branch("16.0")
        cls.branch20 = cls._activate_odoo_branch("20.0")
        cls.repo_branch_oca_14 = cls.env["odoo.repository.branch"].create(
            {"repository_id": cls.repo_oca.id, "branch_id": cls.branch14.id}
        )
        cls.repo_branch_oca_16 = cls.env["odoo.repository.branch"].create(
            {"repository_id": cls.repo_oca.id, "branch_id": cls.branch16.id}
        )
        cls.repo_branch_oca_20 = cls.env["odoo.repository.branch"].create(
            {"repository_id": cls.repo_oca.id, "branch_id": cls.branch20.id}
        )
        cls.lineage_module = cls.env["odoo.module"].create({"name": "lineage_module"})
        cls.lineage_module_branch_14 = cls._create_module_branch(
            cls.lineage_module, cls.branch14, cls.repo_branch_oca_14
        )
        cls.lineage_module_branch_16 = cls._create_module_branch(
            cls.lineage_module, cls.branch16, cls.repo_branch_oca_16
        )
        cls.lineage_module_branch_18 = cls._create_module_branch(
            cls.lineage_module, cls.branch18, cls.repo_branch_oca_18
        )
        cls.lineage_module_branch_20 = cls._create_module_branch(
            cls.lineage_module, cls.branch20, cls.repo_branch_oca_20
        )
        cls.lineage_model = cls.env["odoo.model"].create({"name": "lineage.model"})
        cls.lineage_model_version_14 = cls.env["odoo.model.version"].create(
            {
                "odoo_model_id": cls.lineage_model.id,
                "odoo_version_id": cls.branch14.id,
            }
        )
        cls.lineage_model_version_16 = cls.env["odoo.model.version"].create(
            {
                "odoo_model_id": cls.lineage_model.id,
                "odoo_version_id": cls.branch16.id,
            }
        )
        cls.lineage_model_version_18 = cls.env["odoo.model.version"].create(
            {
                "odoo_model_id": cls.lineage_model.id,
                "odoo_version_id": cls.branch18.id,
            }
        )
        cls.lineage_model_version_20 = cls.env["odoo.model.version"].create(
            {
                "odoo_model_id": cls.lineage_model.id,
                "odoo_version_id": cls.branch20.id,
            }
        )
        cls.lineage_model_14 = cls._create_model_branch(
            cls.lineage_module_branch_14, cls.lineage_model_version_14
        )
        cls.lineage_model_16 = cls._create_model_branch(
            cls.lineage_module_branch_16, cls.lineage_model_version_16
        )
        cls.lineage_model_18 = cls._create_model_branch(
            cls.lineage_module_branch_18, cls.lineage_model_version_18
        )
        cls.lineage_model_20 = cls._create_model_branch(
            cls.lineage_module_branch_20, cls.lineage_model_version_20
        )
        cls.lineage_field_14 = cls._create_field(cls.lineage_model_14, "lineage_field")
        cls.lineage_field_16 = cls._create_field(cls.lineage_model_16, "lineage_field")
        cls.lineage_field_new_18 = cls._create_field(
            cls.lineage_model_18, "lineage_field_new"
        )
        cls.lineage_field_new_20 = cls._create_field(
            cls.lineage_model_20, "lineage_field_new"
        )
        cls.lineage_timeline = cls.env["odoo.code.timeline"].create(
            {
                "element_type": "field",
                "field_id": cls.lineage_field_16.id,
                "next_field_id": cls.lineage_field_new_18.id,
                "timeline_type": "moved",
                "state": "confirmed",
                "note": "Renamed in 18.0.",
            }
        )

    def test_lineage__jumps_versions(self):
        result = self.env["odoo.module.branch"]._ai_code_get_element_lineage(
            element_type="field",
            version="14.0",
            module="lineage_module",
            model="lineage.model",
            name="lineage_field",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["target_version"], "20.0")
        self.assertEqual(
            [step["version"] for step in result["steps"]],
            ["14.0", "16.0", "18.0", "20.0"],
        )
        self.assertEqual(result["steps"][0]["element"]["name"], "lineage_field")
        self.assertEqual(result["steps"][1]["element"]["name"], "lineage_field")
        self.assertEqual(result["steps"][2]["element"]["name"], "lineage_field_new")
        self.assertEqual(result["steps"][3]["element"]["name"], "lineage_field_new")
        self.assertIsNone(result["steps"][0]["timeline"])
        self.assertEqual(result["steps"][1]["timeline"]["type"], "moved")
        self.assertEqual(result["steps"][1]["timeline"]["state"], "confirmed")
        self.assertEqual(
            result["steps"][1]["timeline"]["target"]["name"],
            "lineage_field_new",
        )
        self.assertIsNone(result["steps"][2]["timeline"])

    def test_lineage__target_version(self):
        result = self.env["odoo.module.branch"]._ai_code_get_element_lineage(
            element_type="field",
            version="14.0",
            module="lineage_module",
            model="lineage.model",
            name="lineage_field",
            to_version="18.0",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["target_version"], "18.0")
        self.assertEqual(
            [step["version"] for step in result["steps"]],
            ["14.0", "16.0", "18.0"],
        )

    def test_lineage__target_before_start(self):
        result = self.env["odoo.module.branch"]._ai_code_get_element_lineage(
            element_type="field",
            version="18.0",
            module="lineage_module",
            model="lineage.model",
            name="lineage_field_new",
            to_version="16.0",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("before the starting version", result["error"])

    def test_lineage__removed(self):
        result = self.env["odoo.module.branch"]._ai_code_get_element_lineage(
            element_type="method",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="_removed_method",
            to_version="20.0",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(len(result["steps"]), 1)
        self.assertEqual(result["steps"][0]["timeline"]["type"], "removed")
        self.assertEqual(result["steps"][0]["timeline"]["state"], "confirmed")

    def test_lineage__draft(self):
        result = self.env["odoo.module.branch"]._ai_code_get_element_lineage(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="draft_field",
            to_version="20.0",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(len(result["steps"]), 1)
        self.assertEqual(result["steps"][0]["version"], "17.0")
        self.assertEqual(result["steps"][0]["timeline"]["type"], "moved")
        self.assertEqual(result["steps"][0]["timeline"]["state"], "draft")
        self.assertEqual(
            result["steps"][0]["timeline"]["target"]["name"], "draft_field_new"
        )

    def test_lineage__not_found(self):
        result = self.env["odoo.module.branch"]._ai_code_get_element_lineage(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="unknown_field",
        )
        self.assertIsNotNone(result["error"])

    def test_lineage__repository_ambiguity(self):
        result = self.env["odoo.module.branch"]._ai_code_get_element_lineage(
            element_type="model",
            version="18.0",
            module="test_module_a",
            name="res.partner",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("TestOCA/test-repo", result["error"])
        self.assertIn("TestProject/project-repo", result["error"])

    def test_lineage__batch(self):
        result = self.env["odoo.module.branch"]._ai_code_get_elements_lineage(
            elements=[
                {
                    "element_type": "field",
                    "version": "14.0",
                    "module": "lineage_module",
                    "model": "lineage.model",
                    "name": "lineage_field",
                },
                {
                    "element_type": "field",
                    "version": "17.0",
                    "module": "test_module_a",
                    "model": "res.partner",
                    "name": "unknown_field",
                },
            ],
            to_version="20.0",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(len(result["results"][0]["lineage"]["steps"]), 4)
        self.assertIsNone(result["results"][0]["error"])
        self.assertIsNone(result["results"][1]["lineage"])
        self.assertIn("No field", result["results"][1]["error"])
