# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import CodeMigrationCommon


class TestCodeElementTimeline(CodeMigrationCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.module_branch2 = cls._create_odoo_module_branch(
            cls.module,
            cls.branch2,
            specific=False,
            repository_branch_id=cls.repo_branch2.id,
            last_scanned_commit="sha",
        )
        # Models with their own timelines
        cls.model_a = cls._create_odoo_module_branch_model(
            cls.module_branch, "my_module.model_a"
        )
        cls.model_b = cls._create_odoo_module_branch_model(
            cls.module_branch2, "my_module.model_b"
        )
        cls.timeline_model = cls._create_code_timeline(cls.model_a, cls.model_b)
        # Fields
        cls.field_a = cls._create_odoo_module_branch_model_field(cls.model_a, "field_a")
        cls.field_b = cls._create_odoo_module_branch_model_field(cls.model_b, "field_b")
        cls.field_model_only_a = cls._create_odoo_module_branch_model_field(
            cls.model_a, "model_only_field"
        )
        cls.field_draft_a = cls._create_odoo_module_branch_model_field(
            cls.model_a, "draft_field"
        )
        cls.field_draft_b = cls._create_odoo_module_branch_model_field(
            cls.model_b, "draft_field"
        )
        cls.timeline_field = cls._create_code_timeline(cls.field_a, cls.field_b)
        cls.timeline_draft = cls._create_code_timeline(
            cls.field_draft_a, cls.field_draft_b, state="draft"
        )
        # Methods
        cls.method_a = cls._create_odoo_module_branch_model_method(
            cls.model_a, "_method_a"
        )
        cls.method_b = cls._create_odoo_module_branch_model_method(
            cls.model_b, "_method_b"
        )
        cls.timeline_method = cls._create_code_timeline(cls.method_a, cls.method_b)
        # Data
        cls.data_a = cls._create_odoo_module_branch_data(
            cls.module_branch, "ir.ui.view", "view_a"
        )
        cls.data_b = cls._create_odoo_module_branch_data(
            cls.module_branch2, "ir.ui.view", "view_b"
        )
        cls.timeline_data = cls._create_code_timeline(cls.data_a, cls.data_b)

    def test_timeline_id_on_elements(self):
        # Outgoing confirmed timelines are linked from their source element
        self.assertEqual(self.field_a.timeline_id, self.timeline_field)
        self.assertEqual(self.method_a.timeline_id, self.timeline_method)
        self.assertEqual(self.data_a.timeline_id, self.timeline_data)
        self.assertEqual(self.model_a.timeline_id, self.timeline_model)
        # A draft timeline does not drive the link
        self.assertFalse(self.field_draft_a.timeline_id)
        # Only the source element is linked (no incoming timeline field)
        self.assertFalse(self.field_b.timeline_id)
        self.assertFalse(self.model_b.timeline_id)

    def test_model_timeline_id_on_field(self):
        # A field without its own timeline still exposes its model's timeline
        self.assertFalse(self.field_model_only_a.timeline_id)
        self.assertEqual(self.field_model_only_a.model_timeline_id, self.timeline_model)
        # A field with its own timeline on a model with one
        self.assertEqual(self.field_a.timeline_id, self.timeline_field)
        self.assertEqual(self.field_a.model_timeline_id, self.timeline_model)
        # The target model has no outgoing timeline
        self.assertFalse(self.field_b.model_timeline_id)

    def test_timeline_id_after_confirmation(self):
        self.assertFalse(self.field_draft_a.timeline_id)
        self.timeline_draft.action_confirm()
        self.assertEqual(self.field_draft_a.timeline_id, self.timeline_draft)
