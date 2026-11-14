# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Odoo Repository Code Migration",
    "summary": "Store the evolution of modules code elements between Odoo versions.",
    "version": "18.0.1.0.0",
    "category": "Tools",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["sebalix"],
    "website": "https://github.com/OCA/module-composition-analysis",
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/odoo_code_timeline.xml",
        "views/odoo_module_branch_data.xml",
        "views/odoo_module_branch_model.xml",
        "views/odoo_module_branch_model_field.xml",
        "views/odoo_module_branch_model_method.xml",
    ],
    "installable": True,
    "depends": [
        "odoo_repository_code",
        "odoo_repository_migration",
    ],
    "license": "AGPL-3",
    "pre_init_hook": "pre_init_hook",
}
