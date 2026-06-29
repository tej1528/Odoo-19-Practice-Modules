from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    hide_tax = fields.Boolean(
        string="Hide Taxes",
        default=False,
        help="Hide taxes from invoices, bills, reports and portal.",
    )