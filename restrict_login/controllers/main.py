from odoo import http, fields, _
from odoo.http import request
from odoo.addons.web.controllers.home import Home
import odoo
import logging
from datetime import timedelta
from odoo.fields import Datetime

_logger = logging.getLogger(__name__)
class RestrictLoginHome(Home):

    @http.route('/web/login', type='http', auth='none', sitemap=False)
    def web_login(self, redirect=None, **kw):

        from odoo.addons.web.controllers.home import (
            ensure_db,
            SIGN_UP_REQUEST_PARAMS,
            CREDENTIAL_PARAMS,
        )

        ensure_db()

        request.params['login_success'] = False

        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return request.redirect(redirect)

        if request.env.uid is None:
            if request.session.uid is None:
                request.env["ir.http"]._auth_method_public()
            else:
                request.update_env(user=request.session.uid)

        values = {
            k: v
            for k, v in request.params.items()
            if k in SIGN_UP_REQUEST_PARAMS
        }

        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':

            credential = {
                key: value
                for key, value in request.params.items()
                if key in CREDENTIAL_PARAMS and value
            }

            credential.setdefault('type', 'password')

            
            login = credential.get('login')

            user = request.env['res.users'].sudo().search(
                [('login', '=', login)],
                limit=1
            )

            if user and user.session_updated_on:

                diff = Datetime.now() - user.session_updated_on

                if diff > timedelta(hours=8):

                    user.write({
                        'active_session_sid': False,
                        'session_updated_on': False,
                    })

                    user.invalidate_recordset()

                    user = request.env['res.users'].sudo().browse(user.id)

                    _logger.warning(
                        "OLD SESSION CLEARED FOR USER %s",
                        user.login
                    )
                
                _logger.warning(
                    "OLD SESSION CLEARED FOR USER %s",
                    user.login
                )

            icp = request.env['ir.config_parameter'].sudo()

            restrict_multiple_login = (
                icp.get_param(
                    'restrict_login.restrict_multiple_login',
                    'False'
                ) == 'True'
            )

            force_new_login = (
                icp.get_param(
                    'restrict_login.force_new_login',
                    'False'
                ) == 'True'
            )

            _logger.warning(
                "LOGIN CHECK | user=%s | stored_sid=%s | restrict=%s | force=%s",
                user.login if user else '',
                user.active_session_sid if user else '',
                restrict_multiple_login,
                force_new_login,
            )
            
            # ==========================
            # BLOCK SECOND LOGIN
            # ==========================
            if (
                user
                and restrict_multiple_login
                and user.active_session_sid
                and not force_new_login
            ):
                values['error'] = _(
                    "You are already logged in on another device/browser."
                )

                response = request.render(
                    'web.login',
                    values
                )
                response.headers['Cache-Control'] = 'no-cache'
                return response

            try:

                auth_info = request.session.authenticate(
                    request.env,
                    credential
                )

                request.params['login_success'] = True

                current_user = request.env[
                    'res.users'
                ].sudo().browse(auth_info['uid'])

                current_user.write({
                    'active_session_sid': request.session.sid,
                    'session_updated_on': fields.Datetime.now(),
                })

                return request.redirect(
                    self._login_redirect(
                        auth_info['uid'],
                        redirect=redirect
                    )
                )

            except odoo.exceptions.AccessDenied as e:

                if e.args == odoo.exceptions.AccessDenied().args:
                    values['error'] = _("Wrong login/password")
                else:
                    values['error'] = e.args[0]

        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')

        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True

        response = request.render('web.login', values)
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"

        return response
    
    @http.route('/web/session/logout', type='http', auth='none')
    def session_logout(self, redirect='/web/login'):

        if request.session.uid:

            request.env['res.users'].sudo().browse(
                request.session.uid
            ).write({
                'active_session_sid': False,
                'session_updated_on': False,
            })

        request.session.logout(
            keep_db=True
        )

        return request.redirect(
            redirect,
            303
        )