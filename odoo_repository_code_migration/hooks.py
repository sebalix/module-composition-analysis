# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tools.sql import SQL, column_exists, create_column, table_exists

ELEMENT_TABLES = (
    "odoo_module_branch_model",
    "odoo_module_branch_model_field",
    "odoo_module_branch_model_method",
    "odoo_module_branch_data",
)


def create_next_version_state_columns(cr):
    """Create the 'next_version_state' columns on the code element tables.

    Called by the pre-init hook (module installation). Pre-creating the
    columns prevents the ORM from scheduling the computation of the field on
    the whole recordset at install — the ORM only schedules it for the
    columns it creates itself — which is very long on large databases. The
    existing rows are initialized with the 'unknown' value, and the daily
    scheduled action reclassifies them.
    """
    for table in ELEMENT_TABLES:
        if not table_exists(cr, table):
            # Fresh database: the table will be created with the column
            continue
        if not column_exists(cr, table, "next_version_state"):
            create_column(cr, table, "next_version_state", "VARCHAR")
        cr.execute(
            SQL(
                "UPDATE %s SET next_version_state = 'unknown'"
                " WHERE next_version_state IS NULL",
                SQL.identifier(table),
            )
        )


def pre_init_hook(env):
    """Pre-init hook: create the 'next_version_state' columns before the
    module setup, to avoid a full computation on the existing records."""
    create_next_version_state_columns(env.cr)
