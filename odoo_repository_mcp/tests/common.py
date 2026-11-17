# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import Command
from odoo.tests.common import TransactionCase


class McpCommon(TransactionCase):
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
    def _create_version(cls, module_branch, name, commit=None, **values):
        vals = {
            "module_branch_id": module_branch.id,
            "name": name,
            "manifest_value": name,
            "commit": commit,
        }
        vals.update(values)
        return cls.env["odoo.module.branch.version"].create(vals)

    @classmethod
    def _setup_mca_data(cls):
        # Reference data
        cls.category = cls.env["odoo.module.category"].create({"name": "Test Category"})
        cls.license = cls.env["odoo.license"].create({"name": "Test License"})
        cls.dev_status = cls.env["odoo.module.dev.status"].create({"name": "Beta"})
        cls.author = cls.env["odoo.author"].create({"name": "Test Author"})
        # Organizations and repositories
        cls.org_oca = cls.env["odoo.repository.org"].create({"name": "TestOCA"})
        cls.org_project = cls.env["odoo.repository.org"].create({"name": "TestProject"})
        cls.org_other = cls.env["odoo.repository.org"].create({"name": "TestOther"})
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
        cls.repo_other = cls.env["odoo.repository"].create(
            {
                "org_id": cls.org_other.id,
                "name": "other-repo",
                "repo_url": "https://github.com/TestOther/other-repo",
            }
        )
        # Odoo versions
        cls.branch16 = cls._activate_odoo_branch("16.0")
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
        cls.repo_branch_other_18 = cls.env["odoo.repository.branch"].create(
            {"repository_id": cls.repo_other.id, "branch_id": cls.branch18.id}
        )
        # Technical modules
        cls.module_a = cls.env["odoo.module"].create({"name": "test_module_a"})
        cls.module_b = cls.env["odoo.module"].create({"name": "test_module_b"})
        cls.module_c = cls.env["odoo.module"].create({"name": "test_module_c"})
        # Module branches
        cls.module_branch_a17 = cls._create_module_branch(
            cls.module_a, cls.branch17, cls.repo_branch_oca_17
        )
        cls.module_branch_a18 = cls._create_module_branch(
            cls.module_a,
            cls.branch18,
            cls.repo_branch_oca_18,
            title="Module A",
            summary="Test module A",
            category_id=cls.category.id,
            license_id=cls.license.id,
            development_status_id=cls.dev_status.id,
            author_ids=[Command.link(cls.author.id)],
        )
        cls.module_branch_a18_project = cls._create_module_branch(
            cls.module_a,
            cls.branch18,
            cls.repo_branch_project_18,
            title="Module A (fork)",
        )
        cls.module_branch_b18 = cls._create_module_branch(
            cls.module_b, cls.branch18, cls.repo_branch_oca_18, title="Module B"
        )
        cls.module_branch_c18 = cls._create_module_branch(
            cls.module_c, cls.branch18, cls.repo_branch_oca_18, title="Module C"
        )
        cls.module_branch_c18_other = cls._create_module_branch(
            cls.module_c, cls.branch18, cls.repo_branch_other_18, title="Module C"
        )
        # Dependencies: a18 -> b18 -> (c18, c18_other)
        cls.module_branch_a18.dependency_ids = [Command.link(cls.module_branch_b18.id)]
        cls.module_branch_b18.dependency_ids = [
            Command.link(cls.module_branch_c18.id),
            Command.link(cls.module_branch_c18_other.id),
        ]
        # Versions history
        cls._create_version(cls.module_branch_a17, "17.0.1.0.0", commit="a0" * 20)
        cls._create_version(cls.module_branch_a18, "18.0.1.0.0", commit="a1" * 20)
        cls._create_version(
            cls.module_branch_a18,
            "18.0.1.1.0",
            commit="a2" * 20,
            has_migration_script=True,
        )
        cls._create_version(
            cls.module_branch_a18_project, "18.0.1.0.0", commit="p1" * 20
        )
