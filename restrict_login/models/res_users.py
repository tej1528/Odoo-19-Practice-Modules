from datetime import timedelta
from odoo import api, fields, models

class ResUsers(models.Model):
    _inherit = "res.users"

    active_session_token = fields.Char(string="Active Session Token", copy=False, index=True)
    last_activity = fields.Datetime(string="Last Activity", copy=False)
    failed_login_attempts = fields.Integer(string="Failed Login Attempts", default=0)
    login_blocked_until = fields.Datetime(string="Login Blocked Until", copy=False)

    @api.model
    def _clear_expired_sessions(self):
        """ ક્રોન જોબ દ્વારા ૩૦ મિનિટથી ઇન-એક્ટિવ યુઝર્સના ટોકન ક્લીયર કરવા માટે """
        limit_time = fields.Datetime.now() - timedelta(minutes=30)
        users = self.search([
            ("active_session_token", "!=", False),
            "|",
            ("last_activity", "=", False),
            ("last_activity", "<", limit_time),
        ])
        if users:
            users.write({"active_session_token": False, "last_activity": False})