# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

ELEMENT_TABLES = (
    "odoo_module_branch_model",
    "odoo_module_branch_model_field",
    "odoo_module_branch_model_method",
    "odoo_module_branch_data",
)


def migrate(cr, version):
    if not version:
        return
    # The 'removed' value has been renamed to 'absent': the element is not
    # present in the next scanned version of the module (which is not
    # necessarily a definitive removal, e.g. a community module that has
    # not been migrated yet).
    for table in ELEMENT_TABLES:
        count = openupgrade.logged_query(
            cr,
            f"UPDATE {table} SET next_version_state = 'absent'"
            " WHERE next_version_state = 'removed'",
        )
        _logger.info(
            "%s: %s 'next_version_state' values renamed from 'removed' to 'absent'",
            table,
            count,
        )
