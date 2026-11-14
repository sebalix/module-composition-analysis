# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.odoo_repository_migration.tests.common import MigrationCommon


class CodeMigrationCommon(MigrationCommon):
    def _get_module_branch(self):
        """Return the module branch of the fixture module on the first branch."""
        module = self.env["odoo.module"].search([("name", "=", self.module_name)])
        return self.env["odoo.module.branch"].search(
            [("module_id", "=", module.id), ("branch_id", "=", self.branch.id)]
        )

    def _get_data(self, module_branch, xml_id):
        """Return the data record, archived records included."""
        return (
            self.env["odoo.module.branch.data"]
            .with_context(active_test=False)
            .search(
                [
                    ("module_branch_id", "=", module_branch.id),
                    ("xml_id", "=", xml_id),
                ]
            )
        )

    @classmethod
    def _get_or_create_odoo_model_version(cls, model_name, branch):
        """Return the `odoo.model.version` record for a model name and branch."""
        odoo_model = cls.env["odoo.model"].search([("name", "=", model_name)])
        if not odoo_model:
            odoo_model = cls.env["odoo.model"].create({"name": model_name})
        model_version = cls.env["odoo.model.version"].search(
            [
                ("odoo_model_id", "=", odoo_model.id),
                ("odoo_version_id", "=", branch.id),
            ]
        )
        if not model_version:
            model_version = cls.env["odoo.model.version"].create(
                {"odoo_model_id": odoo_model.id, "odoo_version_id": branch.id}
            )
        return model_version

    @classmethod
    def _create_odoo_module_branch_model(cls, module_branch, model_name, **values):
        model_version = cls._get_or_create_odoo_model_version(
            model_name, module_branch.branch_id
        )
        vals = {
            "module_branch_id": module_branch.id,
            "odoo_model_version_id": model_version.id,
            "model_type": "Model",
        }
        vals.update(values)
        return cls.env["odoo.module.branch.model"].create(vals)

    @classmethod
    def _create_odoo_module_branch_model_field(
        cls, module_branch_model, name, **values
    ):
        vals = {
            "module_branch_model_id": module_branch_model.id,
            "name": name,
            "field_type": "Char",
        }
        vals.update(values)
        return cls.env["odoo.module.branch.model.field"].create(vals)

    @classmethod
    def _create_odoo_module_branch_model_method(
        cls, module_branch_model, name, **values
    ):
        vals = {"module_branch_model_id": module_branch_model.id, "name": name}
        vals.update(values)
        return cls.env["odoo.module.branch.model.method"].create(vals)

    @classmethod
    def _create_odoo_module_branch_data(
        cls, module_branch, model_name, xml_id, **values
    ):
        model_version = cls._get_or_create_odoo_model_version(
            model_name, module_branch.branch_id
        )
        vals = {
            "module_branch_id": module_branch.id,
            "odoo_model_version_id": model_version.id,
            "xml_id": xml_id,
            "name": xml_id,
        }
        vals.update(values)
        return cls.env["odoo.module.branch.data"].create(vals)

    @classmethod
    def _create_code_timeline(
        cls, element, next_element=None, state="renamed", **values
    ):
        element_type = cls.env["odoo.code.timeline"]._get_element_type(element._name)
        vals = {
            "element_type": element_type,
            "state": state,
            f"{element_type}_id": element.id,
        }
        if next_element:
            vals[f"next_{element_type}_id"] = next_element.id
        vals.update(values)
        return cls.env["odoo.code.timeline"].create(vals)
