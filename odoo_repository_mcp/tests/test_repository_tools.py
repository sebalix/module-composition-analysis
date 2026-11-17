# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import McpCommon


class TestRepositoryTools(McpCommon):
    def test_repo_list_versions(self):
        result = self.env["odoo.branch"]._ai_repo_list_versions()
        self.assertNotIn("error", result)
        versions = {version["name"]: version for version in result["versions"]}
        # The active branches are listed (the last 3 versions on a fresh db)
        self.assertIn("16.0", versions)
        self.assertIn("17.0", versions)
        self.assertIn("18.0", versions)
        self.assertEqual(versions["17.0"]["next"], "18.0")
        self.assertEqual(versions["17.0"]["previous"], "16.0")

    def test_repo_list_repositories(self):
        result = self.env["odoo.repository"]._ai_repo_list_repositories()
        self.assertNotIn("error", result)
        repositories = {repo["name"]: repo for repo in result["repositories"]}
        self.assertIn("test-repo", repositories)
        self.assertIn("project-repo", repositories)
        self.assertEqual(repositories["test-repo"]["org"], "TestOCA")
        self.assertEqual(set(repositories["test-repo"]["branches"]), {"17.0", "18.0"})
        self.assertFalse(repositories["test-repo"]["specific"])
        self.assertTrue(repositories["project-repo"]["specific"])

    def test_repo_list_repositories__org_filter(self):
        result = self.env["odoo.repository"]._ai_repo_list_repositories(org="TestOCA")
        self.assertNotIn("error", result)
        repositories = {repo["name"] for repo in result["repositories"]}
        self.assertEqual(repositories, {"test-repo"})

    def test_repo_list_repositories__unknown_org(self):
        result = self.env["odoo.repository"]._ai_repo_list_repositories(
            org="UnknownOrg"
        )
        self.assertIn("error", result)
