## Timeline proposals

The write tools (`migration_create_timeline`, `migration_update_timeline`,
`migration_delete_timeline`) create, update and delete timelines, but only
**draft** ones can be updated or deleted: a human reviews and confirms
them in the UI before they impact the migration analysis.

`migration_create_timeline` and `migration_update_timeline` also accept a
`confirm` input to create or confirm a timeline directly: reserve it to
high-confidence proposals, as a confirmed timeline immediately impacts the
migration analysis.

A module that disappeared without any successor is declared with
`timeline_type="removed"` and no `new_module`: its migration status becomes
`removed` instead of `migrate`.

To allow a client to propose timelines, add its user to the
`Migration Timeline Editor` group
(`odoo_repository_migration_mcp.group_migration_timeline_editor`).
Read-only clients only need the `Odoo MCA User` group (see
`odoo_repository_mcp`).
