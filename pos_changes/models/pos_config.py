from odoo import models, fields


class PosConfig(models.Model):
    _inherit = "pos.config"

    default_user_id = fields.Many2one(
        "res.users",
        string="Default Cashier"
    )