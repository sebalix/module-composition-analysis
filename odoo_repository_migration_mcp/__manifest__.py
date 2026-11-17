# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Odoo MCA Migration MCP",
    "summary": "Expose the modules migration data through an MCP server.",
    "version": "18.0.1.0.0",
    "development_status": "Alpha",
    "category": "Tools",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/module-composition-analysis",
    "data": [
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "data/ai_tools.xml",
    ],
    "installable": True,
    "depends": [
        # OCA/module-composition-analysis
        "odoo_repository_migration",
        "odoo_repository_mcp",
    ],
    "external_dependencies": {
        "python": [
            "pydantic",
        ],
    },
    "license": "AGPL-3",
}
