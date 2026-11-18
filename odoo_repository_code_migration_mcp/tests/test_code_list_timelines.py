# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import McpCodeMigrationCommon


class TestCodeListTimelines(McpCodeMigrationCommon):
    def test_list(self):
        result = self.env["odoo.code.timeline"]._ai_code_list_timelines()
        self.assertIsNone(result["error"])
        self.assertEqual(result["total"], 5)
        self.assertEqual(len(result["timelines"]), 5)
        by_name = {
            (timeline["element_type"], timeline["name"]): timeline
            for timeline in result["timelines"]
        }
        field = by_name[("field", "old_name")]
        self.assertEqual(field["module"], "test_module_a")
        self.assertEqual(field["version"], "17.0")
        self.assertEqual(field["model"], "res.partner")
        self.assertEqual(field["timeline_type"], "moved")
        self.assertEqual(field["state"], "confirmed")
        self.assertEqual(field["next"]["name"], "new_name")
        self.assertEqual(field["starting_version"], "18.0")
        self.assertIn("Renamed upstream, see the commit abc123.", field["note"])
        self.assertIn("<p>", field["note"])
        method = by_name[("method", "_removed_method")]
        self.assertEqual(method["timeline_type"], "removed")
        self.assertIsNone(method["next"])

    def test_list__filters(self):
        model = self.env["odoo.code.timeline"]
        result = model._ai_code_list_timelines(state="draft")
        self.assertEqual(len(result["timelines"]), 1)
        self.assertEqual(result["timelines"][0]["name"], "draft_field")
        result = model._ai_code_list_timelines(state="confirmed")
        self.assertEqual(len(result["timelines"]), 4)
        result = model._ai_code_list_timelines(element_type="model")
        self.assertEqual(len(result["timelines"]), 1)
        result = model._ai_code_list_timelines(module="test_module_a")
        self.assertEqual(len(result["timelines"]), 5)
        result = model._ai_code_list_timelines(version="18.0")
        self.assertEqual(result["timelines"], [])
        result = model._ai_code_list_timelines(repository="TestProject/project-repo")
        self.assertEqual(result["timelines"], [])

    def test_list__pagination(self):
        model = self.env["odoo.code.timeline"]
        result = model._ai_code_list_timelines(limit=2)
        self.assertEqual(result["total"], 5)
        self.assertEqual(len(result["timelines"]), 2)
        result = model._ai_code_list_timelines(limit=2, offset=4)
        self.assertEqual(result["total"], 5)
        self.assertEqual(len(result["timelines"]), 1)

    def test_list__timeline_type(self):
        model = self.env["odoo.code.timeline"]
        result = model._ai_code_list_timelines(timeline_type="moved")
        self.assertEqual(result["total"], 4)
        result = model._ai_code_list_timelines(timeline_type="removed")
        self.assertEqual(result["total"], 1)

    def test_list__invalid_params(self):
        model = self.env["odoo.code.timeline"]
        result = model._ai_code_list_timelines(state="published")
        self.assertIsNotNone(result["error"])
        result = model._ai_code_list_timelines(limit=0)
        self.assertIsNotNone(result["error"])
        result = model._ai_code_list_timelines(module="unknown_module")
        self.assertIsNotNone(result["error"])
