# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models
from odoo.tools import html2plaintext

from odoo.addons.ai_tool.tools import aitool
from odoo.addons.odoo_repository_mcp.models.odoo_module_branch import _to_json_data

TIMELINE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "module": {"type": "string"},
        "version": {"type": "string"},
        "timeline_type": {"type": "string"},
        "state": {"type": "string"},
        "new_module": {"type": "string"},
        "starting_version": {"type": "string"},
        "note": {"type": "string"},
    },
}


class OdooModuleBranchTimeline(models.Model):
    _inherit = "odoo.module.branch.timeline"

    # ------------------------------------------------------------------
    # Shared glue for the MCP tools
    # ------------------------------------------------------------------

    def _mcp_to_dict(self):
        """Convert timeline data to a dictionary."""
        self.ensure_one()
        return _to_json_data(
            {
                "id": self.id,
                "module": self.module_branch_id.module_id.name,
                "version": self.module_branch_id.branch_id.name,
                "timeline_type": self.timeline_type,
                "state": self.state,
                "new_module": self.next_module_id.name,
                "starting_version": self.odoo_version_id.name,
                # The note is stored as HTML: return it as plain text
                "note": html2plaintext(self.note) if self.note else None,
            }
        )

    def _mcp_get_module_branch(self, module, version, repository=None):
        """Return the single `odoo.module.branch` of a module on a version.

        Raise an error when the module is not found on this version, or
        when it is hosted by several repositories and no `repository`
        disambiguates.
        """
        module_branch_model = self.env["odoo.module.branch"]
        module_ = module_branch_model._mcp_get_module(module)
        branch = module_branch_model._mcp_get_branch(version)
        module_branches = module_branch_model._mcp_get_module_branches(
            module_, branch, repository=repository
        )
        if not module_branches:
            raise ValueError(
                f"Module '{module}' not found for Odoo version '{version}'."
            )
        if len(module_branches) > 1:
            repositories = ", ".join(
                module_branches.mapped("repository_id.display_name")
            )
            raise ValueError(
                f"Module '{module}' is hosted by several repositories "
                f"for Odoo version '{version}': {repositories}. "
                "Please specify the 'repository' input."
            )
        return module_branches

    def _mcp_get_timeline(self, module, version, repository=None):
        """Return the timeline of a module on a version."""
        module_branch = self._mcp_get_module_branch(module, version, repository)
        timeline = self.search([("module_branch_id", "=", module_branch.id)])
        if not timeline:
            raise ValueError(
                f"No timeline for module '{module}' on version '{version}'."
            )
        return timeline

    # ------------------------------------------------------------------
    # MCP tools
    # ------------------------------------------------------------------

    @aitool(
        input_schema={
            "module": {
                "type": "string",
                "description": "Module technical name.",
            },
            "version": {
                "type": "string",
                "description": "Filter by the source module Odoo version.",
            },
            "state": {
                "type": "string",
                "enum": ["draft", "confirmed"],
                "description": "Filter by review state.",
            },
            "repository": {
                "type": "string",
                "description": "Filter by repository ('name' or 'org/name').",
            },
        },
        output_schema={
            "error": {"type": "string"},
            "timelines": {"type": "array", "items": TIMELINE_SCHEMA},
        },
    )
    def _ai_migration_list_timelines(
        self, module=None, version=None, state=None, repository=None
    ):
        """List the module renames/replacements declared in the database."""
        try:
            if state is not None and state not in ("draft", "confirmed"):
                raise ValueError(
                    f"Invalid 'state' value: '{state}' "
                    "(expected 'draft' or 'confirmed')."
                )
            module_branch_model = self.env["odoo.module.branch"]
            domain = []
            if module:
                domain.append(
                    (
                        "module_branch_id.module_id",
                        "=",
                        module_branch_model._mcp_get_module(module).id,
                    )
                )
            if version:
                domain.append(
                    (
                        "module_branch_id.branch_id",
                        "=",
                        module_branch_model._mcp_get_branch(version).id,
                    )
                )
            if state:
                domain.append(("state", "=", state))
            if repository:
                domain.append(
                    (
                        "repository_id",
                        "=",
                        module_branch_model._mcp_get_repository(repository).id,
                    )
                )
            timelines = self.search(domain)
            return {"timelines": [timeline._mcp_to_dict() for timeline in timelines]}
        except ValueError as error:
            return {"error": str(error)}

    @aitool(
        input_schema={
            "module": {
                "type": "string",
                "description": "Module technical name.",
            },
            "version": {
                "type": "string",
                "description": "Odoo version of the source module branch.",
            },
            "new_module": {
                "type": "string",
                "description": "Technical name of the new module.",
            },
            "timeline_type": {
                "type": "string",
                "enum": ["renamed", "replaced"],
                "description": "'renamed' (default) or 'replaced'.",
            },
            "note": {
                "type": "string",
                "description": (
                    "Plain text note. When known, mention the upstream "
                    "change justifying the rename/replacement (e.g. the "
                    "GitHub commit or PR URL) to help the reviewer."
                ),
            },
            "repository": {
                "type": "string",
                "description": (
                    "Restrict to one repository ('name' or 'org/name'). "
                    "Required when several repositories host the module."
                ),
            },
        },
        required_inputs=["module", "version", "new_module"],
        output_schema={
            "error": {"type": "string"},
            "timeline": TIMELINE_SCHEMA,
        },
    )
    def _ai_migration_create_timeline(
        self,
        module=None,
        version=None,
        new_module=None,
        timeline_type=None,
        note=None,
        repository=None,
    ):
        """Declare a module rename/replacement, as a draft timeline."""
        try:
            if not module or not version or not new_module:
                raise ValueError(
                    "'module', 'version' and 'new_module' are required inputs."
                )
            if timeline_type not in (None, "renamed", "replaced"):
                raise ValueError(
                    f"Invalid 'timeline_type' value: '{timeline_type}' "
                    "(expected 'renamed' or 'replaced')."
                )
            module_branch_model = self.env["odoo.module.branch"]
            module_branch = self._mcp_get_module_branch(
                module, version, repository=repository
            )
            existing = self.search([("module_branch_id", "=", module_branch.id)])
            if existing:
                raise ValueError(
                    f"A timeline already exists for module '{module}' on "
                    f"version '{version}'."
                )
            timeline = self.create(
                {
                    "module_branch_id": module_branch.id,
                    "next_module_id": module_branch_model._mcp_get_module(
                        new_module
                    ).id,
                    "timeline_type": timeline_type or "renamed",
                    "note": note or False,
                    # Proposal only: applied to the analysis once confirmed
                    # by a human
                    "state": "draft",
                }
            )
            return {"timeline": timeline._mcp_to_dict()}
        except ValueError as error:
            return {"error": str(error)}

    @aitool(
        input_schema={
            "module": {
                "type": "string",
                "description": "Module technical name.",
            },
            "version": {
                "type": "string",
                "description": "Odoo version of the source module branch.",
            },
            "new_module": {
                "type": "string",
                "description": "New technical name of the module.",
            },
            "timeline_type": {
                "type": "string",
                "enum": ["renamed", "replaced"],
                "description": "New type of the timeline.",
            },
            "note": {
                "type": "string",
                "description": (
                    "Plain text note. When known, mention the upstream "
                    "change justifying the rename/replacement (e.g. the "
                    "GitHub commit or PR URL) to help the reviewer."
                ),
            },
            "repository": {
                "type": "string",
                "description": (
                    "Restrict to one repository ('name' or 'org/name'). "
                    "Required when several repositories host the module."
                ),
            },
        },
        required_inputs=["module", "version"],
        output_schema={
            "error": {"type": "string"},
            "timeline": TIMELINE_SCHEMA,
        },
    )
    def _ai_migration_update_timeline(
        self,
        module=None,
        version=None,
        new_module=None,
        timeline_type=None,
        note=None,
        repository=None,
    ):
        """Update a draft timeline proposal."""
        try:
            if not module or not version:
                raise ValueError("'module' and 'version' are required inputs.")
            if timeline_type not in (None, "renamed", "replaced"):
                raise ValueError(
                    f"Invalid 'timeline_type' value: '{timeline_type}' "
                    "(expected 'renamed' or 'replaced')."
                )
            timeline = self._mcp_get_timeline(module, version, repository)
            if timeline.state != "draft":
                raise ValueError(
                    f"The timeline of module '{module}' on version "
                    f"'{version}' is confirmed: only draft timelines can "
                    "be updated (managed by humans in the UI)."
                )
            values = {}
            if new_module is not None:
                if new_module == module:
                    raise ValueError(
                        "The new module must be different from the module."
                    )
                values["next_module_id"] = (
                    self.env["odoo.module.branch"]._mcp_get_module(new_module).id
                )
            if timeline_type is not None:
                values["timeline_type"] = timeline_type
            if note is not None:
                values["note"] = note
            if not values:
                raise ValueError(
                    "No field to update: provide 'new_module', "
                    "'timeline_type' or 'note'."
                )
            timeline.write(values)
            return {"timeline": timeline._mcp_to_dict()}
        except ValueError as error:
            return {"error": str(error)}

    @aitool(
        input_schema={
            "module": {
                "type": "string",
                "description": "Module technical name.",
            },
            "version": {
                "type": "string",
                "description": "Odoo version of the source module branch.",
            },
            "repository": {
                "type": "string",
                "description": (
                    "Restrict to one repository ('name' or 'org/name'). "
                    "Required when several repositories host the module."
                ),
            },
        },
        required_inputs=["module", "version"],
        output_schema={
            "error": {"type": "string"},
            "deleted": {"type": "boolean"},
        },
    )
    def _ai_migration_delete_timeline(self, module=None, version=None, repository=None):
        """Delete a draft timeline proposal."""
        try:
            if not module or not version:
                raise ValueError("'module' and 'version' are required inputs.")
            timeline = self._mcp_get_timeline(module, version, repository)
            if timeline.state != "draft":
                raise ValueError(
                    f"The timeline of module '{module}' on version "
                    f"'{version}' is confirmed: only draft timelines can "
                    "be deleted (managed by humans in the UI)."
                )
            timeline.unlink()
            return {"deleted": True}
        except ValueError as error:
            return {"error": str(error)}
