## Timeline proposals

The write tools (`code_create_timeline`, `code_update_timeline`,
`code_delete_timeline`) create, update and delete timelines, but only
**draft** ones can be updated or deleted: a manual review and confirms
them in the UI before they impact the migration analysis.

`code_create_timeline` and `code_update_timeline` also accept a `confirm`
input to create or confirm a timeline directly: reserve it to
high-confidence proposals, as a confirmed timeline immediately impacts the
migration analysis.

To allow a client to propose timelines, add its user to the
`Code Timeline Editor` group
(`odoo_repository_code_migration_mcp.group_code_timeline_editor`).
Read-only clients only need the `Odoo MCA User` group (see
`odoo_repository_mcp`).
