Expose the Odoo modules code element migration data collected by the Odoo
MCA modules through an MCP (Model Context Protocol) server.

This module adds the code element migration tools to the MCP server
declared by `odoo_repository_mcp`:

- follow an element across the Odoo versions: its next version
  counterpart, its timeline-linked history and its full lineage up to a
  target version, jumping versions missing from the MCA
- list the declared code renames/removals with pagination and filters
- list the elements absent from the next version, with their timeline and
  timeline counters, plus data classification (demo, noupdate or
  overriding records); only data records loaded by the module are listed
- propose new renames/removals as timelines (draft by default, or directly
  confirmed for high-confidence proposals), applied to the analysis once
  confirmed
