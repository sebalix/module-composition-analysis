# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import Command
from odoo.tests.common import TransactionCase


class McpMigrationCommon(TransactionCase):
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
        # Odoo versions (19.0 is created to test the timelines starting
        # from the last known version)
        cls.branch17 = cls._activate_odoo_branch("17.0")
        cls.branch18 = cls._activate_odoo_branch("18.0")
        cls.branch19 = cls._activate_odoo_branch("19.0")
        # Repository branches
        cls.repo_branch_oca_17 = cls.env["odoo.repository.branch"].create(
            {"repository_id": cls.repo_oca.id, "branch_id": cls.branch17.id}
        )
        cls.repo_branch_oca_18 = cls.env["odoo.repository.branch"].create(
            {"repository_id": cls.repo_oca.id, "branch_id": cls.branch18.id}
        )
        cls.repo_branch_project_17 = cls.env["odoo.repository.branch"].create(
            {"repository_id": cls.repo_project.id, "branch_id": cls.branch17.id}
        )
        # Technical modules
        cls.module_a = cls.env["odoo.module"].create({"name": "test_module_a"})
        cls.module_b = cls.env["odoo.module"].create({"name": "test_module_b"})
        cls.module_c = cls.env["odoo.module"].create({"name": "test_module_c"})
        # Module branches:
        # test_module_a is hosted twice on 17.0 (OCA + project forks)
        cls.module_branch_a17 = cls._create_module_branch(
            cls.module_a, cls.branch17, cls.repo_branch_oca_17
        )
        cls.module_branch_a17_project = cls._create_module_branch(
            cls.module_a, cls.branch17, cls.repo_branch_project_17
        )
        cls.module_branch_a18 = cls._create_module_branch(
            cls.module_a, cls.branch18, cls.repo_branch_oca_18
        )
        cls.module_branch_b18 = cls._create_module_branch(
            cls.module_b, cls.branch18, cls.repo_branch_oca_18
        )
        cls.module_branch_b17 = cls._create_module_branch(
            cls.module_b, cls.branch17, cls.repo_branch_oca_17
        )
        cls.module_branch_c17 = cls._create_module_branch(
            cls.module_c, cls.branch17, cls.repo_branch_oca_17
        )
        # Timelines (created before the migration data, as the confirmed
        # ones reset the migration data of the modules they impact)
        cls.timeline_draft = cls.env["odoo.module.branch.timeline"].create(
            {
                "module_branch_id": cls.module_branch_a17.id,
                "next_module_id": cls.module_b.id,
                "note": "Renamed upstream, see the project repository.",
            }
        )
        cls.timeline_confirmed = cls.env["odoo.module.branch.timeline"].create(
            {
                "module_branch_id": cls.module_branch_c17.id,
                "next_module_id": cls.module_a.id,
                "timeline_type": "replaced",
                "state": "confirmed",
            }
        )
        # Migration path and data
        cls.migration_path = cls.env["odoo.migration.path"].create(
            {
                "source_branch_id": cls.branch17.id,
                "target_branch_id": cls.branch18.id,
            }
        )
        cls.migration = cls.env["odoo.module.branch.migration"].create(
            {
                "module_branch_id": cls.module_branch_a17.id,
                "migration_path_id": cls.migration_path.id,
                "process": "migrate",
                "results": {},
                "last_source_scanned_commit": "s1" * 10,
                "last_target_scanned_commit": "t1" * 10,
            }
        )
        cls.migration_project = cls.env["odoo.module.branch.migration"].create(
            {
                "module_branch_id": cls.module_branch_a17_project.id,
                "migration_path_id": cls.migration_path.id,
                "process": "migrate",
                "results": {
                    "existing_pr": {
                        "url": "https://github.com/TestOCA/test-repo/pull/42",
                    },
                },
                "last_source_scanned_commit": "s2" * 10,
                "last_target_scanned_commit": "t2" * 10,
            }
        )
        # A migration with an existing PR on a generic repository is
        # 'review_migration'
        cls.migration_review = cls.env["odoo.module.branch.migration"].create(
            {
                "module_branch_id": cls.module_branch_b17.id,
                "migration_path_id": cls.migration_path.id,
                "process": "migrate",
                "results": {
                    "existing_pr": {
                        "url": "https://github.com/TestOCA/test-repo/pull/43",
                    },
                },
                "last_source_scanned_commit": "s3" * 10,
                "last_target_scanned_commit": "t3" * 10,
            }
        )
        # Editor group members
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
                            "odoo_repository_migration_mcp"
                            ".group_migration_timeline_editor"
                        ).id
                    ),
                ],
            }
        )
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
