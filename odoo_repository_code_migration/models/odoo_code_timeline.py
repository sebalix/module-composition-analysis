# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class OdooCodeTimeline(models.Model):
    _name = "odoo.code.timeline"
    _description = "Odoo Code Timeline (renaming/removal)"
    _order = "odoo_version_sequence"

    _ELEMENT_COMODELS = {
        "model": "odoo.module.branch.model",
        "field": "odoo.module.branch.model.field",
        "method": "odoo.module.branch.model.method",
        "data": "odoo.module.branch.data",
    }

    element_type = fields.Selection(
        selection=[
            ("model", "Model"),
            ("field", "Field"),
            ("method", "Method"),
            ("data", "Data"),
        ],
        required=True,
        index=True,
    )
    state = fields.Selection(
        selection=[
            ("renamed", "has been renamed to"),
            ("removed", "has been removed"),
        ],
        default="renamed",
        required=True,
        index=True,
        help=(
            "Renamed: the element exists in the next version of the module "
            "under another name\n"
            "Removed: the element no longer exists in the next version of "
            "the module"
        ),
    )
    model_id = fields.Many2one(
        comodel_name="odoo.module.branch.model",
        ondelete="cascade",
        string="Model",
        index=True,
    )
    next_model_id = fields.Many2one(
        comodel_name="odoo.module.branch.model",
        ondelete="cascade",
        string="New model",
        index=True,
    )
    field_id = fields.Many2one(
        comodel_name="odoo.module.branch.model.field",
        ondelete="cascade",
        string="Field",
        index=True,
    )
    next_field_id = fields.Many2one(
        comodel_name="odoo.module.branch.model.field",
        ondelete="cascade",
        string="New field",
        index=True,
    )
    method_id = fields.Many2one(
        comodel_name="odoo.module.branch.model.method",
        ondelete="cascade",
        string="Method",
        index=True,
    )
    next_method_id = fields.Many2one(
        comodel_name="odoo.module.branch.model.method",
        ondelete="cascade",
        string="New method",
        index=True,
    )
    data_id = fields.Many2one(
        comodel_name="odoo.module.branch.data",
        ondelete="cascade",
        string="Data",
        index=True,
    )
    next_data_id = fields.Many2one(
        comodel_name="odoo.module.branch.data",
        ondelete="cascade",
        string="New data",
        index=True,
    )
    module_branch_id = fields.Many2one(
        string="Module",
        comodel_name="odoo.module.branch",
        compute="_compute_module_branch_id",
        store=True,
        index=True,
    )
    odoo_version_id = fields.Many2one(
        string="Starting from version",
        related="module_branch_id.branch_id.next_id",
        store=True,
        index=True,
    )
    odoo_version_sequence = fields.Integer(
        related="odoo_version_id.sequence",
        store=True,
    )
    org_id = fields.Many2one(
        string="Organization",
        related="module_branch_id.org_id",
        store=True,
        index=True,
    )
    repository_id = fields.Many2one(
        string="Repository",
        related="module_branch_id.repository_id",
        store=True,
        index=True,
    )
    note = fields.Html(
        help="Explain the details of this migration; especially useful when "
        "an element has been split into several elements.",
    )
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._refresh_element_next_version_state()
        return records

    def write(self, vals):
        res = super().write(vals)
        if set(vals) & {
            "state",
            "model_id",
            "next_model_id",
            "field_id",
            "next_field_id",
            "method_id",
            "next_method_id",
            "data_id",
            "next_data_id",
        }:
            self._refresh_element_next_version_state()
        return res

    def unlink(self):
        element_ids = {
            element_type: (
                self.mapped(f"{element_type}_id").ids
                + self.mapped(f"next_{element_type}_id").ids
            )
            for element_type in self._ELEMENT_COMODELS
        }
        res = super().unlink()
        self._refresh_elements_next_version_state(element_ids)
        return res

    def _refresh_element_next_version_state(self):
        """Recompute the 'next_version_state' of the elements concerned by
        these timelines (a rename/removal declaration changes their state)."""
        self._refresh_elements_next_version_state(
            {
                element_type: (
                    self.mapped(f"{element_type}_id").ids
                    + self.mapped(f"next_{element_type}_id").ids
                )
                for element_type in self._ELEMENT_COMODELS
            }
        )

    _ELEMENT_COMODELS = {
        "model": "odoo.module.branch.model",
        "field": "odoo.module.branch.model.field",
        "method": "odoo.module.branch.model.method",
        "data": "odoo.module.branch.data",
    }

    @api.model
    def _get_element_type(self, element_model_name):
        """Return the element type matching the given element model name."""
        for element_type, comodel in self._ELEMENT_COMODELS.items():
            if comodel == element_model_name:
                return element_type
        return False

    @api.model
    def _refresh_elements_next_version_state(self, element_ids_by_type):
        for element_type, comodel in self._ELEMENT_COMODELS.items():
            ids = element_ids_by_type.get(element_type) or []
            if not ids:
                continue
            elements = self.env[comodel].browse(ids)
            elements.env.add_to_compute(
                elements._fields["next_version_state"], elements
            )
            # Mark the dependent elements for recomputation (e.g. the fields
            # and methods of a model): the recomputation of a stored computed
            # field does not propagate to its dependents by itself
            elements.modified(["next_version_state"])
            # Invalidate the (non-stored) next version lookups
            elements.invalidate_recordset([f"next_odoo_version_{element_type}_id"])
        self.env.flush_all()

    def _get_element(self):
        """Return the element concerned by the timeline."""
        self.ensure_one()
        return self.model_id or self.field_id or self.method_id or self.data_id

    def _get_next_element(self):
        """Return the element replacing the current one, if any."""
        self.ensure_one()
        return (
            self.next_model_id
            or self.next_field_id
            or self.next_method_id
            or self.next_data_id
        )

    @api.depends("model_id", "field_id", "method_id", "data_id")
    def _compute_module_branch_id(self):
        for rec in self:
            rec.module_branch_id = rec._get_element().module_branch_id

    @api.depends(
        "odoo_version_id",
        "state",
        "model_id.display_name",
        "next_model_id.display_name",
        "field_id.display_name",
        "next_field_id.display_name",
        "method_id.display_name",
        "next_method_id.display_name",
        "data_id.display_name",
        "next_data_id.display_name",
    )
    def _compute_display_name(self):
        for rec in self:
            element = rec._get_element()
            next_element = rec._get_next_element()
            next_name = next_element.display_name if next_element else _("removed")
            rec.display_name = (
                f"[{rec.odoo_version_id.name}] {element.display_name} > {next_name}"
            )

    @api.constrains(
        "element_type",
        "state",
        "model_id",
        "next_model_id",
        "field_id",
        "next_field_id",
        "method_id",
        "next_method_id",
        "data_id",
        "next_data_id",
    )
    def _check_element(self):
        for rec in self:
            element = rec._get_element()
            next_element = rec._get_next_element()
            if not element:
                raise ValidationError(
                    _("The element concerned by the timeline is missing.")
                )
            if rec.state == "renamed" and not next_element:
                raise ValidationError(
                    _("A new element is required when the element is renamed.")
                )
            if rec.state == "removed" and next_element:
                raise ValidationError(
                    _("No new element is expected when the element is removed.")
                )
            # Only the m2o fields matching the element type must be set
            for other_type in self._ELEMENT_COMODELS:
                if other_type == rec.element_type:
                    continue
                if rec[f"{other_type}_id"] or rec[f"next_{other_type}_id"]:
                    raise ValidationError(
                        _(
                            "Element %(element)s doesn't match the timeline type "
                            "'%(type)s'.",
                            element=rec[f"{other_type}_id"].display_name,
                            type=rec.element_type,
                        )
                    )

    def _get_previous_timelines_domain(self):
        """Domain to find the timelines renamed to the current element."""
        self.ensure_one()
        element_type = self.element_type
        element = self._get_element()
        if element_type == "model":
            return [
                ("element_type", "=", element_type),
                ("next_model_id.odoo_model_id", "=", element.odoo_model_id.id),
            ]
        if element_type == "data":
            return [
                ("element_type", "=", element_type),
                ("next_data_id.module_name", "=", element.module_name),
                ("next_data_id.xml_id", "=", element.xml_id),
            ]
        # field / method
        return [
            ("element_type", "=", element_type),
            (f"next_{element_type}_id.odoo_model_id", "=", element.odoo_model_id.id),
            (f"next_{element_type}_id.name", "=", element.name),
        ]

    def _get_next_timelines_domain(self):
        """Domain to find the timelines starting from the current next element."""
        self.ensure_one()
        element_type = self.element_type
        next_element = self._get_next_element()
        if not next_element:
            return [("id", "=", False)]
        if element_type == "model":
            return [
                ("element_type", "=", element_type),
                ("model_id.odoo_model_id", "=", next_element.odoo_model_id.id),
            ]
        if element_type == "data":
            return [
                ("element_type", "=", element_type),
                ("data_id.module_name", "=", next_element.module_name),
                ("data_id.xml_id", "=", next_element.xml_id),
            ]
        # field / method
        return [
            ("element_type", "=", element_type),
            (f"{element_type}_id.odoo_model_id", "=", next_element.odoo_model_id.id),
            (f"{element_type}_id.name", "=", next_element.name),
        ]

    def _get_all_impacted_elements(self, visited=None):
        """Recursively collect all elements involved in the chain of timelines.

        Return a dict mapping each element type to the impacted records.
        """
        if visited is None:
            visited = self.env["odoo.code.timeline"].browse()
        impacted_elements = {
            element_type: self.env[comodel].browse()
            for element_type, comodel in self._ELEMENT_COMODELS.items()
        }
        for rec in self:
            if rec in visited:
                continue
            visited |= rec
            impacted_elements[rec.element_type] |= rec._get_element()
            impacted_elements[rec.element_type] |= rec._get_next_element()
            # Find previous timelines (current element is the next one)
            previous_timelines = self.search(rec._get_previous_timelines_domain())
            for timeline in previous_timelines:
                timeline_elements = timeline._get_all_impacted_elements(visited)
                for element_type, elements in timeline_elements.items():
                    impacted_elements[element_type] |= elements
            # Find next timelines (next element is the current one)
            next_timelines = self.search(rec._get_next_timelines_domain())
            for timeline in next_timelines:
                timeline_elements = timeline._get_all_impacted_elements(visited)
                for element_type, elements in timeline_elements.items():
                    impacted_elements[element_type] |= elements
        return impacted_elements

    def _get_related_code_timelines(self):
        """Return code timelines related to current ones regarding the same elements.

        A model A could be renamed to a model B in version X, then renamed
        again to C in version X+1, etc.
        When calling this method on any timeline, the others are returned.
        """
        impacted_elements = self._get_all_impacted_elements()
        domains = []
        for element_type, elements in impacted_elements.items():
            if not elements:
                continue
            domains.append(
                [
                    ("element_type", "=", element_type),
                    "|",
                    (f"{element_type}_id", "in", elements.ids),
                    (f"next_{element_type}_id", "in", elements.ids),
                ]
            )
        if not domains:
            return self.browse()
        domain = domains[0]
        for extra_domain in domains[1:]:
            domain = ["|", domain, extra_domain]
        return self.search(domain)
