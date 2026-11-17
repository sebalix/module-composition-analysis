Expose the Odoo modules code element migration data collected by the Odoo
MCA modules through an MCP (Model Context Protocol) server.

This module adds the code element migration tools to the MCP server
declared by `odoo_repository_mcp`:

- follow an element across the Odoo versions: its next version
  counterpart and its full history
- list the declared code renames/removals
- propose new renames/removals as timelines (draft by default, or directly
  confirmed for high-confidence proposals), applied to the analysis once
  confirmed
