# Copyright 2026 Sébastien Alix
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Odoo Repository MCP",
    "summary": "Expose Odoo MCA data as MCP tools.",
    "version": "18.0.1.0.0",
    "category": "Tools",
    "author": "sebalix, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/module-composition-analysis",
    "data": [
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "depends": [
        "odoo_repository",
        "auth_api_key",
    ],
    "license": "AGPL-3",
}
