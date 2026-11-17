# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Odoo MCA Code MCP",
    "summary": "Expose the modules code elements through an MCP server.",
    "version": "18.0.1.0.0",
    "development_status": "Alpha",
    "category": "Tools",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/module-composition-analysis",
    "data": [
        "data/ai_tools.xml",
    ],
    "installable": True,
    "depends": [
        # OCA/module-composition-analysis
        "odoo_repository_code",
        "odoo_repository_mcp",
    ],
    "external_dependencies": {
        "python": [
            "pydantic",
        ],
    },
    "license": "AGPL-3",
}
