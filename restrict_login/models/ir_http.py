from odoo import models
from odoo.http import request

import logging

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _authenticate(cls, endpoint):

        result = super()._authenticate(endpoint)

        if not request.session.uid:
            return result

        company = request.env.company

        restrict_multiple_login = (
            company.restrict_multiple_login
        )

        force_new_login = (
            company.force_new_login
        )

        if not ( restrict_multiple_login and force_new_login ):
            return result

        user = ( request.env['res.users'] .sudo() .browse(request.session.uid))

        session_token = request.session.get( 'restrict_login_token' )

        _logger.info(
            "AUTH CHECK | user=%s | db_token=%s | session_token=%s",
            user.login,
            user.active_session_token,
            session_token,
        )

        if not session_token:
            return result

        if (user.active_session_token and user.active_session_token != session_token ):
            _logger.warning("FORCE LOGOUT | user=%s",user.login,)
            request.session.logout( keep_db=True )
        return result