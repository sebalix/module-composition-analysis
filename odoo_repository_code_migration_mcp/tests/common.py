# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import Command
from odoo.tests.common import TransactionCase


class McpCodeMigrationCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls._setup_mca_data()

    @classmethod
    def _activate_odoo_branch(cls, name):
        """Return the `odoo.branch` matching `name`, activated.

        The branch is created if it does not exist yet (branches are all
        pre-created by 'odoo_repository', archived but the last three).
        """
        branch = (
            cls.env["odoo.branch"]
            .with_context(active_test=False)
            .search([("name", "=", name)], limit=1)
        )
        if not branch:
            branch = cls.env["odoo.branch"].create({"name": name})
        branch.active = True
        return branch

    @classmethod
    def _create_module_branch(cls, module, branch, repository_branch, **values):
        vals = {
            "module_id": module.id,
            "branch_id": branch.id,
            "repository_branch_id": repository_branch.id,
        }
        vals.update(values)
        return cls.env["odoo.module.branch"].create(vals)

    @classmethod
    def _create_model_branch(cls, module_branch, model_version, **values):
        vals = {
            "module_branch_id": module_branch.id,
            "odoo_model_version_id": model_version.id,
            "model_type": "Model",
        }
        vals.update(values)
        return cls.env["odoo.module.branch.model"].create(vals)

    @classmethod
    def _create_field(cls, model_branch, name, field_type="Char", **values):
        vals = {
            "module_branch_model_id": model_branch.id,
            "name": name,
            "field_type": field_type,
        }
        vals.update(values)
        return cls.env["odoo.module.branch.model.field"].create(vals)

    @classmethod
    def _create_method(cls, model_branch, name, **values):
        vals = {
            "module_branch_model_id": model_branch.id,
            "name": name,
            "data": {"signature": ["self"]},
        }
        vals.update(values)
        return cls.env["odoo.module.branch.model.method"].create(vals)

    @classmethod
    def _create_data(cls, module_branch, model_version, name, xml_id, **values):
        vals = {
            "module_branch_id": module_branch.id,
            "odoo_model_version_id": model_version.id,
            "name": name,
            "xml_id": xml_id,
            "data_type": "data",
        }
        vals.update(values)
        return cls.env["odoo.module.branch.data"].create(vals)

    @classmethod
    def _setup_mca_data(cls):
        # Organizations and repositories
        cls.org_oca = cls.env["odoo.repository.org"].create({"name": "TestOCA"})
        cls.org_project = cls.env["odoo.repository.org"].create({"name": "TestProject"})
        cls.repo_oca = cls.env["odoo.repository"].create(
            {
                "org_id": cls.org_oca.id,
                "name": "test-repo",
                "repo_url": "https://github.com/TestOCA/test-repo",
            }
        )
        cls.repo_project = cls.env["odoo.repository"].create(
            {
                "org_id": cls.org_project.id,
                "name": "project-repo",
                "repo_url": "https://github.com/TestProject/project-repo",
                "specific": True,
            }
        )
        # Odoo versions
        cls.branch17 = cls._activate_odoo_branch("17.0")
        cls.branch18 = cls._activate_odoo_branch("18.0")
        # Repository branches
        cls.repo_branch_oca_17 = cls.env["odoo.repository.branch"].create(
            {"repository_id": cls.repo_oca.id, "branch_id": cls.branch17.id}
        )
        cls.repo_branch_oca_18 = cls.env["odoo.repository.branch"].create(
            {"repository_id": cls.repo_oca.id, "branch_id": cls.branch18.id}
        )
        cls.repo_branch_project_18 = cls.env["odoo.repository.branch"].create(
            {"repository_id": cls.repo_project.id, "branch_id": cls.branch18.id}
        )
        # Modules and module branches
        cls.module_a = cls.env["odoo.module"].create({"name": "test_module_a"})
        cls.module_branch_a17 = cls._create_module_branch(
            cls.module_a, cls.branch17, cls.repo_branch_oca_17
        )
        cls.module_branch_a18 = cls._create_module_branch(
            cls.module_a, cls.branch18, cls.repo_branch_oca_18
        )
        cls.module_branch_a18_project = cls._create_module_branch(
            cls.module_a, cls.branch18, cls.repo_branch_project_18
        )
        # Odoo models and their versions
        cls.odoo_model_partner = cls.env["odoo.model"].create({"name": "res.partner"})
        cls.odoo_model_old = cls.env["odoo.model"].create({"name": "old.model"})
        cls.odoo_model_new = cls.env["odoo.model"].create({"name": "new.model"})
        cls.model_version_partner_17 = cls.env["odoo.model.version"].create(
            {
                "odoo_model_id": cls.odoo_model_partner.id,
                "odoo_version_id": cls.branch17.id,
            }
        )
        cls.model_version_partner_18 = cls.env["odoo.model.version"].create(
            {
                "odoo_model_id": cls.odoo_model_partner.id,
                "odoo_version_id": cls.branch18.id,
            }
        )
        cls.model_version_old_17 = cls.env["odoo.model.version"].create(
            {
                "odoo_model_id": cls.odoo_model_old.id,
                "odoo_version_id": cls.branch17.id,
            }
        )
        cls.model_version_new_18 = cls.env["odoo.model.version"].create(
            {
                "odoo_model_id": cls.odoo_model_new.id,
                "odoo_version_id": cls.branch18.id,
            }
        )
        # Model elements
        cls.model_partner_17 = cls._create_model_branch(
            cls.module_branch_a17, cls.model_version_partner_17
        )
        cls.model_partner_18 = cls._create_model_branch(
            cls.module_branch_a18, cls.model_version_partner_18
        )
        cls.model_partner_18_project = cls._create_model_branch(
            cls.module_branch_a18_project, cls.model_version_partner_18
        )
        cls.model_old_17 = cls._create_model_branch(
            cls.module_branch_a17, cls.model_version_old_17
        )
        cls.model_new_18 = cls._create_model_branch(
            cls.module_branch_a18, cls.model_version_new_18
        )
        # Field elements
        cls.field_name_17 = cls._create_field(cls.model_partner_17, "name")
        cls.field_name_18 = cls._create_field(cls.model_partner_18, "name")
        cls.field_old_name_17 = cls._create_field(cls.model_partner_17, "old_name")
        cls.field_new_name_18 = cls._create_field(cls.model_partner_18, "new_name")
        cls.field_draft_17 = cls._create_field(cls.model_partner_17, "draft_field")
        cls.field_draft_18 = cls._create_field(cls.model_partner_18, "draft_field_new")
        # Method elements
        cls.method_compute_17 = cls._create_method(cls.model_partner_17, "_compute_x")
        cls.method_compute_18 = cls._create_method(cls.model_partner_18, "_compute_x")
        cls.method_removed_17 = cls._create_method(
            cls.model_partner_17, "_removed_method"
        )
        # Data elements
        cls.data_kept_17 = cls._create_data(
            cls.module_branch_a17,
            cls.model_version_partner_17,
            "Kept record",
            "kept_record",
        )
        cls.data_kept_18 = cls._create_data(
            cls.module_branch_a18,
            cls.model_version_partner_18,
            "Kept record",
            "kept_record",
        )
        cls.data_old_17 = cls._create_data(
            cls.module_branch_a17,
            cls.model_version_partner_17,
            "Old record",
            "old_record",
        )
        cls.data_new_18 = cls._create_data(
            cls.module_branch_a18,
            cls.model_version_partner_18,
            "New record",
            "new_record",
        )
        # Elements absent from the next version
        cls.field_gone_17 = cls._create_field(cls.model_partner_17, "gone_field")
        cls.method_gone_17 = cls._create_method(cls.model_partner_17, "_gone_method")
        cls.data_gone_17 = cls._create_data(
            cls.module_branch_a17,
            cls.model_version_partner_17,
            "Gone record",
            "gone_record",
        )
        cls.odoo_model_gone = cls.env["odoo.model"].create({"name": "gone.model"})
        cls.model_version_gone_17 = cls.env["odoo.model.version"].create(
            {
                "odoo_model_id": cls.odoo_model_gone.id,
                "odoo_version_id": cls.branch17.id,
            }
        )
        cls.model_gone_17 = cls._create_model_branch(
            cls.module_branch_a17, cls.model_version_gone_17
        )
        # Confirmed timelines
        cls.timeline_field = cls.env["odoo.code.timeline"].create(
            {
                "element_type": "field",
                "field_id": cls.field_old_name_17.id,
                "next_field_id": cls.field_new_name_18.id,
                "timeline_type": "moved",
                "state": "confirmed",
                "note": "Renamed upstream, see the commit abc123.",
            }
        )
        cls.timeline_method = cls.env["odoo.code.timeline"].create(
            {
                "element_type": "method",
                "method_id": cls.method_removed_17.id,
                "timeline_type": "removed",
                "state": "confirmed",
            }
        )
        cls.timeline_data = cls.env["odoo.code.timeline"].create(
            {
                "element_type": "data",
                "data_id": cls.data_old_17.id,
                "next_data_id": cls.data_new_18.id,
                "timeline_type": "moved",
                "state": "confirmed",
            }
        )
        cls.timeline_model = cls.env["odoo.code.timeline"].create(
            {
                "element_type": "model",
                "model_id": cls.model_old_17.id,
                "next_model_id": cls.model_new_18.id,
                "timeline_type": "moved",
                "state": "confirmed",
            }
        )
        # Draft timeline
        cls.timeline_draft = cls.env["odoo.code.timeline"].create(
            {
                "element_type": "field",
                "field_id": cls.field_draft_17.id,
                "next_field_id": cls.field_draft_18.id,
                "timeline_type": "moved",
                "state": "draft",
            }
        )
        # Users
        cls.reader_user = cls.env["res.users"].create(
            {
                "name": "MCP Reader",
                "login": "mcp_reader",
                "groups_id": [
                    Command.link(cls.env.ref("base.group_user").id),
                    Command.link(
                        cls.env.ref("odoo_repository.group_odoo_repository_user").id
                    ),
                ],
            }
        )
        cls.editor_user = cls.env["res.users"].create(
            {
                "name": "MCP Editor",
                "login": "mcp_editor",
                "groups_id": [
                    Command.link(cls.env.ref("base.group_user").id),
                    Command.link(
                        cls.env.ref("odoo_repository.group_odoo_repository_user").id
                    ),
                    Command.link(
                        cls.env.ref(
                            "odoo_repository_code_migration_mcp"
                            ".group_code_timeline_editor"
                        ).id
                    ),
                ],
            }
        )
