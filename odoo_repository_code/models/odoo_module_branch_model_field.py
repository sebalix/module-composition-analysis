# Copyright 2025 Sebastien Alix <https://github.com/sebalix>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class OdooModuleBranchModelField(models.Model):
    _name = "odoo.module.branch.model.field"
    _description = "Odoo field"

    module_branch_model_id = fields.Many2one(
        comodel_name="odoo.module.branch.model",
        ondelete="cascade",
        string="Model",
        required=True,
        index=True,
    )
    module_branch_id = fields.Many2one(
        related="module_branch_model_id.module_branch_id",
        store=True,
        index=True,
    )
    module_name = fields.Char(
        related="module_branch_model_id.module_name",
        string="Technical module name",
        required=True,
        store=True,
        precompute=True,
        index=True,
    )
    odoo_model_id = fields.Many2one(
        related="module_branch_model_id.odoo_model_id",
        string="Model ",
        required=True,
        store=True,
        precompute=True,
        index=True,
    )
    odoo_version_id = fields.Many2one(
        related="module_branch_model_id.odoo_version_id",
        string="Odoo Version",
        required=True,
        store=True,
        precompute=True,
        index=True,
    )
    org_id = fields.Many2one(related="module_branch_id.org_id", store=True, index=True)
    repository_id = fields.Many2one(
        related="module_branch_id.repository_id", store=True, index=True
    )
    global_dependency_level = fields.Integer(
        related="module_branch_id.global_dependency_level", store=True
    )
    name = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    field_type = fields.Char(string="Type", required=True, index=True)
    data = fields.Serialized()
    lineno = fields.Integer(compute="_compute_field_params", store=True)
    end_lineno = fields.Integer(compute="_compute_field_params", store=True)
    param_string = fields.Char(compute="_compute_field_params", store=True)
    param_required = fields.Boolean(compute="_compute_field_params", store=True)
    param_readonly = fields.Boolean(compute="_compute_field_params", store=True)
    param_default = fields.Char(compute="_compute_field_params", store=True)
    param_help = fields.Char(compute="_compute_field_params", store=True)
    param_compute = fields.Char(compute="_compute_field_params", store=True)
    param_inverse = fields.Char(compute="_compute_field_params", store=True)
    param_search = fields.Char(compute="_compute_field_params", store=True)
    param_related = fields.Char(compute="_compute_field_params", store=True)
    param_store = fields.Boolean(compute="_compute_field_params", store=True)
    param_index = fields.Boolean(compute="_compute_field_params", store=True)
    param_copy = fields.Boolean(compute="_compute_field_params", store=True)
    param_ondelete = fields.Boolean(compute="_compute_field_params", store=True)
    param_auto_join = fields.Boolean(compute="_compute_field_params", store=True)
    param_comodel_name = fields.Char(compute="_compute_field_params", store=True)
    is_computed = fields.Boolean(compute="_compute_is_computed", store=True)
    is_readonly = fields.Boolean(compute="_compute_is_readonly", store=True)
    is_stored = fields.Boolean(compute="_compute_is_stored", store=True)

    @api.depends("data")
    def _compute_field_params(self):
        for rec in self:
            rec.lineno = rec.data.get("lineno", 0)
            rec.end_lineno = rec.data.get("end_lineno", 0)
            rec.param_string = rec.data.get("string")
            kwargs = rec.data.get("kwargs", {})
            rec.param_required = kwargs.get("required", False)
            rec.param_readonly = kwargs.get("readonly", False)
            rec.param_default = kwargs.get("default")
            rec.param_help = kwargs.get("help")
            rec.param_compute = kwargs.get("compute")
            rec.param_inverse = kwargs.get("inverse")
            rec.param_search = kwargs.get("search")
            rec.param_related = kwargs.get("related")
            rec.param_store = kwargs.get("store", False)
            rec.param_index = kwargs.get("index", False)
            rec.param_copy = kwargs.get("copy", False)
            rec.param_ondelete = kwargs.get("ondelete", False)
            rec.param_auto_join = kwargs.get("auto_join", False)
            rec.param_comodel_name = rec.data.get("comodel_name")

    @api.depends("data")
    def _compute_is_readonly(self):
        for rec in self:
            # Default: not readonly
            rec.is_readonly = False
            kwargs = rec.data.get("kwargs", {})
            # Simple case: 'readonly' attribute manually set
            if "readonly" in kwargs:
                rec.is_readonly = kwargs["readonly"]
            # Computed field without inverse
            elif kwargs.get("compute") and not kwargs.get("inverse"):
                rec.is_readonly = True
            # Related field
            elif kwargs.get("related"):
                rec.is_readonly = True

    @api.depends("data")
    def _compute_is_stored(self):
        for rec in self:
            # Default: stored
            rec.is_stored = True
            kwargs = rec.data.get("kwargs", {})
            # Simple case: 'store' attribute manually set
            if "store" in kwargs:
                rec.is_stored = kwargs["store"]
            # Computed or related field
            elif kwargs.get("compute") or kwargs.get("related"):
                rec.is_stored = False

    @api.depends("param_compute", "param_related")
    def _compute_is_computed(self):
        for rec in self:
            rec.is_computed = rec.param_compute or rec.param_related

    def _to_dict(self):
        self.ensure_one()
        return {
            "name": self.name,
            "field_type": self.field_type,
        }
