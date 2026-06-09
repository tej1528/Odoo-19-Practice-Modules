from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    active_session_sid = fields.Char(
        string="Active Session SID",
        copy=False,
    )

    session_updated_on = fields.Datetime(
        string="Session Updated On",
        copy=False,
    )