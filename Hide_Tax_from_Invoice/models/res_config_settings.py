from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    hide_tax = fields.Boolean(
        related="company_id.hide_tax",
        readonly=False,
        string="Hide Taxes",
    )