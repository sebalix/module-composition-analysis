# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from typing import Literal

from pydantic import BaseModel, Field

from odoo import models

from odoo.addons.odoo_repository_mcp.utils import (
    NullableStr,
    check_source_of_truth,
    mcp_tool,
)


class Timeline(BaseModel):
    """Timeline (rename/replacement/removal proposal) of a module."""

    id: int
    module: str = Field(description="Module technical name.")
    version: str = Field(description="Odoo version of the source module branch.")
    timeline_type: str = Field(description="'renamed', 'replaced' or 'removed'.")
    state: str = Field(description="Review state: 'draft' or 'confirmed'.")
    new_module: NullableStr = Field(
        default=None,
        description=(
            "New module technical name ('removed' timelines have no new module)."
        ),
    )
    starting_version: NullableStr = None
    note: NullableStr = Field(
        default=None,
        description="HTML note explaining the module move/replacement/removal.",
    )


class TimelineListInput(BaseModel):
    """Inputs of the `migration_list_timelines` tool."""

    module: str | None = Field(default=None, description="Module technical name.")
    version: str | None = Field(
        default=None, description="Filter by the source module Odoo version."
    )
    state: Literal["draft", "confirmed"] | None = Field(
        default=None, description="Filter by review state."
    )
    repository: str | None = Field(
        default=None, description="Filter by repository ('name' or 'org/name')."
    )


class TimelineListOutput(BaseModel):
    """Output of the `migration_list_timelines` tool."""

    error: str | None = None
    timelines: list[Timeline]


class TimelineCreateInput(BaseModel):
    """Inputs of the `migration_create_timeline` tool."""

    module: str = Field(description="Module technical name.")
    version: str = Field(description="Odoo version of the source module branch.")
    new_module: str | None = Field(
        default=None,
        description=(
            "Technical name of the new module. Required for 'renamed' and "
            "'replaced' timelines, forbidden for 'removed' ones."
        ),
    )
    timeline_type: Literal["renamed", "replaced", "removed"] | None = Field(
        default=None,
        description=(
            "'renamed' (default), 'replaced', or 'removed' when the module "
            "disappeared without any successor."
        ),
    )
    note: str | None = Field(
        default=None,
        description=(
            "HTML note. Start the visible text with '[HIGHLY-CONFIDENT]' "
            "or '[LESS-CONFIDENT]', explain the change, then end with a "
            "bulleted Source section: "
            "'<br/>Source:<br/>- <a href=\"URL\">URL</a>' for each link. "
            "Put the full URL as link text, commit first; do not use "
            "Markdown."
        ),
        examples=[
            (
                "<p>[HIGHLY-CONFIDENT] Module renamed.<br/>Source:"
                '<br/>- <a href="https://github.com/odoo/odoo/commit/abc123">'
                "https://github.com/odoo/odoo/commit/abc123</a>"
                '<br/>- <a href="https://github.com/OCA/OpenUpgrade">'
                "https://github.com/OCA/OpenUpgrade</a></p>"
            )
        ],
    )
    confirm: bool = Field(
        default=False,
        description=(
            "Create the timeline as confirmed instead of draft. Only for "
            "high-confidence proposals: a confirmed timeline immediately "
            "impacts the migration analysis, and a source of truth URL is "
            "required in 'note'."
        ),
    )
    repository: str | None = Field(
        default=None,
        description=(
            "Restrict to one repository ('name' or 'org/name'). "
            "Required when several repositories host the module."
        ),
    )


class TimelineOutput(BaseModel):
    """Output of the timeline write tools."""

    error: str | None = None
    timeline: Timeline


class TimelineUpdateInput(BaseModel):
    """Inputs of the `migration_update_timeline` tool."""

    module: str = Field(description="Module technical name.")
    version: str = Field(description="Odoo version of the source module branch.")
    new_module: str | None = Field(
        default=None,
        description=(
            "New technical name of the module. Required to turn a 'removed' "
            "timeline into a 'renamed' or 'replaced' one, forbidden for "
            "'removed' timelines."
        ),
    )
    timeline_type: Literal["renamed", "replaced", "removed"] | None = Field(
        default=None,
        description=(
            "New type of the timeline: 'renamed', 'replaced', or 'removed' "
            "when the module disappeared without any successor."
        ),
    )
    note: str | None = Field(
        default=None,
        description=(
            "HTML note. Start the visible text with '[HIGHLY-CONFIDENT]' "
            "or '[LESS-CONFIDENT]', explain the change, then end with a "
            "bulleted Source section: "
            "'<br/>Source:<br/>- <a href=\"URL\">URL</a>' for each link. "
            "Put the full URL as link text, commit first; do not use "
            "Markdown. On a confirmed timeline, only the note can be "
            "updated."
        ),
        examples=[
            (
                "<p>[HIGHLY-CONFIDENT] Module renamed.<br/>Source:"
                '<br/>- <a href="https://github.com/odoo/odoo/commit/abc123">'
                "https://github.com/odoo/odoo/commit/abc123</a>"
                '<br/>- <a href="https://github.com/OCA/OpenUpgrade">'
                "https://github.com/OCA/OpenUpgrade</a></p>"
            )
        ],
    )
    confirm: bool = Field(
        default=False,
        description=(
            "Confirm the timeline instead of keeping it as a draft. Only "
            "for high-confidence proposals: a confirmed timeline "
            "immediately impacts the migration analysis, and a source of "
            "truth URL is required in 'note'."
        ),
    )
    repository: str | None = Field(
        default=None,
        description=(
            "Restrict to one repository ('name' or 'org/name'). "
            "Required when several repositories host the module."
        ),
    )


class TimelineDeleteInput(BaseModel):
    """Inputs of the `migration_delete_timeline` tool."""

    module: str = Field(description="Module technical name.")
    version: str = Field(description="Odoo version of the source module branch.")
    repository: str | None = Field(
        default=None,
        description=(
            "Restrict to one repository ('name' or 'org/name'). "
            "Required when several repositories host the module."
        ),
    )


class TimelineDeletedOutput(BaseModel):
    """Output of the `migration_delete_timeline` tool."""

    error: str | None = None
    deleted: bool


class OdooModuleBranchTimeline(models.Model):
    _inherit = "odoo.module.branch.timeline"

    # ------------------------------------------------------------------
    # Shared glue for the MCP tools
    # ------------------------------------------------------------------

    def _mcp_to_dict(self):
        """Convert timeline data to a dictionary."""
        self.ensure_one()
        return {
            "id": self.id,
            "module": self.module_branch_id.module_id.name,
            "version": self.module_branch_id.branch_id.name,
            "timeline_type": self.timeline_type,
            "state": self.state,
            "new_module": self.next_module_id.name,
            "starting_version": self.odoo_version_id.name,
            # The note is stored as HTML: keep the markup and links
            "note": str(self.note) if self.note else None,
        }

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

    @mcp_tool(TimelineListInput, TimelineListOutput)
    def _ai_migration_list_timelines(
        self, module=None, version=None, state=None, repository=None
    ):
        """List the module renames/replacements declared in the database."""
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

    @mcp_tool(TimelineCreateInput, TimelineOutput)
    def _ai_migration_create_timeline(
        self,
        module=None,
        version=None,
        new_module=None,
        timeline_type=None,
        note=None,
        confirm=None,
        repository=None,
    ):
        """Declare a module rename/replacement/removal, as a draft or confirmed
        timeline.

        Set 'confirm' to true for a high-confidence rename/replacement/removal
        with a source-of-truth URL in 'note': a confirmed module timeline
        immediately activates the module lineage used by the code
        absent-elements workflow.
        """
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
        timeline_type = timeline_type or "renamed"
        if timeline_type == "removed":
            if new_module is not None:
                raise ValueError(
                    "A removed timeline cannot target a new module: it has "
                    "no successor."
                )
            next_module_id = False
        else:
            if not new_module:
                raise ValueError(
                    f"A new module is required for a '{timeline_type}' timeline."
                )
            next_module_id = module_branch_model._mcp_get_module(new_module).id
        if confirm:
            check_source_of_truth(note)
        timeline = self.create(
            {
                "module_branch_id": module_branch.id,
                "next_module_id": next_module_id,
                "timeline_type": timeline_type,
                "note": note or False,
                # Proposal only by default: applied to the analysis once
                # confirmed (by a human, or directly for a high-confidence
                # proposal through the 'confirm' input)
                "state": "draft",
            }
        )
        if confirm:
            timeline.action_confirm()
        return {"timeline": timeline._mcp_to_dict()}

    def _mcp_update_confirmed_timeline_note(
        self, timeline, new_module, timeline_type, note, confirm
    ):
        """Annotate a confirmed module timeline (note only)."""
        if confirm:
            raise ValueError(
                "The timeline is already confirmed: 'confirm' is not expected."
            )
        if new_module is not None or timeline_type is not None:
            raise ValueError(
                "The timeline is confirmed: only its note can be updated "
                "(semantic fields are managed by humans in the UI)."
            )
        if note is None:
            raise ValueError(
                "The timeline is confirmed: provide 'note' to annotate it; "
                "semantic fields cannot be updated."
            )
        check_source_of_truth(note)
        timeline.write({"note": note})
        return {"timeline": timeline._mcp_to_dict()}

    @mcp_tool(TimelineUpdateInput, TimelineOutput)
    def _ai_migration_update_timeline(
        self,
        module=None,
        version=None,
        new_module=None,
        timeline_type=None,
        note=None,
        confirm=None,
        repository=None,
    ):
        """Update or confirm a draft module timeline proposal.

        The note is HTML; on a confirmed timeline only the note can be
        updated, and it must carry a source URL. Changing the type to
        'removed' clears the new module; switching back to 'renamed' or
        'replaced' requires a new module.
        """
        timeline = self._mcp_get_timeline(module, version, repository)
        if timeline.state != "draft":
            return self._mcp_update_confirmed_timeline_note(
                timeline, new_module, timeline_type, note, confirm
            )
        values = {}
        final_type = timeline_type or timeline.timeline_type
        if final_type == "removed":
            if new_module is not None:
                raise ValueError(
                    "A removed timeline cannot target a new module: it has "
                    "no successor."
                )
            if timeline.timeline_type != "removed":
                values["next_module_id"] = False
        elif new_module is not None:
            if new_module == module:
                raise ValueError("The new module must be different from the module.")
            values["next_module_id"] = (
                self.env["odoo.module.branch"]._mcp_get_module(new_module).id
            )
        elif not timeline.next_module_id:
            raise ValueError(
                f"A new module is required for a '{final_type}' timeline: "
                "provide 'new_module'."
            )
        if timeline_type is not None:
            values["timeline_type"] = timeline_type
        if note is not None:
            values["note"] = note
        if not values and not confirm:
            raise ValueError(
                "No field to update: provide 'new_module', 'timeline_type' or 'note'."
            )
        if confirm:
            check_source_of_truth(note if note is not None else timeline.note)
        if values:
            timeline.write(values)
        if confirm:
            timeline.action_confirm()
        return {"timeline": timeline._mcp_to_dict()}

    @mcp_tool(TimelineDeleteInput, TimelineDeletedOutput)
    def _ai_migration_delete_timeline(self, module=None, version=None, repository=None):
        """Delete a draft timeline proposal."""
        timeline = self._mcp_get_timeline(module, version, repository)
        if timeline.state != "draft":
            raise ValueError(
                f"The timeline of module '{module}' on version '{version}' "
                "is confirmed: only draft timelines can be deleted "
                "(managed by humans in the UI)."
            )
        timeline.unlink()
        return {"deleted": True}
