Expose the Odoo modules migration data collected by the Odoo MCA modules
through an MCP (Model Context Protocol) server.

This module adds the migration tools to the MCP server declared by
`odoo_repository_mcp`:

- get the migration status and the scan data of a module
- list the declared module renames/replacements
- propose new renames/replacements as timelines (draft by default, or
  directly confirmed for high-confidence proposals), applied to the
  migration analysis once confirmed
