# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import McpCommon


class TestModuleTools(McpCommon):
    """Test the module tools on their own (no HTTP layer involved)."""

    def test_module_search__by_name(self):
        result = self.env["odoo.module.branch"]._ai_module_search(name="test_module_a")
        self.assertIsNone(result["error"])
        # test_module_a exists on 17.0 and 18.0 (twice: OCA + project repos)
        self.assertEqual(result["total"], 3)
        modules = {module["module"] for module in result["modules"]}
        self.assertEqual(modules, {"test_module_a"})

    def test_module_search__by_version(self):
        result = self.env["odoo.module.branch"]._ai_module_search(version="18.0")
        self.assertIsNone(result["error"])
        self.assertEqual(result["total"], 5)
        modules = {module["module"] for module in result["modules"]}
        self.assertEqual(modules, {"test_module_a", "test_module_b", "test_module_c"})

    def test_module_search__by_org(self):
        result = self.env["odoo.module.branch"]._ai_module_search(org="TestOCA")
        self.assertIsNone(result["error"])
        self.assertEqual(result["total"], 4)

    def test_module_search__by_repository(self):
        result = self.env["odoo.module.branch"]._ai_module_search(
            repository="TestOCA/test-repo"
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["total"], 4)

    def test_module_search__by_category_and_author(self):
        result = self.env["odoo.module.branch"]._ai_module_search(
            category="Test Category"
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["modules"][0]["module"], "test_module_a")
        result = self.env["odoo.module.branch"]._ai_module_search(author="Test Author")
        self.assertIsNone(result["error"])
        self.assertEqual(result["total"], 1)

    def test_module_search__summary_values(self):
        result = self.env["odoo.module.branch"]._ai_module_search(name="test_module_b")
        module = result["modules"][0]
        self.assertEqual(module["version"], "18.0")
        self.assertEqual(module["org"], "TestOCA")
        self.assertEqual(module["repository"], "test-repo")
        self.assertEqual(module["title"], "Module B")
        self.assertFalse(module["removed"])

    def test_module_search__unknown_filters(self):
        for kwargs in (
            {"version": "99.0"},
            {"org": "UnknownOrg"},
            {"repository": "unknown-repo"},
            {"category": "Unknown Category"},
            {"author": "Unknown Author"},
        ):
            result = self.env["odoo.module.branch"]._ai_module_search(**kwargs)
            self.assertIsNotNone(result["error"], kwargs)

    def test_module_search__pagination(self):
        model = self.env["odoo.module.branch"]
        result = model._ai_module_search(version="18.0", limit=2)
        self.assertEqual(result["total"], 5)
        self.assertEqual(len(result["modules"]), 2)
        result = model._ai_module_search(version="18.0", limit=2, offset=4)
        self.assertEqual(result["total"], 5)
        self.assertEqual(len(result["modules"]), 1)

    def test_module_search__invalid_pagination(self):
        model = self.env["odoo.module.branch"]
        for kwargs in ({"limit": 0}, {"limit": -1}, {"offset": -1}, {"limit": "NaN"}):
            result = model._ai_module_search(**kwargs)
            self.assertIsNotNone(result["error"], kwargs)

    def test_module_search__ambiguous_repository(self):
        # A second organization using the same repository name
        org = self.env["odoo.repository.org"].create({"name": "TestFork"})
        self.env["odoo.repository"].create(
            {
                "org_id": org.id,
                "name": "test-repo",
                "repo_url": "https://github.com/TestFork/test-repo",
            }
        )
        result = self.env["odoo.module.branch"]._ai_module_search(
            repository="test-repo"
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("ambiguous", result["error"])
        # The 'org/name' format disambiguates
        result = self.env["odoo.module.branch"]._ai_module_search(
            repository="TestOCA/test-repo"
        )
        self.assertIsNone(result["error"])

    def test_module_get_details__all_occurrences(self):
        result = self.env["odoo.module.branch"]._ai_module_get_details(
            module="test_module_a", version="18.0"
        )
        self.assertIsNone(result["error"])
        self.assertEqual(len(result["modules"]), 2)
        repositories = {module["repository"]["name"] for module in result["modules"]}
        self.assertEqual(repositories, {"test-repo", "project-repo"})

    def test_module_get_details__values(self):
        result = self.env["odoo.module.branch"]._ai_module_get_details(
            module="test_module_a", version="18.0", repository="TestOCA/test-repo"
        )
        self.assertIsNone(result["error"])
        self.assertEqual(len(result["modules"]), 1)
        module = result["modules"][0]
        self.assertEqual(module["module"], "test_module_a")
        self.assertEqual(module["branch"], "18.0")
        self.assertEqual(module["title"], "Module A")
        self.assertEqual(module["depends"], ["test_module_b"])
        self.assertEqual(module["authors"], ["Test Author"])
        self.assertEqual(module["license"], "Test License")
        self.assertEqual(len(module["versions"]), 2)
        self.assertIn("test_module_a", module["url"])

    def test_module_get_details__not_found(self):
        result = self.env["odoo.module.branch"]._ai_module_get_details(
            module="test_module_c", version="17.0"
        )
        self.assertIsNotNone(result["error"])
        result = self.env["odoo.module.branch"]._ai_module_get_details(
            module="unknown_module", version="18.0"
        )
        self.assertIsNotNone(result["error"])

    def test_module_get_details__missing_inputs(self):
        result = self.env["odoo.module.branch"]._ai_module_get_details(
            module="test_module_a"
        )
        self.assertIsNotNone(result["error"])

    def test_module_get_dependencies__direct(self):
        result = self.env["odoo.module.branch"]._ai_module_get_dependencies(
            module="test_module_a",
            version="18.0",
            repository="TestOCA/test-repo",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["dependencies"][0]["module"], "test_module_b")

    def test_module_get_dependencies__recursive(self):
        result = self.env["odoo.module.branch"]._ai_module_get_dependencies(
            module="test_module_a",
            version="18.0",
            repository="TestOCA/test-repo",
            scope="recursive",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["total"], 3)
        modules = {dep["module"] for dep in result["dependencies"]}
        self.assertEqual(modules, {"test_module_b", "test_module_c"})

    def test_module_get_dependencies__reverse(self):
        model = self.env["odoo.module.branch"]
        result = model._ai_module_get_dependencies(
            module="test_module_c",
            version="18.0",
            repository="TestOCA/test-repo",
            direction="reverse",
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["dependencies"][0]["module"], "test_module_b")
        result = model._ai_module_get_dependencies(
            module="test_module_c",
            version="18.0",
            repository="TestOCA/test-repo",
            direction="reverse",
            scope="recursive",
        )
        self.assertIsNone(result["error"])
        modules = {dep["module"] for dep in result["dependencies"]}
        self.assertEqual(modules, {"test_module_a", "test_module_b"})

    def test_module_get_dependencies__org_filter(self):
        result = self.env["odoo.module.branch"]._ai_module_get_dependencies(
            module="test_module_b", version="18.0", org="TestOther"
        )
        self.assertIsNone(result["error"])
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["dependencies"][0]["module"], "test_module_c")
        self.assertEqual(result["dependencies"][0]["repository"], "other-repo")

    def test_module_get_dependencies__multiple_repositories(self):
        # test_module_a is hosted twice on 18.0: the 'repository' input is
        # required to know which occurrence to look at
        result = self.env["odoo.module.branch"]._ai_module_get_dependencies(
            module="test_module_a", version="18.0"
        )
        self.assertIsNotNone(result["error"])
        self.assertIn("TestOCA/test-repo", result["error"])
        self.assertIn("TestProject/project-repo", result["error"])

    def test_module_get_dependencies__invalid_params(self):
        model = self.env["odoo.module.branch"]
        result = model._ai_module_get_dependencies(
            module="test_module_b",
            version="18.0",
            direction="sideways",
        )
        self.assertIsNotNone(result["error"])
        result = model._ai_module_get_dependencies(
            module="test_module_b",
            version="18.0",
            scope="everything",
        )
        self.assertIsNotNone(result["error"])

    def test_module_list_versions(self):
        result = self.env["odoo.module.branch"]._ai_module_list_versions(
            module="test_module_a"
        )
        self.assertIsNone(result["error"])
        self.assertEqual(len(result["versions"]), 4)
        versions = {
            (version["version"], version["repository"])
            for version in result["versions"]
        }
        self.assertEqual(
            versions,
            {
                ("17.0", "test-repo"),
                ("18.0", "test-repo"),
                ("18.0", "project-repo"),
            },
        )
        scripts = [
            version for version in result["versions"] if version["has_migration_script"]
        ]
        self.assertEqual(len(scripts), 1)
        self.assertEqual(scripts[0]["manifest_version"], "18.0.1.1.0")
        self.assertEqual(scripts[0]["commit"], "a2" * 20)

    def test_module_list_versions__unknown_module(self):
        result = self.env["odoo.module.branch"]._ai_module_list_versions(
            module="unknown_module"
        )
        self.assertIsNotNone(result["error"])
        result = self.env["odoo.module.branch"]._ai_module_list_versions()
        self.assertIsNotNone(result["error"])
