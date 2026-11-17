## Timeline proposals

The write tools (`migration_create_timeline`, `migration_update_timeline`,
`migration_delete_timeline`) create, update and delete **draft** timelines
only: a human reviews and confirms them in the UI before they impact the
migration analysis.

To allow a client to propose timelines, add its user to the
`Migration Timeline Editor` group
(`odoo_repository_migration_mcp.group_migration_timeline_editor`).
Read-only clients only need the `Odoo MCA User` group (see
`odoo_repository_mcp`).
