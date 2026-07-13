# -*- coding: utf-8 -*-
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

        if not request.session.uid or not request.env.user or not request.env.user.id:
            return result

        user = request.env.user.sudo()

        if user._is_public() or not user.exists():
            return result

        company = user.company_id
        if not company or not company.restrict_multiple_login:
            return result

        db_token = user.active_session_token
        session_token = request.session.get("restrict_login_token")

        if db_token and session_token and db_token != session_token:
            _logger.info("Multiple login detected for user %s", user.login)
            request.session.pop("restrict_login_token", None)
            request.session.logout(keep_db=True)
            return result

        now = fields.Datetime.now()
        if not user.last_activity or user.last_activity < now - timedelta(minutes=1):
            user.write({
                "last_activity": now,
            })

        return result