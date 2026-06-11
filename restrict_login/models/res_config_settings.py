from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    restrict_multiple_login = fields.Boolean(
        related="company_id.restrict_multiple_login",
        readonly=False,
    )

    force_new_login = fields.Boolean(
        related="company_id.force_new_login",
        readonly=False,
    )