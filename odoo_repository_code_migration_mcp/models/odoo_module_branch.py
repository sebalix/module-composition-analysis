# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from typing import Literal

from pydantic import BaseModel, Field

from odoo import models

from odoo.addons.odoo_repository_mcp.utils import NullableStr, mcp_tool

ELEMENT_MODELS = {
    "model": "odoo.module.branch.model",
    "field": "odoo.module.branch.model.field",
    "method": "odoo.module.branch.model.method",
    "data": "odoo.module.branch.data",
}


# ---------------------------------------------------------------------------
# Pydantic models of the MCP tools
# ---------------------------------------------------------------------------


class ElementRef(BaseModel):
    """Reference to a code element."""

    element_type: str = Field(description="'model', 'field', 'method' or 'data'.")
    module: str = Field(description="Technical module name.")
    version: str = Field(description="Odoo version.")
    model: NullableStr = Field(
        default=None,
        description="Model the element belongs to (None for model elements).",
    )
    name: str = Field(description="Element name (the full XML ID for data elements).")


class ElementInput(BaseModel):
    """Inputs identifying a code element."""

    element_type: Literal["model", "field", "method", "data"] = Field(
        description="Type of the element."
    )
    version: str = Field(description="Odoo version of the element (e.g. '17.0').")
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


class NextVersionOutput(BaseModel):
    """Output of the `code_get_next_version_element` tool."""

    error: str | None = None
    found: bool = Field(
        description="Whether the element exists in the next Odoo version."
    )
    state: NullableStr = Field(
        default=None,
        description=(
            "Next version state: 'unknown' (the next version is not scanned "
            "yet), 'available' or 'absent'."
        ),
    )
    next: ElementRef | None = Field(
        default=None, description="Next version counterpart, if any."
    )


class HistoryEntry(ElementRef):
    """Step of the version chain of a code element."""

    timeline_type: NullableStr = Field(
        default=None,
        description=(
            "Type of the timeline linking to the next step ('moved' or 'removed')."
        ),
    )
    state: NullableStr = Field(
        default=None,
        description=(
            "State of the timeline linking to the next step ('draft' or 'confirmed')."
        ),
    )


class HistoryOutput(BaseModel):
    """Output of the `code_get_element_history` tool."""

    error: str | None = None
    history: list[HistoryEntry]


class AbsentElement(ElementRef):
    """Code element absent from the next Odoo version."""

    org: NullableStr = Field(
        default=None, description="Organization owning the repository."
    )
    repository: NullableStr = Field(default=None, description="Repository name.")
    timeline_type: NullableStr = Field(
        default=None,
        description=(
            "Type of the timeline already covering the element ('moved' or "
            "'removed'), if any."
        ),
    )
    timeline_state: NullableStr = Field(
        default=None,
        description=(
            "State of the timeline already covering the element ('draft' or "
            "'confirmed'), if any."
        ),
    )


class AbsentElementsInput(BaseModel):
    """Inputs of the `code_list_absent_elements` tool."""

    module: str = Field(description="Technical module name.")
    version: str = Field(
        description=(
            "Source Odoo version (the elements are checked against its next version)."
        )
    )
    element_type: Literal["model", "field", "method", "data"] | None = Field(
        default=None, description="Filter by element type."
    )
    model: str | None = Field(default=None, description="Filter by model name.")
    repository: str | None = Field(
        default=None,
        description=(
            "Restrict to one repository ('name' or 'org/name'). "
            "Required when several repositories host the module."
        ),
    )
    limit: int = Field(default=50, ge=1, description="Number of elements to return.")
    offset: int = Field(
        default=0, ge=0, description="Index of the first element to return."
    )


class AbsentElementsOutput(BaseModel):
    """Output of the `code_list_absent_elements` tool."""

    error: str | None = None
    total: int
    next_version: NullableStr = Field(
        default=None, description="Odoo version the elements are absent from."
    )
    elements: list[AbsentElement]


class OdooModuleBranch(models.Model):
    _inherit = "odoo.module.branch"

    # ------------------------------------------------------------------
    # Shared glue for the MCP tools
    # ------------------------------------------------------------------

    def _mcp_get_element(
        self,
        element_type,
        version,
        module,
        model=None,
        name=None,
        repository=None,
    ):
        """Return the single code element matching the inputs."""
        domain = []
        if module:
            domain.append(("module_name", "=", module))
        if version:
            domain.append(("odoo_version_id", "=", self._mcp_get_branch(version).id))
        if repository:
            domain.append(
                ("repository_id", "=", self._mcp_get_repository(repository).id)
            )
        if model:
            domain.append(("odoo_model_name", "=", model))
        if element_type == "model":
            domain.append(("odoo_model_name", "=", name))
        elif element_type == "data":
            domain.extend(["|", ("full_xml_id", "=", name), ("xml_id", "=", name)])
        else:
            domain.append(("name", "=", name))
        elements = self.env[ELEMENT_MODELS[element_type]].search(domain)
        if not elements:
            context = f" (model '{model}')" if model else ""
            raise ValueError(
                f"No {element_type} '{name}' found for module '{module}' "
                f"on Odoo version '{version}'{context}."
            )
        if len(elements) > 1:
            repositories = ", ".join(elements.mapped("repository_id.display_name"))
            raise ValueError(
                f"The {element_type} '{name}' is defined in several repositories "
                f"for module '{module}' on Odoo version '{version}': "
                f"{repositories}. Please specify the 'repository' input."
            )
        return elements

    # ------------------------------------------------------------------
    # MCP tools
    # ------------------------------------------------------------------

    @mcp_tool(ElementInput, NextVersionOutput)
    def _ai_code_get_next_version_element(
        self,
        element_type=None,
        version=None,
        module=None,
        model=None,
        name=None,
        repository=None,
    ):
        """Get the next Odoo version counterpart of a code element."""
        if element_type in ("field", "method") and not model:
            raise ValueError(
                f"The 'model' input is required for {element_type} elements."
            )
        element = self._mcp_get_element(
            element_type,
            version,
            module,
            model=model,
            name=name,
            repository=repository,
        )
        next_element = element._mcp_get_next_version_element()
        return {
            "found": bool(next_element),
            "state": element.next_version_state,
            "next": next_element._mcp_to_element_dict() if next_element else None,
        }

    @mcp_tool(ElementInput, HistoryOutput)
    def _ai_code_get_element_history(
        self,
        element_type=None,
        version=None,
        module=None,
        model=None,
        name=None,
        repository=None,
    ):
        """Get the version chain of a code element."""
        if element_type in ("field", "method") and not model:
            raise ValueError(
                f"The 'model' input is required for {element_type} elements."
            )
        element = self._mcp_get_element(
            element_type,
            version,
            module,
            model=model,
            name=name,
            repository=repository,
        )
        timeline_model = self.env["odoo.code.timeline"]
        element_model = self.env[ELEMENT_MODELS[element_type]]
        # Seed the chain from the timeline starting at the element, or from
        # the one pointing to it
        timeline = timeline_model.search(
            [
                ("state", "=", "confirmed"),
                ("element_type", "=", element_type),
                (f"{element_type}_id", "=", element.id),
            ],
            limit=1,
        )
        if not timeline:
            timeline = timeline_model._mcp_get_previous_timeline(element)
        elements = element_model.browse()
        if timeline:
            elements = timeline._get_all_impacted_elements()[element_type]
        elements |= element
        elements = elements.sorted(lambda element: element.odoo_version_id.sequence)
        history = []
        for current in elements:
            outgoing = timeline_model.search(
                [
                    ("state", "=", "confirmed"),
                    ("element_type", "=", element_type),
                    (f"{element_type}_id", "=", current.id),
                ],
                limit=1,
            )
            entry = current._mcp_to_element_dict()
            entry["timeline_type"] = outgoing.timeline_type
            entry["state"] = outgoing.state
            history.append(entry)
        return {"history": history}

    def _mcp_get_element_timelines(self, elements):
        """Return the timelines covering the given elements, by type and id."""
        timeline_model = self.env["odoo.code.timeline"]
        timelines = {}
        for element_type, model_name in ELEMENT_MODELS.items():
            ids = [element.id for element in elements if element._name == model_name]
            if not ids:
                continue
            records = timeline_model.search(
                [
                    ("element_type", "=", element_type),
                    (f"{element_type}_id", "in", ids),
                ]
            )
            timelines[element_type] = {
                record[f"{element_type}_id"].id: record for record in records
            }
        return timelines

    def _mcp_absent_element_dict(self, element, timelines):
        """Convert an absent element to a dictionary."""
        element_type = self.env["odoo.code.timeline"]._get_element_type(element._name)
        data = element._mcp_to_element_dict()
        data["org"] = element.org_id.name
        data["repository"] = element.repository_id.name
        timeline = timelines.get(element_type, {}).get(element.id)
        data["timeline_type"] = timeline.timeline_type if timeline else None
        data["timeline_state"] = timeline.state if timeline else None
        return data

    @mcp_tool(AbsentElementsInput, AbsentElementsOutput)
    def _ai_code_list_absent_elements(
        self,
        module=None,
        version=None,
        element_type=None,
        model=None,
        repository=None,
        limit=None,
        offset=None,
    ):
        """List the code elements of a module absent from its next Odoo
        version."""
        module_ = self._mcp_get_module(module)
        branch = self._mcp_get_branch(version)
        domain = [
            ("module_id", "=", module_.id),
            ("branch_id", "=", branch.id),
        ]
        if repository:
            domain.append(
                ("repository_id", "=", self._mcp_get_repository(repository).id)
            )
        else:
            domain.append(("repository_id", "!=", False))
        module_branches = self.search(domain)
        if not module_branches:
            raise ValueError(
                f"Module '{module}' not found for Odoo version '{version}'."
            )
        next_version = module_branches[0].branch_id.next_id
        if not next_version:
            raise ValueError(f"No Odoo version known after '{version}'.")
        element_models = dict(ELEMENT_MODELS)
        if element_type:
            element_models = {element_type: element_models[element_type]}
        elements = []
        for model_name in element_models.values():
            element_domain = [
                ("module_branch_id", "in", module_branches.ids),
                ("next_version_state", "=", "absent"),
            ]
            if model:
                element_domain.append(("odoo_model_name", "=", model))
            elements.extend(self.env[model_name].search(element_domain))
        elements.sort(
            key=lambda element: (
                self.env["odoo.code.timeline"]._get_element_type(element._name),
                element.odoo_model_name or "",
                getattr(element, "name", "") or "",
            )
        )
        total = len(elements)
        elements = elements[offset : offset + limit]
        timelines = self._mcp_get_element_timelines(elements)
        return {
            "total": total,
            "next_version": next_version.name,
            "elements": [
                self._mcp_absent_element_dict(element, timelines)
                for element in elements
            ],
        }
