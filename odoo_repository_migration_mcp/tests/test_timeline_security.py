# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.exceptions import AccessError

from .common import McpMigrationCommon


class TestTimelineSecurity(McpMigrationCommon):
    def test_write_requires_editor_group(self):
        timeline_model = self.env["odoo.module.branch.timeline"]
        values = {
            "module_branch_id": self.module_branch_b18.id,
            "next_module_id": self.module_c.id,
        }
        with self.assertRaises(AccessError):
            timeline_model.with_user(self.reader_user).create(dict(values))
        with self.assertRaises(AccessError):
            self.timeline_draft.with_user(self.reader_user).write({"note": "hack"})
        with self.assertRaises(AccessError):
            self.timeline_draft.with_user(self.reader_user).unlink()
        # A member of the editor group can create
        record = timeline_model.with_user(self.editor_user).create(
            dict(values, state="draft")
        )
        self.assertTrue(record.exists())
