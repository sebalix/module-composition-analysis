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

from .odoo_module_branch import ELEMENT_MODELS, ElementRef

# ---------------------------------------------------------------------------
# Pydantic models of the MCP tools
# ---------------------------------------------------------------------------


class Timeline(BaseModel):
    """Code timeline (element move/replacement/removal)."""

    id: int
    element_type: str = Field(description="'model', 'field', 'method' or 'data'.")
    module: str = Field(description="Technical module name.")
    version: str = Field(description="Odoo version of the source element.")
    model: NullableStr = Field(
        default=None,
        description="Model the element belongs to (None for model elements).",
    )
    name: str = Field(description="Element name (the full XML ID for data elements).")
    timeline_type: str = Field(
        description="'moved' (renamed or replaced) or 'removed'."
    )
    state: str = Field(description="Review state: 'draft' or 'confirmed'.")
    next: ElementRef | None = Field(
        default=None, description="Target element of a move/replacement, if any."
    )
    starting_version: NullableStr = Field(
        default=None, description="Odoo version the timeline starts from."
    )
    note: NullableStr = Field(
        default=None,
        description="HTML note explaining the move/replacement/removal.",
    )


class TimelineListInput(BaseModel):
    """Inputs of the `code_list_timelines` tool."""

    module: str | None = Field(default=None, description="Technical module name.")
    version: str | None = Field(
        default=None, description="Filter by the source element Odoo version."
    )
    element_type: Literal["model", "field", "method", "data"] | None = Field(
        default=None, description="Filter by element type."
    )
    state: Literal["draft", "confirmed"] | None = Field(
        default=None, description="Filter by review state."
    )
    timeline_type: Literal["moved", "removed"] | None = Field(
        default=None, description="Filter by timeline type."
    )
    repository: str | None = Field(
        default=None, description="Filter by repository ('name' or 'org/name')."
    )
    limit: int = Field(default=50, ge=1, description="Number of timelines to return.")
    offset: int = Field(
        default=0, ge=0, description="Index of the first timeline to return."
    )


class TimelineListOutput(BaseModel):
    """Output of the `code_list_timelines` tool."""

    error: str | None = None
    total: int
    timelines: list[Timeline]


class TimelineCreateInput(BaseModel):
    """Inputs of the `code_create_timeline` tool."""

    element_type: Literal["model", "field", "method", "data"] = Field(
        description="Type of the element."
    )
    version: str = Field(
        description="Odoo version of the source element (e.g. '17.0')."
    )
    module: str = Field(description="Technical module name.")
    model: str | None = Field(
        default=None,
        description=(
            "Model name the element belongs to (required for fields and methods)."
        ),
    )
    name: str = Field(
        description=(
            "Element name (the external ID for data elements, local or fully "
            "qualified)."
        )
    )
    timeline_type: Literal["moved", "removed"] | None = Field(
        default=None,
        description="'moved' (default, renamed or replaced) or 'removed'.",
    )
    next_name: str | None = Field(
        default=None,
        description=(
            "Name of the element in the next Odoo version (required for a "
            "rename, forbidden for a removal). For data elements, a full "
            "XML ID ('module.xml_id') is accepted and can infer the target "
            "module when unambiguous. It can be omitted for a pure move "
            "(same name) when 'next_module' or 'next_model' is set: the "
            "source name/XML ID is then reused."
        ),
    )
    next_module: str | None = Field(
        default=None,
        description=(
            "Technical name of the module hosting the target element when "
            "it moved to another module (default: the source module, "
            "following the module renames/replacements)."
        ),
    )
    next_model: str | None = Field(
        default=None,
        description=(
            "Technical name of the model hosting the target element when a "
            "field or method moved to another model (default: the source "
            "model, following the model renames). Only for fields and "
            "methods."
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
                "<p>[HIGHLY-CONFIDENT] Renamed.<br/>Source:"
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
    """Inputs of the `code_update_timeline` tool."""

    element_type: Literal["model", "field", "method", "data"] = Field(
        description="Type of the element."
    )
    version: str = Field(
        description="Odoo version of the source element (e.g. '17.0')."
    )
    module: str = Field(description="Technical module name.")
    model: str | None = Field(
        default=None,
        description=(
            "Model name the element belongs to (required for fields and methods)."
        ),
    )
    name: str = Field(
        description=(
            "Element name (the external ID for data elements, local or fully "
            "qualified)."
        )
    )
    timeline_type: Literal["moved", "removed"] | None = Field(
        default=None,
        description=(
            "New type of the timeline: 'moved' (renamed or replaced) or 'removed'."
        ),
    )
    next_name: str | None = Field(
        default=None,
        description=(
            "New name of the element in the next Odoo version. For data "
            "elements, a full XML ID ('module.xml_id') is accepted and can "
            "infer the target module when unambiguous. It can be omitted "
            "when only 'next_module' or 'next_model' changes: the current "
            "target name is then reused."
        ),
    )
    next_module: str | None = Field(
        default=None,
        description=(
            "Technical name of the module hosting the target element when "
            "it moved to another module (default: the current target module "
            "if any, else the source module)."
        ),
    )
    next_model: str | None = Field(
        default=None,
        description=(
            "Technical name of the model hosting the target element when a "
            "field or method moved to another model (default: the current "
            "target model if any, else the source model). Only for fields "
            "and methods."
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
                "<p>[HIGHLY-CONFIDENT] Renamed.<br/>Source:"
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
    """Inputs of the `code_delete_timeline` tool."""

    element_type: Literal["model", "field", "method", "data"] = Field(
        description="Type of the element."
    )
    version: str = Field(
        description="Odoo version of the source element (e.g. '17.0')."
    )
    module: str = Field(description="Technical module name.")
    model: str | None = Field(
        default=None,
        description=(
            "Model name the element belongs to (required for fields and methods)."
        ),
    )
    name: str = Field(
        description=(
            "Element name (the external ID for data elements, local or fully "
            "qualified)."
        )
    )
    repository: str | None = Field(
        default=None,
        description=(
            "Restrict to one repository ('name' or 'org/name'). "
            "Required when several repositories host the module."
        ),
    )


class TimelineDeletedOutput(BaseModel):
    """Output of the `code_delete_timeline` tool."""

    error: str | None = None
    deleted: bool


class OdooCodeTimeline(models.Model):
    _inherit = "odoo.code.timeline"

    # ------------------------------------------------------------------
    # Shared glue for the MCP tools
    # ------------------------------------------------------------------

    def _mcp_to_dict(self):
        """Convert the timeline to a dictionary."""
        self.ensure_one()
        element = self._get_element()
        next_element = self._get_next_element()
        data = element._mcp_to_element_dict()
        data.update(
            {
                "id": self.id,
                "timeline_type": self.timeline_type,
                "state": self.state,
                "next": (next_element._mcp_to_element_dict() if next_element else None),
                "starting_version": self.odoo_version_id.name,
                # The note is stored as HTML: keep the markup and links
                "note": str(self.note) if self.note else None,
            }
        )
        return data

    def _mcp_to_ref(self):
        """Convert the timeline to the shared MCP timeline reference."""
        self.ensure_one()
        next_element = self._get_next_element()
        return {
            "id": self.id,
            "type": self.timeline_type,
            "state": self.state,
            "target": (next_element._mcp_to_element_dict() if next_element else None),
        }

    def _mcp_get_timeline_for_element(self, element):
        """Return the timeline covering the given element, if any."""
        element.ensure_one()
        element_type = self._get_element_type(element._name)
        return self.search(
            [
                ("element_type", "=", element_type),
                (f"{element_type}_id", "=", element.id),
            ],
            limit=1,
        )

    def _mcp_get_previous_timeline(self, element):
        """Return the confirmed timeline pointing to the given element."""
        element_type = self._get_element_type(element._name)
        if element_type == "model":
            domain = [
                ("state", "=", "confirmed"),
                ("element_type", "=", "model"),
                ("next_model_id.odoo_model_id", "=", element.odoo_model_id.id),
            ]
        elif element_type == "data":
            domain = [
                ("state", "=", "confirmed"),
                ("element_type", "=", "data"),
                ("next_data_id.module_name", "=", element.module_name),
                ("next_data_id.xml_id", "=", element.xml_id),
            ]
        else:
            domain = [
                ("state", "=", "confirmed"),
                ("element_type", "=", element_type),
                (
                    f"next_{element_type}_id.odoo_model_id",
                    "=",
                    element.odoo_model_id.id,
                ),
                (f"next_{element_type}_id.name", "=", element.name),
            ]
        return self.search(domain, limit=1)

    def _mcp_get_timeline(
        self,
        element_type,
        version,
        module,
        model=None,
        name=None,
        repository=None,
    ):
        """Return the timeline of the given element."""
        element = self.env["odoo.module.branch"]._mcp_get_element(
            element_type,
            version,
            module,
            model=model,
            name=name,
            repository=repository,
        )
        timeline = self.search(
            [
                ("element_type", "=", element_type),
                (f"{element_type}_id", "=", element.id),
            ]
        )
        if not timeline:
            raise ValueError(
                f"No timeline for {element_type} '{name}' of module '{module}' "
                f"on Odoo version '{version}'."
            )
        return timeline

    def _mcp_get_element_name(self, element):
        """Return the identifying name/XML ID of a code element."""
        element_type = self._get_element_type(element._name)
        if element_type == "model":
            return element.odoo_model_name
        if element_type == "data":
            return element.xml_id
        return element.name

    def _mcp_get_target_module_branch(self, element, next_module=None):
        """Return the module branch hosting the target element.

        By default the module lineage of the source module is followed (module
        renames/replacements included). An explicit `next_module` targets
        another module of the same repository.
        """
        source_branch = element.module_branch_id
        target_module_name = next_module or source_branch.module_name
        # These computed fields may have been cached before the target
        # version was scanned
        source_branch.invalidate_recordset(["next_odoo_version_module_branch_id"])
        if target_module_name == source_branch.module_name:
            lineage_branch = source_branch.next_odoo_version_module_branch_id
            if not lineage_branch:
                raise ValueError(
                    f"No later version of module '{source_branch.module_name}' "
                    "is scanned (is the next version of the module scanned?)."
                )
            # A module can be hosted by several repositories: prefer the next
            # branch of the source repository (the lineage branch may belong
            # to another repository).
            if source_branch.repository_id:
                target_branch = self.env["odoo.module.branch"].search(
                    [
                        ("module_id", "=", lineage_branch.module_id.id),
                        ("repository_id", "=", source_branch.repository_id.id),
                        (
                            "branch_sequence",
                            ">=",
                            source_branch.branch_id.next_id.sequence,
                        ),
                    ],
                    order="branch_sequence",
                    limit=1,
                )
                if target_branch:
                    return target_branch
            return lineage_branch
        if not source_branch.branch_id.next_id:
            raise ValueError(
                f"No Odoo version known after '{source_branch.branch_id.name}'."
            )
        domain = [
            ("module_name", "=", target_module_name),
            ("branch_sequence", ">=", source_branch.branch_id.next_id.sequence),
        ]
        repository = source_branch.repository_id
        if repository:
            domain.append(("repository_id", "=", repository.id))
        else:
            # Orphaned modules carry no scanned data
            domain.append(("repository_id", "!=", False))
        target_branch = self.env["odoo.module.branch"].search(
            domain, order="branch_sequence", limit=1
        )
        if target_branch:
            return target_branch
        if repository:
            other_branch = self.env["odoo.module.branch"].search(
                [
                    ("module_name", "=", target_module_name),
                    ("repository_id", "!=", False),
                    (
                        "branch_sequence",
                        ">=",
                        source_branch.branch_id.next_id.sequence,
                    ),
                ],
                order="branch_sequence",
                limit=1,
            )
            if other_branch:
                raise ValueError(
                    f"The target module '{target_module_name}' is not hosted "
                    f"by repository '{repository.display_name}' (found in "
                    f"'{other_branch.repository_id.display_name}'): "
                    "cross-repository moves are not supported."
                )
        raise ValueError(
            f"No module '{target_module_name}' found for an Odoo version after "
            f"'{source_branch.branch_id.name}'."
        )

    def _mcp_get_target_model(
        self, element, target_branch, next_model=None, next_module=None
    ):
        """Return the model record hosting the target field/method."""
        if next_model:
            target_model = self.env["odoo.module.branch.model"].search(
                [
                    ("module_branch_id", "=", target_branch.id),
                    ("odoo_model_name", "=", next_model),
                ],
                limit=1,
            )
            if not target_model:
                raise ValueError(
                    f"No model '{next_model}' found in module "
                    f"'{target_branch.module_name}' on Odoo version "
                    f"'{target_branch.branch_id.name}'."
                )
            return target_model
        source_branch = element.module_branch_id
        if next_module and next_module != source_branch.module_name:
            # The target module is explicit: the source model name is reused
            # unless the caller provided 'next_model'.
            target_model = self.env["odoo.module.branch.model"].search(
                [
                    ("module_branch_id", "=", target_branch.id),
                    ("odoo_model_name", "=", element.odoo_model_name),
                ],
                limit=1,
            )
            if not target_model:
                raise ValueError(
                    f"No model '{element.odoo_model_name}' found in module "
                    f"'{target_branch.module_name}' on Odoo version "
                    f"'{target_branch.branch_id.name}'; provide 'next_model' "
                    "if the model was renamed."
                )
            return target_model
        source_model = element.module_branch_model_id
        source_model.invalidate_recordset(["next_odoo_version_model_id"])
        target_model = source_model.next_odoo_version_model_id
        if not target_model:
            raise ValueError(
                f"No later version of model '{element.odoo_model_name}' is "
                "scanned (is the next version of the module scanned?)."
            )
        return target_model

    def _mcp_find_data_by_full_xml_id(self, element, next_name):
        """Find a data record by full XML ID in later module branches.

        Fallback used when no explicit target module is given: a full XML ID
        is expected to be unique enough to identify the target across the
        modules of the same repository.
        """
        source_branch = element.module_branch_id
        if not source_branch.branch_id.next_id:
            return self.env["odoo.module.branch.data"].browse()
        domain = [
            ("full_xml_id", "=", next_name),
            (
                "odoo_version_id.sequence",
                ">=",
                source_branch.branch_id.next_id.sequence,
            ),
        ]
        if source_branch.repository_id:
            domain.append(("repository_id", "=", source_branch.repository_id.id))
        if element.data_type:
            domain.append(("data_type", "=", element.data_type))
        candidates = self.env["odoo.module.branch.data"].search(domain)
        if len(candidates) > 1:
            modules = ", ".join(
                sorted(
                    candidate.module_branch_id.display_name for candidate in candidates
                )
            )
            raise ValueError(
                f"Several data records match the full XML ID '{next_name}' in "
                f"a later version: {modules}. Specify 'next_module' to "
                "disambiguate."
            )
        return candidates

    def _mcp_get_updated_target(
        self, timeline, element_type, next_name, next_module, next_model
    ):
        """Return the target of an update, reusing the current target scope."""
        element = timeline._get_element()
        current_target = timeline._get_next_element()
        if next_name is not None:
            target_name = next_name
        elif current_target:
            target_name = self._mcp_get_element_name(current_target)
        else:
            target_name = self._mcp_get_element_name(element)
        target_module = next_module
        if target_module is None and current_target:
            target_module = current_target.module_branch_id.module_name
        target_model = next_model
        if (
            target_model is None
            and current_target
            and element_type in ("field", "method")
        ):
            target_model = current_target.module_branch_model_id.odoo_model_name
        return self._mcp_get_next_element(
            element,
            target_name,
            next_module=target_module,
            next_model=target_model,
        )

    def _mcp_get_next_element(
        self, element, next_name, next_module=None, next_model=None
    ):
        """Return the target element of a move, resolved in the target scope.

        The target scope defaults to the source module/model lineage. It can
        be changed explicitly with `next_module` and `next_model` (the latter
        for fields and methods only). The target is still stored as a record
        reference (`next_*_id`): its module and model are deduced from it.
        """
        element_type = self._get_element_type(element._name)
        if not next_name:
            # Pure move (or merge): reuse the source identity
            next_name = self._mcp_get_element_name(element)
        target_branch = self._mcp_get_target_module_branch(element, next_module)
        target_model = None
        if element_type == "model":
            next_element = self.env["odoo.module.branch.model"].search(
                [
                    ("module_branch_id", "=", target_branch.id),
                    ("odoo_model_name", "=", next_name),
                ],
                limit=1,
            )
        elif element_type == "data":
            # Search by full XML ID first (can be an override), then by the
            # local XML ID
            next_element = self.env["odoo.module.branch.data"].search(
                [
                    ("module_branch_id", "=", target_branch.id),
                    "|",
                    ("full_xml_id", "=", next_name),
                    ("xml_id", "=", next_name),
                ],
                limit=1,
            )
            if not next_element and not next_module and "." in next_name:
                # A full XML ID can identify a target living in another module
                next_element = self._mcp_find_data_by_full_xml_id(element, next_name)
        else:
            target_model = self._mcp_get_target_model(
                element,
                target_branch,
                next_model=next_model,
                next_module=next_module,
            )
            next_element = self.env[ELEMENT_MODELS[element_type]].search(
                [
                    ("module_branch_model_id", "=", target_model.id),
                    ("name", "=", next_name),
                ],
                limit=1,
            )
        if not next_element:
            context = (
                f" on model '{target_model.odoo_model_name}'" if target_model else ""
            )
            raise ValueError(
                f"The new {element_type} '{next_name}' was not found in module "
                f"'{target_branch.module_name}' on Odoo version "
                f"'{target_branch.branch_id.name}'{context} (is the next "
                "version of the module scanned?)."
            )
        return next_element

    # ------------------------------------------------------------------
    # MCP tools
    # ------------------------------------------------------------------

    @mcp_tool(TimelineListInput, TimelineListOutput)
    def _ai_code_list_timelines(
        self,
        module=None,
        version=None,
        element_type=None,
        state=None,
        timeline_type=None,
        repository=None,
        limit=None,
        offset=None,
    ):
        """List the code element moves/replacements/removals."""
        module_branch_model = self.env["odoo.module.branch"]
        domain = []
        if module:
            domain.append(
                ("module_id", "=", module_branch_model._mcp_get_module(module).id)
            )
        if version:
            domain.append(
                (
                    "module_branch_id.branch_id",
                    "=",
                    module_branch_model._mcp_get_branch(version).id,
                )
            )
        if element_type:
            domain.append(("element_type", "=", element_type))
        if state:
            domain.append(("state", "=", state))
        if timeline_type:
            domain.append(("timeline_type", "=", timeline_type))
        if repository:
            domain.append(
                (
                    "repository_id",
                    "=",
                    module_branch_model._mcp_get_repository(repository).id,
                )
            )
        total = self.search_count(domain)
        timelines = self.search(domain, limit=limit, offset=offset)
        return {
            "total": total,
            "timelines": [timeline._mcp_to_dict() for timeline in timelines],
        }

    @mcp_tool(TimelineCreateInput, TimelineOutput)
    def _ai_code_create_timeline(
        self,
        element_type=None,
        version=None,
        module=None,
        model=None,
        name=None,
        timeline_type=None,
        next_name=None,
        next_module=None,
        next_model=None,
        note=None,
        confirm=None,
        repository=None,
    ):
        """Declare a code element move, replacement or removal, as a draft.

        For elements that moved to another module or model, set
        'next_module' and/or 'next_model'; 'next_name' can be omitted when
        the element keeps its name/XML ID. Prefer a 'moved' timeline with
        the target over a 'removed' one when the target is known: it
        preserves the link for the migration analysis.
        """
        if element_type in ("field", "method") and not model:
            raise ValueError(
                f"The 'model' input is required for {element_type} elements."
            )
        if element_type not in ("field", "method") and next_model:
            raise ValueError(
                "'next_model' is only supported for field and method elements."
            )
        element = self.env["odoo.module.branch"]._mcp_get_element(
            element_type,
            version,
            module,
            model=model,
            name=name,
            repository=repository,
        )
        existing = self.search(
            [
                ("element_type", "=", element_type),
                (f"{element_type}_id", "=", element.id),
            ]
        )
        if existing:
            raise ValueError(
                f"A timeline already exists for {element_type} '{name}' of "
                f"module '{module}' on Odoo version '{version}'."
            )
        if confirm:
            check_source_of_truth(note)
        timeline_type = timeline_type or "moved"
        values = {
            "element_type": element_type,
            f"{element_type}_id": element.id,
            "timeline_type": timeline_type,
            "note": note or False,
            # Proposal only by default: applied to the analysis once
            # confirmed (by a human, or directly for a high-confidence
            # proposal through the 'confirm' input)
            "state": "draft",
        }
        if timeline_type == "removed":
            if next_name or next_module or next_model:
                raise ValueError(
                    "'next_name', 'next_module' and 'next_model' are not "
                    "expected when the element is removed."
                )
        else:
            if not next_name and not (next_module or next_model):
                raise ValueError(
                    "'next_name' is required when the element is renamed, "
                    "unless 'next_module' or 'next_model' is set for a pure "
                    "move (same name/XML ID)."
                )
            values[f"next_{element_type}_id"] = self._mcp_get_next_element(
                element,
                next_name,
                next_module=next_module,
                next_model=next_model,
            ).id
        timeline = self.create(values)
        if confirm:
            timeline.action_confirm()
        return {"timeline": timeline._mcp_to_dict()}

    def _mcp_update_confirmed_timeline(
        self, timeline, timeline_type, next_name, next_module, next_model, note, confirm
    ):
        """Annotate a confirmed timeline (note only)."""
        if confirm:
            raise ValueError(
                "The timeline is already confirmed: 'confirm' is not expected."
            )
        if any(
            value is not None
            for value in (timeline_type, next_name, next_module, next_model)
        ):
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
    def _ai_code_update_timeline(
        self,
        element_type=None,
        version=None,
        module=None,
        model=None,
        name=None,
        timeline_type=None,
        next_name=None,
        next_module=None,
        next_model=None,
        note=None,
        confirm=None,
        repository=None,
    ):
        """Update a draft code timeline proposal.

        The target module/model can be changed with 'next_module' and
        'next_model'; 'next_name' can be omitted to keep the current target
        name/XML ID. Prefer a 'moved' timeline with the target over a
        'removed' one when the target is known: it preserves the link for
        the migration analysis. The note is HTML; on a confirmed timeline
        only the note can be updated, and it must carry a source URL.
        """
        if element_type in ("field", "method") and not model:
            raise ValueError(
                f"The 'model' input is required for {element_type} elements."
            )
        if element_type not in ("field", "method") and next_model:
            raise ValueError(
                "'next_model' is only supported for field and method elements."
            )
        timeline = self._mcp_get_timeline(
            element_type,
            version,
            module,
            model=model,
            name=name,
            repository=repository,
        )
        if timeline.state != "draft":
            return self._mcp_update_confirmed_timeline(
                timeline,
                timeline_type,
                next_name,
                next_module,
                next_model,
                note,
                confirm,
            )
        timeline_type = timeline_type or timeline.timeline_type
        current_target = timeline._get_next_element()
        values = {}
        if timeline_type == "removed":
            if next_name or next_module or next_model:
                raise ValueError(
                    "'next_name', 'next_module' and 'next_model' are not "
                    "expected when the element is removed (set "
                    "timeline_type='moved' to declare a target)."
                )
            if current_target:
                values[f"next_{element_type}_id"] = False
        else:
            target_changed = (
                next_name is not None
                or next_module is not None
                or next_model is not None
            )
            if target_changed:
                values[f"next_{element_type}_id"] = self._mcp_get_updated_target(
                    timeline,
                    element_type,
                    next_name,
                    next_module,
                    next_model,
                ).id
            elif not current_target:
                raise ValueError(
                    "'next_name' is required when the element is renamed, "
                    "unless 'next_module' or 'next_model' is set for a pure "
                    "move (same name/XML ID)."
                )
        if timeline_type != timeline.timeline_type:
            values["timeline_type"] = timeline_type
        if note is not None:
            values["note"] = note
        if not values and not confirm:
            raise ValueError(
                "No field to update: provide 'timeline_type', 'next_name', "
                "'next_module', 'next_model' or 'note'."
            )
        if confirm:
            check_source_of_truth(note if note is not None else timeline.note)
        if values:
            timeline.write(values)
        if confirm:
            timeline.action_confirm()
        return {"timeline": timeline._mcp_to_dict()}

    @mcp_tool(TimelineDeleteInput, TimelineDeletedOutput)
    def _ai_code_delete_timeline(
        self,
        element_type=None,
        version=None,
        module=None,
        model=None,
        name=None,
        repository=None,
    ):
        """Delete a draft code timeline proposal."""
        timeline = self._mcp_get_timeline(
            element_type,
            version,
            module,
            model=model,
            name=name,
            repository=repository,
        )
        if timeline.state != "draft":
            raise ValueError(
                f"The timeline of {element_type} '{name}' of module '{module}' "
                f"on Odoo version '{version}' is confirmed: only draft "
                "timelines can be deleted (managed by humans in the UI)."
            )
        timeline.unlink()
        return {"deleted": True}
