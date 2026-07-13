# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    restrict_multiple_login = fields.Boolean(related="company_id.restrict_multiple_login", readonly=False)
    force_new_login = fields.Boolean(related="company_id.force_new_login", readonly=False)
    restrict_login_attempts = fields.Boolean(related="company_id.restrict_login_attempts", readonly=False)
    login_attempts = fields.Integer(related="company_id.login_attempts", readonly=False)
    block_time = fields.Integer(related="company_id.block_time", readonly=False)
    block_time_unit = fields.Selection(related="company_id.block_time_unit", readonly=False)
    session_timeout = fields.Integer(related="company_id.session_timeout", readonly=False)