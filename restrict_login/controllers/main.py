# -*- coding: utf-8 -*-
from datetime import timedelta
import logging
import uuid

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

    def _get_company(self, login_username=None):
        """ યુઝરના લોગિન ઇનપુટ પરથી સાચી કંપની શોધવી """
        if request.env.user and request.env.user.id and not request.env.user._is_public():
            return request.env.user.company_id.sudo()
        
        if login_username:
            user = request.env["res.users"].sudo().search([("login", "=", login_username)], limit=1)
            if user and user.company_id:
                return user.company_id.sudo()

        allowed_companies = request.env.context.get('allowed_company_ids')
        if allowed_companies:
            return request.env['res.company'].sudo().browse(allowed_companies[0])
            
        return request.env['res.company'].sudo().search([], limit=1)

    def _get_login_settings(self, login_username=None):
        company = self._get_company(login_username)
        return {
            "restrict_multiple_login": company.restrict_multiple_login,
            "force_new_login": company.force_new_login,
            "restrict_login_attempts": company.restrict_login_attempts,
            "login_attempts": company.login_attempts or 5,
            "block_time": company.block_time or 1,
            "block_time_unit": company.block_time_unit or "minutes",
            "session_timeout": company.session_timeout or 30,
        }

    def _get_login_values(self, login_username=None):
        values = {
            k: v
            for k, v in request.params.items()
            if k in SIGN_UP_REQUEST_PARAMS
        }

        try:
            values["databases"] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values["databases"] = None

        settings = self._get_login_settings(login_username)
        values["show_force_login_checkbox"] = False
        values["login_blocked"] = False
        return values, settings

    @http.route("/web/login", type="http", auth="none", sitemap=False)
    def web_login(self, redirect=None, **kw):
        ensure_db()
        request.params["login_success"] = False

        if (
            request.httprequest.method == "GET"
            and redirect
            and request.session.uid
        ):
            return request.redirect(redirect)

        values, settings = self._get_login_values()

        if request.httprequest.method == "POST":
            credential = {
                k: v
                for k, v in request.params.items()
                if k in CREDENTIAL_PARAMS and v
            }
            credential.setdefault("type", "password")
            login = credential.get("login")
            password = credential.get("password")

            values, settings = self._get_login_values(login_username=login)

            user = request.env["res.users"].sudo().search(
                [("login", "=", login)],
                limit=1,
            )
            force_login_checked = bool(request.params.get("force_login"))

            # ૧. જો યુઝર ઓલરેડી બ્લોક હોય, તો ટાઈમર બતાવીને રિટર્ન કરો
            if (
                user
                and settings["restrict_login_attempts"]
                and user.login_blocked_until
            ):
                now = fields.Datetime.now()
                if user.login_blocked_until > now:
                    remaining_seconds = int((user.login_blocked_until - now).total_seconds())
                    values.update({
                        "login_blocked": True,
                        "remaining_seconds": remaining_seconds,
                        "error": _("Maximum login attempts reached. Your account is temporarily blocked."),
                    })
                    return request.render("web.login", values)
                
                # જો બ્લોક સમય પૂરો થઈ ગયો હોય, તો અટેમ્પ્ટ રીસેટ કરો
                user.write({
                    "failed_login_attempts": 0,
                    "login_blocked_until": False,
                })

            # ૨. પાસવર્ડ ઓથેન્ટિકેશન (ઓડુની ડિફોલ્ટ પાસવર્ડ વેરિફિકેશન મેથડથી)
            is_password_correct = False
            if user and password:
                # Odoo ઇન્ટર્નલી પાસવર્ડ હેશ ચેક કરવા પાસલિબ વાપરે છે, તેનાથી સ્ટેટ બગડશે નહીં
                is_password_correct = user._crypt_context().verify(password, user.password)

            # ૩. જો પાસવર્ડ ખોટો હોય તો અટેમ્પ્ટ કાઉન્ટ કરો અને બ્લોક કરો
            if not is_password_correct and user and settings["restrict_login_attempts"]:
                new_cr = request.registry.cursor()
                try:
                    env_cr = request.env(cr=new_cr)
                    user_cr = env_cr["res.users"].sudo().browse(user.id)
                    
                    new_attempts = user_cr.failed_login_attempts + 1
                    user_cr.write({"failed_login_attempts": new_attempts})

                    if new_attempts >= settings["login_attempts"]:
                        block_duration = settings["block_time"]
                        unit = settings["block_time_unit"]

                        if unit == "minutes":
                            delta = timedelta(minutes=block_duration)
                        elif unit == "hours":
                            delta = timedelta(hours=block_duration)
                        else:
                            delta = timedelta(days=block_duration)

                        blocked_until = fields.Datetime.now() + delta
                        user_cr.write({"login_blocked_until": blocked_until})
                        
                        values.update({
                            "login_blocked": True,
                            "remaining_seconds": int(delta.total_seconds()),
                            "error": _("Maximum login attempts reached. Your account is temporarily blocked."),
                        })
                    else:
                        max_att = settings["login_attempts"]
                        values["error"] = _("Wrong login/password. Attempt %s of %s.") % (new_attempts, max_att)
                    
                    new_cr.commit()
                finally:
                    new_cr.close()

                return request.render("web.login", values)

            # ૪. મલ્ટીપલ લોગિન માટેનું વેલિડેશન (જ્યારે પાસવર્ડ ૧૦૦% સાચો હશે ત્યારે જ રન થશે)
            if (
                is_password_correct
                and user
                and settings["restrict_multiple_login"]
                and user.active_session_token
                and user.last_activity
            ):
                limit = fields.Datetime.now() - timedelta(minutes=settings["session_timeout"])
                if user.last_activity > limit:
                    if settings["force_new_login"] and not force_login_checked:
                        values["error"] = _("You are already logged in on another browser.")
                        values["show_force_login_checkbox"] = True
                        return request.render("web.login", values)
                    
                    if settings["force_new_login"] and force_login_checked:
                        user.write({
                            "active_session_token": False,
                            "last_activity": False,
                        })
                    else:
                        values["error"] = _("You are already logged in on another browser. Parallel login is restricted.")
                        return request.render("web.login", values)

            # ૫. સ્ટાન્ડર્ડ ઓડુ ઓથેન્ટિકેશન અને લોગિન સક્સેસ
            try:
                auth_info = request.session.authenticate(request.env, credential)
                request.params["login_success"] = True
                current_user = request.env["res.users"].sudo().browse(auth_info["uid"])

                if settings["restrict_login_attempts"]:
                    current_user.write({
                        "failed_login_attempts": 0,
                        "login_blocked_until": False,
                    })

                if settings["restrict_multiple_login"]:
                    token = str(uuid.uuid4())
                    current_user.write({
                        "active_session_token": token,
                        "last_activity": fields.Datetime.now(),
                    })
                    request.session["restrict_login_token"] = token

                return request.redirect(
                    self._login_redirect(auth_info["uid"], redirect=redirect)
                )

            except odoo.exceptions.AccessDenied:
                values["error"] = _("Wrong login/password")
                return request.render("web.login", values)

        return request.render("web.login", values)