# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tests.common import TransactionCase


class McpCodeCommon(TransactionCase):
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
        cls.repo_branch_oca_18 = cls.env["odoo.repository.branch"].create(
            {"repository_id": cls.repo_oca.id, "branch_id": cls.branch18.id}
        )
        cls.repo_branch_project_18 = cls.env["odoo.repository.branch"].create(
            {"repository_id": cls.repo_project.id, "branch_id": cls.branch18.id}
        )
        # Modules and module branches
        cls.module_a = cls.env["odoo.module"].create({"name": "test_module_a"})
        cls.module_branch_a18 = cls._create_module_branch(
            cls.module_a, cls.branch18, cls.repo_branch_oca_18
        )
        cls.module_branch_a18_project = cls._create_module_branch(
            cls.module_a, cls.branch18, cls.repo_branch_project_18
        )
        # Odoo models and their versions
        cls.odoo_model_partner = cls.env["odoo.model"].create({"name": "res.partner"})
        cls.odoo_model_sale = cls.env["odoo.model"].create({"name": "sale.order"})
        cls.model_version_partner = cls.env["odoo.model.version"].create(
            {
                "odoo_model_id": cls.odoo_model_partner.id,
                "odoo_version_id": cls.branch18.id,
            }
        )
        cls.model_version_sale = cls.env["odoo.model.version"].create(
            {
                "odoo_model_id": cls.odoo_model_sale.id,
                "odoo_version_id": cls.branch18.id,
            }
        )
        # The inherited models are resolved through their 'odoo.model.version'
        cls.odoo_model_base = cls.env["odoo.model"].create({"name": "models.Model"})
        cls.model_version_base = cls.env["odoo.model.version"].create(
            {
                "odoo_model_id": cls.odoo_model_base.id,
                "odoo_version_id": cls.branch18.id,
            }
        )
        # Model elements
        cls.model_partner = cls.env["odoo.module.branch.model"].create(
            {
                "module_branch_id": cls.module_branch_a18.id,
                "odoo_model_version_id": cls.model_version_partner.id,
                "model_type": "Model",
                "order": "name",
                "data": {"inherit": ["models.Model"]},
            }
        )
        cls.model_sale = cls.env["odoo.module.branch.model"].create(
            {
                "module_branch_id": cls.module_branch_a18.id,
                "odoo_model_version_id": cls.model_version_sale.id,
                "model_type": "Model",
                "data": {"inherit": ["models.Model"]},
            }
        )
        cls.model_partner_project = cls.env["odoo.module.branch.model"].create(
            {
                "module_branch_id": cls.module_branch_a18_project.id,
                "odoo_model_version_id": cls.model_version_partner.id,
                "model_type": "Model",
                "data": {"inherit": ["models.Model"]},
            }
        )
        # Field elements
        cls.field_partner_id = cls.env["odoo.module.branch.model.field"].create(
            {
                "module_branch_model_id": cls.model_partner.id,
                "name": "partner_id",
                "field_type": "Many2one",
                "data": {
                    "comodel_name": "res.partner",
                    "code": "partner_id = fields.Many2one('res.partner')",
                },
            }
        )
        cls.field_name = cls.env["odoo.module.branch.model.field"].create(
            {
                "module_branch_model_id": cls.model_partner.id,
                "name": "name",
                "field_type": "Char",
                "data": {"code": "name = fields.Char()"},
            }
        )
        # Method elements
        cls.method_compute = cls.env["odoo.module.branch.model.method"].create(
            {
                "module_branch_model_id": cls.model_partner.id,
                "name": "_compute_display_name",
                "data": {
                    "signature": ["self"],
                    "decorators": ["api.depends('name')"],
                    "code": "def _compute_display_name(self):\n    pass",
                },
            }
        )
        # Data elements
        cls.data_partner = cls.env["odoo.module.branch.data"].create(
            {
                "module_branch_id": cls.module_branch_a18.id,
                "odoo_model_version_id": cls.model_version_partner.id,
                "name": "Partner record",
                "xml_id": "partner_test",
                "data_type": "data",
                "loaded": True,
                "noupdate": True,
                "file_path": "data/partner.xml",
                "data": {
                    "model": "res.partner",
                    "xml": "<record id='partner_test'/>",
                },
            }
        )
