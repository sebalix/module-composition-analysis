# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import McpCodeMigrationCommon

SOURCE_URL = (
    "https://github.com/OCA/OpenUpgrade/blob/18.0/openupgrade_scripts/scripts"
    "/test_module/18.0.1.0.0/pre-migration.py"
)


class TestCodeTimelineCrossScope(McpCodeMigrationCommon):
    """Target elements living in another module/model/version."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_cross_scope_data()

    @classmethod
    def _setup_cross_scope_data(cls):
        env = cls.env
        # Module B in the same repository, available on 17.0 and 18.0
        cls.module_b = env["odoo.module"].create({"name": "test_module_b"})
        cls.module_branch_b17 = cls._create_module_branch(
            cls.module_b, cls.branch17, cls.repo_branch_oca_17
        )
        cls.module_branch_b18 = cls._create_module_branch(
            cls.module_b, cls.branch18, cls.repo_branch_oca_18
        )
        # Cross-module model: cross.old @ A/17 -> cross.new @ B/18
        cls.odoo_model_cross_old = env["odoo.model"].create({"name": "cross.old"})
        cls.odoo_model_cross_new = env["odoo.model"].create({"name": "cross.new"})
        cls.model_version_cross_old_17 = env["odoo.model.version"].create(
            {
                "odoo_model_id": cls.odoo_model_cross_old.id,
                "odoo_version_id": cls.branch17.id,
            }
        )
        cls.model_version_cross_new_18 = env["odoo.model.version"].create(
            {
                "odoo_model_id": cls.odoo_model_cross_new.id,
                "odoo_version_id": cls.branch18.id,
            }
        )
        cls.model_cross_old_17 = cls._create_model_branch(
            cls.module_branch_a17, cls.model_version_cross_old_17
        )
        # A target model in module B and another one in module A
        cls.model_cross_new_18_b = cls._create_model_branch(
            cls.module_branch_b18, cls.model_version_cross_new_18
        )
        cls.model_cross_new_18_a = cls._create_model_branch(
            cls.module_branch_a18, cls.model_version_cross_new_18
        )
        # Cross-module + cross-model field
        cls.field_cross_old_17 = cls._create_field(
            cls.model_cross_old_17, "cross_field"
        )
        cls.field_cross_new_18_a = cls._create_field(
            cls.model_cross_new_18_a, "cross_field_new"
        )
        cls.field_cross_new_18_b = cls._create_field(
            cls.model_cross_new_18_b, "cross_field_new"
        )
        # Cross-model field in the same module
        cls.field_same_module_old_17 = cls._create_field(
            cls.model_cross_old_17, "same_module_field"
        )
        cls.field_same_module_new_18_a = cls._create_field(
            cls.model_cross_new_18_a, "same_module_field_new"
        )
        # Pure move: the field keeps its name but changes model and module
        cls.field_pure_old_17 = cls._create_field(cls.model_cross_old_17, "pure_field")
        cls.field_pure_new_18_b = cls._create_field(
            cls.model_cross_new_18_b, "pure_field"
        )
        # Many-to-one merge
        cls.field_merge_1_17 = cls._create_field(
            cls.model_cross_old_17, "merge_field_1"
        )
        cls.field_merge_2_17 = cls._create_field(
            cls.model_cross_old_17, "merge_field_2"
        )
        cls.field_merged_18_b = cls._create_field(
            cls.model_cross_new_18_b, "merged_field"
        )
        # One-to-many split (not representable: one target per source)
        cls.field_split_17 = cls._create_field(cls.model_cross_old_17, "split_field")
        cls.field_split_target_1_18_b = cls._create_field(
            cls.model_cross_new_18_b, "split_target_1"
        )
        cls.field_split_target_2_18_b = cls._create_field(
            cls.model_cross_new_18_b, "split_target_2"
        )
        cls.field_remove_17 = cls._create_field(cls.model_cross_old_17, "remove_field")
        # Cross-module data: same local ID and different local ID
        cls.data_cross_17 = cls._create_data(
            cls.module_branch_a17,
            cls.model_version_partner_17,
            "Cross record",
            "cross_record",
        )
        cls.data_cross_18_b = cls._create_data(
            cls.module_branch_b18,
            cls.model_version_partner_18,
            "Cross record",
            "cross_record",
        )
        cls.data_cross_renamed_17 = cls._create_data(
            cls.module_branch_a17,
            cls.model_version_partner_17,
            "Cross record renamed",
            "cross_record_renamed",
        )
        cls.data_cross_renamed_18_b = cls._create_data(
            cls.module_branch_b18,
            cls.model_version_partner_18,
            "Cross record new",
            "cross_record_new",
        )
        # Data override: the target lives in A/18 but declares an external ID
        cls.data_override_17_b = cls._create_data(
            cls.module_branch_b17,
            cls.model_version_partner_17,
            "Override record",
            "override_record",
        )
        cls.data_override_18_a = cls._create_data(
            cls.module_branch_a18,
            cls.model_version_partner_18,
            "Override record",
            "test_module_b.override_record",
        )
        # Cross-repository target
        cls.module_project = env["odoo.module"].create({"name": "test_module_project"})
        cls.module_branch_project_18 = cls._create_module_branch(
            cls.module_project, cls.branch18, cls.repo_branch_project_18
        )
        cls.odoo_model_cross_repo_old = env["odoo.model"].create(
            {"name": "cross_repo.old"}
        )
        cls.model_version_cross_repo_old_17 = env["odoo.model.version"].create(
            {
                "odoo_model_id": cls.odoo_model_cross_repo_old.id,
                "odoo_version_id": cls.branch17.id,
            }
        )
        cls.model_cross_repo_old_17 = cls._create_model_branch(
            cls.module_branch_a17, cls.model_version_cross_repo_old_17
        )
        cls.odoo_model_project_new = env["odoo.model"].create({"name": "project.new"})
        cls.model_version_project_new_18 = env["odoo.model.version"].create(
            {
                "odoo_model_id": cls.odoo_model_project_new.id,
                "odoo_version_id": cls.branch18.id,
            }
        )
        cls.model_project_new_18 = cls._create_model_branch(
            cls.module_branch_project_18, cls.model_version_project_new_18
        )
        # Version gap: module C exists on 17.0 and 19.0, not on 18.0
        cls.branch19 = cls._activate_odoo_branch("19.0")
        cls.repo_branch_oca_19 = env["odoo.repository.branch"].create(
            {
                "repository_id": cls.repo_oca.id,
                "branch_id": cls.branch19.id,
            }
        )
        cls.module_gap = env["odoo.module"].create({"name": "test_module_gap"})
        cls.module_branch_gap_17 = cls._create_module_branch(
            cls.module_gap, cls.branch17, cls.repo_branch_oca_17
        )
        cls.module_branch_gap_19 = cls._create_module_branch(
            cls.module_gap, cls.branch19, cls.repo_branch_oca_19
        )
        cls.odoo_model_gap_old = env["odoo.model"].create({"name": "gap.old"})
        cls.odoo_model_gap_new = env["odoo.model"].create({"name": "gap.new"})
        cls.model_version_gap_old_17 = env["odoo.model.version"].create(
            {
                "odoo_model_id": cls.odoo_model_gap_old.id,
                "odoo_version_id": cls.branch17.id,
            }
        )
        cls.model_version_gap_new_19 = env["odoo.model.version"].create(
            {
                "odoo_model_id": cls.odoo_model_gap_new.id,
                "odoo_version_id": cls.branch19.id,
            }
        )
        cls.model_gap_old_17 = cls._create_model_branch(
            cls.module_branch_gap_17, cls.model_version_gap_old_17
        )
        cls.model_gap_new_19 = cls._create_model_branch(
            cls.module_branch_gap_19, cls.model_version_gap_new_19
        )

    def _create(self, **kwargs):
        return self.env["odoo.code.timeline"]._ai_code_create_timeline(**kwargs)

    def _update(self, **kwargs):
        return self.env["odoo.code.timeline"]._ai_code_update_timeline(**kwargs)

    def test_create_model_cross_module(self):
        result = self._create(
            element_type="model",
            version="17.0",
            module="test_module_a",
            name="cross.old",
            next_module="test_module_b",
            next_name="cross.new",
            note="Moved to another module.",
        )
        self.assertIsNone(result["error"])
        timeline = result["timeline"]
        self.assertEqual(timeline["timeline_type"], "moved")
        self.assertEqual(timeline["next"]["module"], "test_module_b")
        self.assertEqual(timeline["next"]["version"], "18.0")
        self.assertEqual(timeline["next"]["name"], "cross.new")

    def test_create_model_version_gap(self):
        # Module 'test_module_gap' has no 18.0 branch: the target on 19.0 is
        # resolved through the next available version.
        result = self._create(
            element_type="model",
            version="17.0",
            module="test_module_gap",
            name="gap.old",
            next_name="gap.new",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["timeline"]["next"]["version"], "19.0")
        self.assertEqual(result["timeline"]["next"]["name"], "gap.new")

    def test_create_data_cross_module_same_local_id(self):
        # 'next_name' is omitted: the source XML ID is reused for the move
        result = self._create(
            element_type="data",
            version="17.0",
            module="test_module_a",
            name="cross_record",
            next_module="test_module_b",
            note="Data record moved to another module.",
        )
        self.assertIsNone(result["error"])
        next_ = result["timeline"]["next"]
        self.assertEqual(next_["module"], "test_module_b")
        self.assertEqual(next_["name"], "test_module_b.cross_record")

    def test_create_data_cross_module_full_xml_id_without_next_module(self):
        # The full XML ID alone identifies the target module when unambiguous
        result = self._create(
            element_type="data",
            version="17.0",
            module="test_module_a",
            name="cross_record",
            next_name="test_module_b.cross_record",
            note="Data record moved to another module.",
        )
        self.assertIsNone(result["error"])
        next_ = result["timeline"]["next"]
        self.assertEqual(next_["module"], "test_module_b")
        self.assertEqual(next_["name"], "test_module_b.cross_record")

    def test_create_data_cross_module_different_local_id(self):
        result = self._create(
            element_type="data",
            version="17.0",
            module="test_module_a",
            name="cross_record_renamed",
            next_module="test_module_b",
            next_name="cross_record_new",
            note="Data record moved and renamed.",
        )
        self.assertIsNone(result["error"])
        next_ = result["timeline"]["next"]
        self.assertEqual(next_["module"], "test_module_b")
        self.assertEqual(next_["name"], "test_module_b.cross_record_new")

    def test_create_data_override_full_xml_id(self):
        # The target XML ID is prefixed with another module: it must be
        # resolved as an override, not split on the dot.
        result = self._create(
            element_type="data",
            version="17.0",
            module="test_module_b",
            name="override_record",
            next_module="test_module_a",
            next_name="test_module_b.override_record",
            note="Data record moved to another module as an override.",
        )
        self.assertIsNone(result["error"])
        next_ = result["timeline"]["next"]
        self.assertEqual(next_["module"], "test_module_a")
        self.assertEqual(next_["name"], "test_module_b.override_record")

    def test_create_field_cross_module_and_model(self):
        result = self._create(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="cross.old",
            name="cross_field",
            next_module="test_module_b",
            next_model="cross.new",
            next_name="cross_field_new",
            note="Field moved to another model and module.",
        )
        self.assertIsNone(result["error"])
        next_ = result["timeline"]["next"]
        self.assertEqual(next_["module"], "test_module_b")
        self.assertEqual(next_["model"], "cross.new")
        self.assertEqual(next_["name"], "cross_field_new")

    def test_create_field_cross_model_same_module(self):
        result = self._create(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="cross.old",
            name="same_module_field",
            next_model="cross.new",
            next_name="same_module_field_new",
            note="Field moved to another model.",
        )
        self.assertIsNone(result["error"])
        next_ = result["timeline"]["next"]
        self.assertEqual(next_["module"], "test_module_a")
        self.assertEqual(next_["model"], "cross.new")
        self.assertEqual(next_["name"], "same_module_field_new")

    def test_create_field_pure_move_without_next_name(self):
        result = self._create(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="cross.old",
            name="pure_field",
            next_module="test_module_b",
            next_model="cross.new",
            note="Field moved to another model and module, same name.",
        )
        self.assertIsNone(result["error"])
        next_ = result["timeline"]["next"]
        self.assertEqual(next_["module"], "test_module_b")
        self.assertEqual(next_["model"], "cross.new")
        self.assertEqual(next_["name"], "pure_field")

    def test_create_many_to_one_merge(self):
        for name in ("merge_field_1", "merge_field_2"):
            result = self._create(
                element_type="field",
                version="17.0",
                module="test_module_a",
                model="cross.old",
                name=name,
                next_module="test_module_b",
                next_model="cross.new",
                next_name="merged_field",
                note="Field merged into merged_field.",
            )
            self.assertIsNone(result["error"])
            next_ = result["timeline"]["next"]
            self.assertEqual(next_["module"], "test_module_b")
            self.assertEqual(next_["model"], "cross.new")
            self.assertEqual(next_["name"], "merged_field")

    def test_create_split_is_rejected(self):
        # Phase 3 decision: one target per source, the other targets are
        # explained in the note.
        result = self._create(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="cross.old",
            name="split_field",
            next_module="test_module_b",
            next_model="cross.new",
            next_name="split_target_1",
            note="Split into split_target_1 and split_target_2.",
        )
        self.assertIsNone(result["error"])
        self.assertIn(
            "Split into split_target_1 and split_target_2.",
            result["timeline"]["note"],
        )
        result = self._create(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="cross.old",
            name="split_field",
            next_module="test_module_b",
            next_model="cross.new",
            next_name="split_target_2",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("already exists", result["error"])

    def test_update_target_module(self):
        result = self._create(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="cross.old",
            name="cross_field",
            next_model="cross.new",
            next_name="cross_field_new",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["timeline"]["next"]["module"], "test_module_a")
        # Only the target module changes: the target name/model are reused
        result = self._update(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="cross.old",
            name="cross_field",
            next_module="test_module_b",
        )
        self.assertIsNone(result["error"])
        next_ = result["timeline"]["next"]
        self.assertEqual(next_["module"], "test_module_b")
        self.assertEqual(next_["model"], "cross.new")
        self.assertEqual(next_["name"], "cross_field_new")

    def test_removed_rejects_target_scope(self):
        result = self._create(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="cross.old",
            name="remove_field",
            timeline_type="removed",
            next_module="test_module_b",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("not expected", result["error"])

    def test_next_model_rejected_for_model(self):
        result = self._create(
            element_type="model",
            version="17.0",
            module="test_module_a",
            name="cross.old",
            next_model="cross.new",
            next_name="cross.new",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("next_model", result["error"])

    def test_cross_repository_rejected(self):
        result = self._create(
            element_type="model",
            version="17.0",
            module="test_module_a",
            name="cross_repo.old",
            next_module="test_module_project",
            next_name="project.new",
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("cross-repository", result["error"])

    def test_next_version_follows_cross_module_data(self):
        result = self._create(
            element_type="data",
            version="17.0",
            module="test_module_a",
            name="cross_record",
            next_module="test_module_b",
            note=SOURCE_URL,
            confirm=True,
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["timeline"]["state"], "confirmed")
        result = self.env["odoo.module.branch"]._ai_code_get_next_version_element(
            element_type="data",
            version="17.0",
            module="test_module_a",
            name="cross_record",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["state"], "available")
        self.assertEqual(result["next"]["module"], "test_module_b")
        self.assertEqual(result["next"]["name"], "test_module_b.cross_record")
        self.assertEqual(result["timeline"]["type"], "moved")
        self.assertEqual(result["timeline"]["state"], "confirmed")

    def test_next_version_follows_cross_model_field(self):
        result = self._create(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="cross.old",
            name="cross_field",
            next_module="test_module_b",
            next_model="cross.new",
            next_name="cross_field_new",
            note=SOURCE_URL,
            confirm=True,
        )
        self.assertIsNone(result["error"])
        result = self.env["odoo.module.branch"]._ai_code_get_next_version_element(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="cross.old",
            name="cross_field",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["state"], "available")
        self.assertEqual(result["next"]["module"], "test_module_b")
        self.assertEqual(result["next"]["model"], "cross.new")
        self.assertEqual(result["next"]["name"], "cross_field_new")
        self.assertEqual(result["timeline"]["type"], "moved")
        self.assertEqual(result["timeline"]["target"]["model"], "cross.new")

    def test_history_follows_cross_module_data(self):
        result = self._create(
            element_type="data",
            version="17.0",
            module="test_module_a",
            name="cross_record",
            next_module="test_module_b",
            note=SOURCE_URL,
            confirm=True,
        )
        self.assertIsNone(result["error"])
        result = self.env["odoo.module.branch"]._ai_code_get_element_history(
            element_type="data",
            version="17.0",
            module="test_module_a",
            name="cross_record",
        )
        self.assertIsNone(result["error"])
        history = result["history"]
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["module"], "test_module_a")
        self.assertEqual(history[0]["name"], "test_module_a.cross_record")
        self.assertEqual(history[0]["timeline"]["type"], "moved")
        self.assertEqual(history[1]["module"], "test_module_b")
        self.assertEqual(history[1]["name"], "test_module_b.cross_record")
