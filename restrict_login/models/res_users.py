from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    active_session_token = fields.Char(
        string="Active Session Token",
        copy=False,
    )