Expose the Odoo modules code elements collected by the Odoo MCA modules
through an MCP (Model Context Protocol) server.

This module adds the code element tools to the MCP server declared by
`odoo_repository_mcp`:

- search the models, fields, methods and data records collected from the
  scanned repositories
- get the full details of one element (model structure, field type and
  code, method signature and code, data JSON and XML source)
