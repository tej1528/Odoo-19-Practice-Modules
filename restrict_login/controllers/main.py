from odoo import http, _
from odoo.http import request
from odoo.addons.web.controllers.home import Home
from odoo.addons.web.controllers.home import (ensure_db, SIGN_UP_REQUEST_PARAMS, CREDENTIAL_PARAMS,)
import odoo
import uuid
import logging

_logger = logging.getLogger(__name__)

_logger.warning("===== RESTRICT LOGIN CONTROLLER LOADED =====")

class RestrictLoginHome(Home):

    @http.route('/web/login', type='http', auth='none', sitemap=False)
    def web_login(self, redirect=None, **kw):

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

            force_login_checked = (
                request.params.get('force_login')
            )    

            _logger.warning(
                "LOGIN BLOCK CHECK | token=%s | restrict=%s | force=%s",
                user.active_session_token if user else False,
                restrict_multiple_login,
                force_new_login,
            )
            
            _logger.warning(
                "USER=%s TOKEN=%s",
                user.login if user else False,
                user.active_session_token if user else False,
            )
            
            # Restrict Multiple Login
            if (
                user
                and restrict_multiple_login
                and user.active_session_token
                and not force_new_login
            ):
                
                _logger.warning(
                    "LOGIN BLOCKED FOR USER %s",
                    user.login,
                )
                values['error'] = _(
                    "You are already logged in on another device/browser."
                )

                return request.render(
                    'web.login',
                    values
                )

            try:

                auth_info = request.session.authenticate(
                    request.env,
                    credential
                )

                request.params['login_success'] = True

                _logger.warning("LOGIN SUCCESS")

                current_user = request.env[
                    'res.users'
                ].sudo().browse(auth_info['uid'])

                if (
                    not current_user.active_session_token
                    or (
                        force_new_login
                        and force_login_checked
                    )
                ):
                    token = str(uuid.uuid4())

                    current_user.write({
                        'active_session_token': token,
                    })

                    request.session[
                        'restrict_login_token'
                    ] = token

                _logger.warning(
                    "SESSION TOKEN = %s",
                    request.session.get(
                        'restrict_login_token'
                    )
                )

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
                'active_session_token': False,
            })

        request.session.logout(
            keep_db=True
        )

        return request.redirect(
            redirect,
            303
        )