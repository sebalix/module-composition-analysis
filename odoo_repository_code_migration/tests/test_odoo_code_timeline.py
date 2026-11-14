# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.exceptions import ValidationError

from .common import CodeMigrationCommon


class TestOdooCodeTimeline(CodeMigrationCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Modules A, B and C (the base module is renamed to A, then to B, ...)
        cls.module_a = cls.module.copy({"name": "module_a"})
        cls.module_branch_a = cls._create_odoo_module_branch(
            cls.module_a,
            cls.branch,
            specific=False,
            repository_branch_id=cls.repo_branch.id,
        )
        cls.module_b = cls.module.copy({"name": "module_b"})
        cls.module_branch_b = cls._create_odoo_module_branch(
            cls.module_b,
            cls.branch2,
            specific=False,
            repository_branch_id=cls.repo_branch2.id,
        )
        cls.module_c = cls.module.copy({"name": "module_c"})
        cls.module_branch_c = cls._create_odoo_module_branch(
            cls.module_c,
            cls.branch3,
            specific=False,
            repository_branch_id=cls.repo_branch3.id,
        )
        # Models (A renamed to B in 16.0, B renamed to C in 17.0)
        cls.model_a = cls._create_odoo_module_branch_model(
            cls.module_branch_a, "my_module.model_a"
        )
        cls.model_b = cls._create_odoo_module_branch_model(
            cls.module_branch_b, "my_module.model_b"
        )
        cls.model_c = cls._create_odoo_module_branch_model(
            cls.module_branch_c, "my_module.model_c"
        )
        # Model A still exists (same name) in the renamed module (module B)
        cls.model_a2 = cls._create_odoo_module_branch_model(
            cls.module_branch_b, "my_module.model_a"
        )
        # Models of another history (D renamed to E)
        cls.model_d = cls._create_odoo_module_branch_model(
            cls.module_branch_a, "my_module.model_d"
        )
        cls.model_e = cls._create_odoo_module_branch_model(
            cls.module_branch_b, "my_module.model_e"
        )

    def test_element_constraint(self):
        """The element fields must match the element type and the state."""
        # Valid: renamed model
        timeline = self._create_code_timeline(self.model_a, self.model_b)
        self.assertEqual(timeline.element_type, "model")
        self.assertEqual(timeline.module_branch_id, self.module_branch_a)
        self.assertEqual(timeline.odoo_version_id, self.branch2)
        # Valid: removed model
        self._create_code_timeline(self.model_d, state="removed")
        # Invalid: missing element
        with self.assertRaises(ValidationError):
            self.env["odoo.code.timeline"].create(
                {"element_type": "model", "state": "renamed"}
            )
        # Invalid: renamed without new element
        with self.assertRaises(ValidationError):
            self.env["odoo.code.timeline"].create(
                {
                    "element_type": "model",
                    "state": "renamed",
                    "model_id": self.model_a.id,
                }
            )
        # Invalid: removed with a new element
        with self.assertRaises(ValidationError):
            self.env["odoo.code.timeline"].create(
                {
                    "element_type": "model",
                    "state": "removed",
                    "model_id": self.model_a.id,
                    "next_model_id": self.model_b.id,
                }
            )
        # Invalid: element not matching the element type
        with self.assertRaises(ValidationError):
            self.env["odoo.code.timeline"].create(
                {
                    "element_type": "data",
                    "state": "renamed",
                    "model_id": self.model_a.id,
                    "next_model_id": self.model_b.id,
                }
            )

    def test_display_name(self):
        """The display name shows the version and the elements."""
        timeline = self._create_code_timeline(self.model_a, self.model_b)
        self.assertEqual(
            timeline.display_name,
            f"[{self.branch2.name}] {self.model_a.display_name}"
            f" > {self.model_b.display_name}",
        )
        timeline_removed = self._create_code_timeline(self.model_d, state="removed")
        self.assertEqual(
            timeline_removed.display_name,
            f"[{self.branch2.name}] {self.model_d.display_name} > removed",
        )

    def test_get_related_code_timelines(self):
        """Test _get_related_code_timelines returns all timelines in a chain.

        Data input:
            - model A renamed to B in X+1
            - model B renamed to C in X+2
            - model D renamed to E in X+1 (other history)

        Expected output:
            - Calling _get_related_code_timelines on any timeline of a chain
              should return all the timelines of this chain
        """
        timeline_ab = self._create_code_timeline(self.model_a, self.model_b)
        timeline_bc = self._create_code_timeline(self.model_b, self.model_c)
        timeline_de = self._create_code_timeline(self.model_d, self.model_e)
        # Test from first timeline (A -> B)
        related_timelines = timeline_ab._get_related_code_timelines()
        self.assertIn(timeline_ab, related_timelines)
        self.assertIn(timeline_bc, related_timelines)
        self.assertNotIn(timeline_de, related_timelines)
        # Test from second timeline (B -> C)
        related_timelines = timeline_bc._get_related_code_timelines()
        self.assertIn(timeline_ab, related_timelines)
        self.assertIn(timeline_bc, related_timelines)
        self.assertNotIn(timeline_de, related_timelines)

    def test_next_odoo_version_model_renamed(self):
        """A renamed model jumps to the new model record."""
        self._create_code_timeline(self.model_a, self.model_b)
        self.assertEqual(self.model_a.next_odoo_version_model_id, self.model_b)
        # A renamed model is 'available' in the next version
        self.assertEqual(self.model_a.next_version_state, "available")

    def test_next_odoo_version_model_removed(self):
        """A removed model has no next version model."""
        self._create_code_timeline(self.model_a, state="removed")
        self.assertFalse(self.model_a.next_odoo_version_model_id)
        self.assertEqual(self.model_a.next_version_state, "removed")

    def test_next_odoo_version_model_module_rename(self):
        """The next version model follows the module renames."""
        # Module A renamed to module B starting from 16.0
        self._create_module_timeline(self.module_branch_a, self.module_b, "renamed")
        # The model exists in the renamed module (16.0): found
        model_y = self._create_odoo_module_branch_model(
            self.module_branch_a, "my_module.model_y"
        )
        model_y2 = self._create_odoo_module_branch_model(
            self.module_branch_b, "my_module.model_y"
        )
        self.assertEqual(model_y.next_odoo_version_model_id, model_y2)
        self.assertEqual(model_y.next_version_state, "available")
        # The model doesn't exist in the renamed module: not found, even if
        # another module provides a model with the same name later
        self._create_odoo_module_branch_model(self.module_branch_c, "my_module.model_x")
        model_x = self._create_odoo_module_branch_model(
            self.module_branch_a, "my_module.model_x"
        )
        self.assertFalse(model_x.next_odoo_version_model_id)
        self.assertEqual(model_x.next_version_state, "removed")

    def test_next_odoo_version_field_on_renamed_model(self):
        """A field that is not renamed follows the rename of its model."""
        field_x = self._create_odoo_module_branch_model_field(self.model_a, "field_x")
        field_x2 = self._create_odoo_module_branch_model_field(self.model_b, "field_x")
        field_y = self._create_odoo_module_branch_model_field(self.model_a, "field_y")
        # Without any declaration, the fields are not classifiable (the next
        # version of the module is not scanned)
        self.assertEqual(field_x.next_version_state, "unknown")
        self.assertEqual(field_y.next_version_state, "unknown")
        # Model A renamed to B in 16.0 (code timeline): the fields follow
        self._create_code_timeline(self.model_a, self.model_b)
        self.assertEqual(field_x.next_version_state, "available")
        self.assertEqual(field_x.next_odoo_version_field_id, field_x2)
        self.assertEqual(field_y.next_version_state, "removed")
        self.assertFalse(field_y.next_odoo_version_field_id)

    def test_next_odoo_version_field(self):
        """The next version field follows renames (field and module)."""
        # Module A renamed to module B starting from 16.0
        self._create_module_timeline(self.module_branch_a, self.module_b, "renamed")
        # The field exists in module A (15.0) and in module B (16.0): found
        field_x = self._create_odoo_module_branch_model_field(self.model_a, "field_x")
        field_x2 = self._create_odoo_module_branch_model_field(self.model_a2, "field_x")
        self.assertEqual(field_x.next_odoo_version_field_id, field_x2)
        self.assertEqual(field_x.next_version_state, "available")
        # The field doesn't exist in the renamed module: not found, even if
        # another module provides it later
        model_a3 = self._create_odoo_module_branch_model(
            self.module_branch_c, "my_module.model_a"
        )
        self._create_odoo_module_branch_model_field(model_a3, "field_y")
        field_y = self._create_odoo_module_branch_model_field(self.model_a, "field_y")
        self.assertFalse(field_y.next_odoo_version_field_id)
        self.assertEqual(field_y.next_version_state, "removed")
        # The field is renamed in 16.0 (code timeline): jump to the new field
        field_x3 = self._create_odoo_module_branch_model_field(
            self.model_a2, "field_x_renamed"
        )
        self._create_code_timeline(field_x, field_x3)
        self.assertEqual(field_x.next_odoo_version_field_id, field_x3)
        self.assertEqual(field_x.next_version_state, "available")
        # The field is removed in 16.0
        field_z = self._create_odoo_module_branch_model_field(self.model_a, "field_z")
        self._create_code_timeline(field_z, state="removed")
        self.assertFalse(field_z.next_odoo_version_field_id)
        self.assertEqual(field_z.next_version_state, "removed")

    def test_next_odoo_version_method(self):
        """The next version method follows renames (method and module)."""
        # Module A renamed to module B starting from 16.0
        self._create_module_timeline(self.module_branch_a, self.module_b, "renamed")
        # The method exists in module A (15.0) and module B (16.0): found
        method_x = self._create_odoo_module_branch_model_method(
            self.model_a, "method_x"
        )
        method_x2 = self._create_odoo_module_branch_model_method(
            self.model_a2, "method_x"
        )
        self.assertEqual(method_x.next_odoo_version_method_id, method_x2)
        self.assertEqual(method_x.next_version_state, "available")
        # The method is renamed in 16.0 (code timeline): jump to the new method
        method_x3 = self._create_odoo_module_branch_model_method(
            self.model_a2, "method_x_renamed"
        )
        self._create_code_timeline(method_x, method_x3)
        self.assertEqual(method_x.next_odoo_version_method_id, method_x3)
        self.assertEqual(method_x.next_version_state, "available")
        # The method is removed in 16.0
        method_y = self._create_odoo_module_branch_model_method(
            self.model_a, "method_y"
        )
        self._create_code_timeline(method_y, state="removed")
        self.assertFalse(method_y.next_odoo_version_method_id)
        self.assertEqual(method_y.next_version_state, "removed")

    def test_next_odoo_version_data(self):
        """The next version data follows renames (data and module)."""
        # Module A renamed to module B starting from 16.0
        self._create_module_timeline(self.module_branch_a, self.module_b, "renamed")
        # The data exists in module A (15.0) and module B (16.0): found
        data_x = self._create_odoo_module_branch_data(
            self.module_branch_a, "ir.ui.view", "data_x"
        )
        data_x2 = self._create_odoo_module_branch_data(
            self.module_branch_b, "ir.ui.view", "data_x"
        )
        self.assertEqual(data_x.next_odoo_version_data_id, data_x2)
        self.assertEqual(data_x.next_version_state, "available")
        # The data doesn't exist in the renamed module: removed
        data_y = self._create_odoo_module_branch_data(
            self.module_branch_a, "ir.ui.view", "data_y"
        )
        self.assertEqual(data_y.next_version_state, "removed")
        # The data is renamed in 16.0 (code timeline): jump to the new data
        data_x3 = self._create_odoo_module_branch_data(
            self.module_branch_b, "ir.ui.view", "data_x_renamed"
        )
        self._create_code_timeline(data_x, data_x3)
        self.assertEqual(data_x.next_odoo_version_data_id, data_x3)
        self.assertEqual(data_x.next_version_state, "available")
        # The data is removed in 16.0
        data_z = self._create_odoo_module_branch_data(
            self.module_branch_a, "ir.ui.view", "data_z"
        )
        self._create_code_timeline(data_z, state="removed")
        self.assertFalse(data_z.next_odoo_version_data_id)
        self.assertEqual(data_z.next_version_state, "removed")
