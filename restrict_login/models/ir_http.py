from datetime import timedelta
from odoo import fields, models
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _authenticate(cls, endpoint):
        result = super()._authenticate(endpoint)

        if not request.session.uid:
            return result

        user = request.env.user.sudo()
        company = request.env.company

        if not company.restrict_multiple_login:
            return result

        db_token = user.active_session_token
        session_token = request.session.get("restrict_login_token")

        if not db_token:
            return result

        if db_token != session_token:
            _logger.warning("TOKEN MISMATCH | Force logging out invalid browser session for user %s", user.login)
            
            request.session.pop("restrict_login_token", None)
            request.session.logout(keep_db=True)
            return result

        limit_time = fields.Datetime.now() - timedelta(minutes=1)
        if not user.last_activity or user.last_activity < limit_time:
            user.write({"last_activity": fields.Datetime.now()})

        return result