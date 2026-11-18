# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from collections import Counter, defaultdict
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


class TimelineRef(BaseModel):
    """Timeline linked to a code element."""

    id: int = Field(description="Timeline record id.")
    type: Literal["moved", "removed"] = Field(
        description="'moved' (renamed or replaced) or 'removed'."
    )
    state: Literal["draft", "confirmed"] = Field(
        description="'draft' (proposal pending review) or 'confirmed'."
    )
    target: ElementRef | None = Field(
        default=None, description="Target element of a move, if any."
    )


class NextVersionOutput(BaseModel):
    """Output of the `code_get_next_version_element` tool."""

    error: str | None = None
    state: NullableStr = Field(
        default=None,
        description=(
            "Next version state: 'unknown' (the next version is not scanned "
            "yet), 'available' or 'absent'."
        ),
    )
    next: ElementRef | None = Field(
        default=None, description="Confirmed next version counterpart, if any."
    )
    timeline: TimelineRef | None = Field(
        default=None,
        description=(
            "Timeline covering the element, if any. A draft move/removal is "
            "reported here while 'next' remains null."
        ),
    )


class HistoryEntry(ElementRef):
    """Step of the version chain of a code element."""

    timeline: TimelineRef | None = Field(
        default=None,
        description="Timeline linking the element to its next version, if any.",
    )


class HistoryOutput(BaseModel):
    """Output of the `code_get_element_history` tool."""

    error: str | None = None
    history: list[HistoryEntry]


class ElementLineageStep(BaseModel):
    """Existing element at one Odoo version in a lineage."""

    version: str = Field(description="Odoo version.")
    element: ElementRef = Field(description="Element at this version.")
    timeline: TimelineRef | None = Field(
        default=None,
        description="Outgoing timeline from this element, if any.",
    )


class ElementLineage(BaseModel):
    """Full lineage of a code element across Odoo versions."""

    start: ElementRef = Field(description="Starting element.")
    target_version: str = Field(description="Target Odoo version.")
    steps: list[ElementLineageStep] = Field(
        description=(
            "Existing elements ordered by version. Version jumps indicate "
            "missing versions/scans or unresolved transitions."
        )
    )


class ElementLineageOutput(ElementLineage):
    """Output of the `code_get_element_lineage` tool."""

    error: str | None = None


class ElementLineageInput(ElementInput):
    """Inputs of the `code_get_element_lineage` tool."""

    to_version: str | None = Field(
        default=None,
        description=(
            "Target Odoo version. Defaults to the latest Odoo version known to the MCA."
        ),
    )


class ElementLineageBatchInput(BaseModel):
    """Inputs of the `code_get_elements_lineage` tool."""

    elements: list[ElementInput] = Field(
        min_length=1,
        max_length=100,
        description="Elements to trace (between 1 and 100).",
    )
    to_version: str | None = Field(
        default=None,
        description=(
            "Target Odoo version for all elements. Defaults to the latest "
            "Odoo version known to the MCA."
        ),
    )


class ElementLineageBatchResult(BaseModel):
    """One element result in a batch lineage call."""

    element: ElementInput = Field(description="Element requested by the caller.")
    lineage: ElementLineage | None = Field(
        default=None, description="Lineage, if the element was found."
    )
    error: str | None = Field(
        default=None, description="Error for this element, if any."
    )


class ElementLineageBatchOutput(BaseModel):
    """Output of the `code_get_elements_lineage` tool."""

    error: str | None = None
    results: list[ElementLineageBatchResult]


class AbsentElementCounts(BaseModel):
    """Timeline counters of the absent elements."""

    uncovered: int = 0
    draft: int = 0
    removed: int = 0
    moved: int = 0


class AbsentElement(ElementRef):
    """Code element absent from the next Odoo version."""

    org: NullableStr = Field(
        default=None, description="Organization owning the repository."
    )
    repository: NullableStr = Field(default=None, description="Repository name.")
    timeline: TimelineRef | None = Field(
        default=None,
        description=(
            "Timeline covering the element, if any. No timeline means the "
            "element is uncovered and still needs analysis."
        ),
    )
    data_type: Literal["data", "demo"] | None = Field(
        default=None, description="'data' or 'demo' (for data elements)."
    )
    noupdate: bool | None = Field(
        default=None, description="Whether the data is in noupdate mode."
    )
    is_override: bool | None = Field(
        default=None,
        description=(
            "Whether the data record overrides a record of another module "
            "(for data elements)."
        ),
    )
    overridden_xml_id: NullableStr = Field(
        default=None,
        description=(
            "XML ID of the overridden record when 'is_override' is true "
            "(for data elements)."
        ),
    )
    next_defined_in: list[str] = Field(
        default_factory=list,
        description=(
            "Modules defining the same model in the next version, in the same "
            "repository (for model elements)."
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
    data_type: Literal["data", "demo"] | None = Field(
        default=None,
        description=(
            "Filter data elements by type. Setting any data filter restricts "
            "the search to data elements."
        ),
    )
    noupdate: bool | None = Field(
        default=None, description="Filter data elements by noupdate mode."
    )
    is_override: bool | None = Field(
        default=None,
        description="Filter data elements by whether they override another record.",
    )
    timeline_state: Literal["none", "draft", "confirmed"] | None = Field(
        default=None,
        description=(
            "Filter by timeline state: 'none' (no timeline), 'draft' or 'confirmed'."
        ),
    )
    timeline_type: Literal["moved", "removed"] | None = Field(
        default=None, description="Filter by timeline type."
    )
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
    counts: AbsentElementCounts = Field(
        description=(
            "Timeline counters over the elements matching every filter except "
            "the timeline filters, before pagination."
        )
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
        timeline = self.env["odoo.code.timeline"]._mcp_get_timeline_for_element(element)
        return {
            "state": element.next_version_state,
            "next": next_element._mcp_to_element_dict() if next_element else None,
            "timeline": timeline._mcp_to_ref() if timeline else None,
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
            entry["timeline"] = outgoing._mcp_to_ref() if outgoing else None
            history.append(entry)
        return {"history": history}

    def _mcp_get_target_branch(self, to_version=None):
        """Return the target Odoo branch of a lineage request."""
        branch_model = self.env["odoo.branch"].with_context(active_test=False)
        if to_version:
            branch = branch_model.search([("name", "=", to_version)], limit=1)
            if not branch:
                raise ValueError(f"Unknown Odoo version: '{to_version}'.")
            return branch
        branch = branch_model.search([], order="sequence desc", limit=1)
        if not branch:
            raise ValueError("No Odoo version known to the MCA.")
        return branch

    def _mcp_get_element_lineage(self, element, target_branch):
        """Walk the element lineage up to the target Odoo version."""
        timeline_model = self.env["odoo.code.timeline"]
        steps = []
        current = element
        while True:
            timeline = timeline_model._mcp_get_timeline_for_element(current)
            steps.append(
                {
                    "version": current.odoo_version_id.name,
                    "element": current._mcp_to_element_dict(),
                    "timeline": timeline._mcp_to_ref() if timeline else None,
                }
            )
            if current.odoo_version_id.sequence >= target_branch.sequence:
                break
            next_element = current._mcp_get_next_version_element()
            if (
                not next_element
                or next_element.odoo_version_id.sequence > target_branch.sequence
                or next_element.odoo_version_id.sequence
                <= current.odoo_version_id.sequence
            ):
                break
            current = next_element
        return {
            "start": element._mcp_to_element_dict(),
            "target_version": target_branch.name,
            "steps": steps,
        }

    @mcp_tool(ElementLineageInput, ElementLineageOutput)
    def _ai_code_get_element_lineage(
        self,
        element_type=None,
        version=None,
        module=None,
        model=None,
        name=None,
        repository=None,
        to_version=None,
    ):
        """Get the full version lineage of a code element."""
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
        target_branch = self._mcp_get_target_branch(to_version)
        if target_branch.sequence < element.odoo_version_id.sequence:
            raise ValueError(
                f"The target version '{target_branch.name}' is before the "
                f"starting version '{element.odoo_version_id.name}'."
            )
        return self._mcp_get_element_lineage(element, target_branch)

    @mcp_tool(ElementLineageBatchInput, ElementLineageBatchOutput)
    def _ai_code_get_elements_lineage(self, elements=None, to_version=None):
        """Get the full version lineage of several code elements."""
        target_branch = self._mcp_get_target_branch(to_version)
        results = []
        for element_input in elements:
            element_type = element_input["element_type"]
            try:
                if element_type in ("field", "method") and not element_input.get(
                    "model"
                ):
                    raise ValueError(
                        f"The 'model' input is required for {element_type} elements."
                    )
                element = self._mcp_get_element(
                    element_type,
                    element_input["version"],
                    element_input["module"],
                    model=element_input.get("model"),
                    name=element_input["name"],
                    repository=element_input.get("repository"),
                )
                if target_branch.sequence < element.odoo_version_id.sequence:
                    raise ValueError(
                        f"The target version '{target_branch.name}' is before "
                        f"the starting version "
                        f"'{element.odoo_version_id.name}'."
                    )
                lineage = self._mcp_get_element_lineage(element, target_branch)
                results.append(
                    {
                        "element": element_input,
                        "lineage": lineage,
                        "error": None,
                    }
                )
            except ValueError as error:
                results.append(
                    {
                        "element": element_input,
                        "lineage": None,
                        "error": str(error),
                    }
                )
        return {"results": results}

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

    def _mcp_get_next_defined_in(self, elements, next_version):
        """Map (model id, repository id) to the modules defining the model in
        the next version."""
        model_elements = [
            element
            for element in elements
            if element._name == "odoo.module.branch.model"
        ]
        if not model_elements:
            return {}
        models = self.env["odoo.module.branch.model"].search(
            [
                ("odoo_version_id", "=", next_version.id),
                (
                    "odoo_model_id",
                    "in",
                    [element.odoo_model_id.id for element in model_elements],
                ),
            ]
        )
        mapping = defaultdict(set)
        for model in models:
            mapping[(model.odoo_model_id.id, model.repository_id.id)].add(
                model.module_name
            )
        return {key: sorted(module_names) for key, module_names in mapping.items()}

    def _mcp_absent_element_dict(self, element, timelines, next_defined_in=None):
        """Convert an absent element to a dictionary."""
        element_type = self.env["odoo.code.timeline"]._get_element_type(element._name)
        data = element._mcp_to_element_dict()
        data["org"] = element.org_id.name
        data["repository"] = element.repository_id.name
        timeline = timelines.get(element_type, {}).get(element.id)
        data["timeline"] = timeline._mcp_to_ref() if timeline else None
        if element_type == "data":
            data.update(
                {
                    "data_type": element.data_type,
                    "noupdate": element.noupdate,
                    "is_override": element.is_override,
                    "overridden_xml_id": (
                        element.xml_id if element.is_override else None
                    ),
                }
            )
        elif element_type == "model":
            data["next_defined_in"] = (next_defined_in or {}).get(
                (element.odoo_model_id.id, element.repository_id.id), []
            )
        return data

    def _mcp_get_absent_data_filters(
        self, element_type, data_type, noupdate, is_override
    ):
        """Return the element type and the active data filters."""
        data_filters = {
            "data_type": data_type,
            "noupdate": noupdate,
            "is_override": is_override,
        }
        active_filters = {
            key: value for key, value in data_filters.items() if value is not None
        }
        if active_filters:
            if element_type not in (None, "data"):
                raise ValueError(
                    "The data filters ('data_type', 'noupdate', 'is_override') "
                    "are only supported for data elements."
                )
            element_type = "data"
        return element_type, active_filters

    def _mcp_get_absent_elements(
        self,
        module,
        version,
        element_type,
        model,
        repository,
        active_data_filters,
    ):
        """Return the absent elements and the next Odoo version."""
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
            if model_name == "odoo.module.branch.data":
                # Only records actually loaded by the module are relevant.
                element_domain.append(("loaded", "=", True))
                for field_name, value in active_data_filters.items():
                    element_domain.append((field_name, "=", value))
            elements.extend(self.env[model_name].search(element_domain))
        elements.sort(
            key=lambda element: (
                self.env["odoo.code.timeline"]._get_element_type(element._name),
                element.odoo_model_name or "",
                getattr(element, "name", "") or "",
            )
        )
        return elements, next_version

    def _mcp_count_absent_timelines(self, rows):
        """Count the timeline distribution of absent element rows."""
        counts = Counter()
        for row in rows:
            timeline = row["timeline"]
            if not timeline:
                counts["uncovered"] += 1
            elif timeline["state"] == "draft":
                counts["draft"] += 1
            elif timeline["type"] == "removed":
                counts["removed"] += 1
            else:
                counts["moved"] += 1
        return counts

    def _mcp_filter_absent_rows(self, rows, timeline_state, timeline_type):
        """Filter absent element rows on their timeline."""
        if timeline_state:
            if timeline_state == "none":
                rows = [row for row in rows if not row["timeline"]]
            else:
                rows = [
                    row
                    for row in rows
                    if row["timeline"] and row["timeline"]["state"] == timeline_state
                ]
        if timeline_type:
            rows = [
                row
                for row in rows
                if row["timeline"] and row["timeline"]["type"] == timeline_type
            ]
        return rows

    @mcp_tool(AbsentElementsInput, AbsentElementsOutput)
    def _ai_code_list_absent_elements(
        self,
        module=None,
        version=None,
        element_type=None,
        model=None,
        data_type=None,
        noupdate=None,
        is_override=None,
        timeline_state=None,
        timeline_type=None,
        repository=None,
        limit=None,
        offset=None,
    ):
        """List the code elements of a module absent from its next Odoo
        version."""
        element_type, active_data_filters = self._mcp_get_absent_data_filters(
            element_type, data_type, noupdate, is_override
        )
        elements, next_version = self._mcp_get_absent_elements(
            module,
            version,
            element_type,
            model,
            repository,
            active_data_filters,
        )
        timelines = self._mcp_get_element_timelines(elements)
        next_defined_in = self._mcp_get_next_defined_in(elements, next_version)
        rows = [
            self._mcp_absent_element_dict(
                element, timelines, next_defined_in=next_defined_in
            )
            for element in elements
        ]
        counts = self._mcp_count_absent_timelines(rows)
        rows = self._mcp_filter_absent_rows(rows, timeline_state, timeline_type)
        total = len(rows)
        rows = rows[offset : offset + limit]
        return {
            "total": total,
            "next_version": next_version.name,
            "counts": {
                "uncovered": counts.get("uncovered", 0),
                "draft": counts.get("draft", 0),
                "removed": counts.get("removed", 0),
                "moved": counts.get("moved", 0),
            },
            "elements": rows,
        }
