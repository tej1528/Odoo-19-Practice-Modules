# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    restrict_multiple_login = fields.Boolean(string="Restrict Multiple Login")
    force_new_login = fields.Boolean(string="Force New Login")
    restrict_login_attempts = fields.Boolean(string="Restrict Login Attempts")
    login_attempts = fields.Integer(string="Maximum Login Attempts", default=3)
    block_time = fields.Integer(string="Block Time", default=1)
    block_time_unit = fields.Selection([
        ("minutes", "Minutes"),
        ("hours", "Hours"),
        ("days", "Days"),
    ], string="Time Unit", default="minutes")
    session_timeout = fields.Integer(string="Session Timeout (Minutes)", default=30)