from odoo import models, fields
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

        if restrict_login != 'True':
            return result

        user = (request.env['res.users'].sudo().browse(request.session.uid))

        user.write({'session_updated_on': fields.Datetime.now(),})
        
        if (
            user.active_session_sid
            and user.active_session_sid != request.session.sid
        ):

            request.session.logout(
                keep_db=True
            )

            return result