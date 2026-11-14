# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    # The 'renamed' timeline type has been renamed to 'moved': it covers
    # both the renames and the replacements (e.g. a Char field turned into a
    # Many2one while keeping the same semantics)
    cr.execute(
        """
        UPDATE odoo_code_timeline
        SET timeline_type = 'moved'
        WHERE timeline_type = 'renamed'
        """
    )
    _logger.info("'renamed' timeline type of 'odoo.code.timeline' renamed to 'moved'.")
