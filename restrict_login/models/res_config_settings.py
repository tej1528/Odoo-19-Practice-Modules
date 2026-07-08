import uuid
from odoo import fields, models
from odoo.http import request

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    restrict_multiple_login = fields.Boolean(related="company_id.restrict_multiple_login", readonly=False)
    force_new_login = fields.Boolean(related="company_id.force_new_login", readonly=False)
    restrict_login_attempts = fields.Boolean(related="company_id.restrict_login_attempts", readonly=False)
    login_attempts = fields.Integer(related="company_id.login_attempts", readonly=False)
    block_time = fields.Integer(related="company_id.block_time", readonly=False)
    block_time_unit = fields.Selection(related="company_id.block_time_unit", readonly=False)

    def execute(self):
        res = super().execute()
        
        if self.restrict_multiple_login and request and request.session.uid:
            user = self.env.user.sudo()
            new_token = str(uuid.uuid4())
            user.write({
                "active_session_token": new_token,
                "last_activity": fields.Datetime.now(),
            })
            request.session["restrict_login_token"] = new_token
            
        return res