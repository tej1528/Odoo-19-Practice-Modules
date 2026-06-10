from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _authenticate(cls, endpoint):

        result = super()._authenticate(endpoint)

        if not request.session.uid:
            return result

        restrict_login = (
            request.env['ir.config_parameter']
            .sudo()
            .get_param(
                'restrict_login.restrict_multiple_login',
                'False'
            )
        )

        force_new_login = (
            request.env['ir.config_parameter']
            .sudo()
            .get_param(
                'restrict_login.force_new_login',
                'False'
            )
        )

        if (
            restrict_login != 'True'
            or force_new_login != 'True'
        ):
            return result

        user = request.env['res.users'].sudo().browse(
            request.session.uid
        )

        session_token = request.session.get(
            'restrict_login_token'
        )

        if (
            user.active_session_token
            and session_token
            and user.active_session_token != session_token
        ):
            request.session.logout(
                keep_db=True
            )

        return result