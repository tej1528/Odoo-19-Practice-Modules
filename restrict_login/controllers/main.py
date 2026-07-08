from datetime import timedelta
import uuid
import logging

import odoo
from odoo import _, fields, http
from odoo.addons.web.controllers.home import (
    Home,
    ensure_db,
    SIGN_UP_REQUEST_PARAMS,
    CREDENTIAL_PARAMS,
)
from odoo.http import request

_logger = logging.getLogger(__name__)

class RestrictLoginHome(Home):

    def _get_login_settings(self):
        company = request.env.company
        return {
            "restrict_multiple_login": company.restrict_multiple_login,
            "force_new_login": company.force_new_login,
            "restrict_login_attempts": company.restrict_login_attempts,
            "login_attempts": company.login_attempts,
            "block_time": company.block_time,
            "block_time_unit": company.block_time_unit,
        }

    @http.route("/web/login", type="http", auth="none", sitemap=False)
    def web_login(self, redirect=None, **kw):
        ensure_db()
        request.params["login_success"] = False
        
        if request.httprequest.method == "GET" and redirect and request.session.uid:
            return request.redirect(redirect)

        if request.env.uid is None:
            if request.session.uid is None:
                request.env["ir.http"]._auth_method_public()
            else:
                request.update_env(user=request.session.uid)

        values = {k: v for k, v in request.params.items() if k in SIGN_UP_REQUEST_PARAMS}

        try:
            values["databases"] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values["databases"] = None

        settings = self._get_login_settings()
        values["show_force_login_checkbox"] = settings["restrict_multiple_login"] and settings["force_new_login"]

        if request.httprequest.method == "POST":
            credential = {k: v for k, v in request.params.items() if k in CREDENTIAL_PARAMS and v}
            credential.setdefault("type", "password")
            
            login = credential.get("login")
            user = request.env["res.users"].sudo().search([("login", "=", login)], limit=1)
            force_login_checked = bool(request.params.get("force_login"))

            if user and settings["restrict_login_attempts"] and user.login_blocked_until:
                now = fields.Datetime.now()
                if user.login_blocked_until > now:
                    remaining_seconds = int((user.login_blocked_until - now).total_seconds())
                    values.update({
                        "login_blocked": True,
                        "remaining_seconds": remaining_seconds,
                        "error": False, 
                    })
                    return request.render("web.login", values)
                
                user.write({"failed_login_attempts": 0, "login_blocked_until": False})
                if "login_blocked" in values:
                    del values["login_blocked"]

            limit_time = fields.Datetime.now() - timedelta(minutes=30)
            if (
                user 
                and settings["restrict_multiple_login"] 
                and user.active_session_token 
                and not force_login_checked
                and not settings["force_new_login"]
                and user.last_activity 
                and user.last_activity > limit_time
            ):
                values["error"] = _("You are already logged in on another browser.")
                return request.render("web.login", values)

            try:
                auth_info = request.session.authenticate(request.env, credential)
                request.params["login_success"] = True
                current_user = request.env["res.users"].sudo().browse(auth_info["uid"])

                if settings["restrict_login_attempts"]:
                    current_user.write({"failed_login_attempts": 0, "login_blocked_until": False})

                if settings["restrict_multiple_login"]:
                    if force_login_checked or not current_user.active_session_token:
                        token = str(uuid.uuid4())
                        current_user.write({"active_session_token": token, "last_activity": fields.Datetime.now()})
                        request.session["restrict_login_token"] = token
                    else:
                        if not request.session.get("restrict_login_token"):
                            request.session["restrict_login_token"] = current_user.active_session_token
                        current_user.write({"last_activity": fields.Datetime.now()})

                return request.redirect(self._login_redirect(auth_info["uid"], redirect=redirect))

            except odoo.exceptions.AccessDenied as e:
                if user and settings["restrict_login_attempts"]:
                    attempts = user.failed_login_attempts + 1
                    if attempts >= settings["login_attempts"]:
                        now = fields.Datetime.now()
                        value = settings["block_time"]
                        delta_kwargs = {settings["block_time_unit"]: value} if settings["block_time_unit"] in ['minutes', 'hours', 'days'] else {'minutes': value}
                        
                        blocked_until = now + timedelta(**delta_kwargs)
                        user.write({"failed_login_attempts": 0, "login_blocked_until": blocked_until})
                        
                        values.update({
                            "login_blocked": True,
                            "remaining_seconds": int((blocked_until - now).total_seconds()),
                        })
                        return request.render("web.login", values)
                    else:
                        user.write({"failed_login_attempts": attempts})
                        values["error"] = _("Wrong login/password. Attempt %s of %s.") % (attempts, settings["login_attempts"])
                else:
                    values["error"] = _("Wrong login/password") if e.args == odoo.exceptions.AccessDenied().args else e.args[0]

        if "login" not in values and request.session.get("auth_login"):
            values["login"] = request.session.get("auth_login")

        if not odoo.tools.config["list_db"]:
            values["disable_database_manager"] = True

        response = request.render("web.login", values)
        response.headers.update({
            "Cache-Control": "no-cache",
            "X-Frame-Options": "SAMEORIGIN",
            "Content-Security-Policy": "frame-ancestors 'self'"
        })
        return response

    @http.route("/web/session/logout", type="http", auth="none")
    def session_logout(self, redirect="/web/login"):
        if request.session.uid:
            request.env["res.users"].sudo().browse(request.session.uid).write({
                "active_session_token": False,
                "last_activity": False,
            })
        request.session.pop("restrict_login_token", None)
        request.session.logout(keep_db=True)
        return request.redirect(redirect, 303)