from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
import random


class MobileOTPLogin(http.Controller):

    # -----------------------------------------
    # MOBILE LOGIN PAGE
    # -----------------------------------------
    @http.route('/web/login/mobile', type='http', auth='public', website=True)
    def mobile_login_page(self, **kw):
        return request.render('hospital_management.mobile_login_template', {})

    # -----------------------------------------
    # SEND OTP
    # -----------------------------------------
    @http.route('/web/login/send_otp', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def send_otp(self, **post):

        login_input = post.get('login')

        if not login_input:
            return request.redirect('/web/login/mobile?error=no_input')

        # detect email or mobile
        if '@' in login_input:
            domain = [('email', '=', login_input)]
        else:
            domain = [('phone', '=', login_input)]

        partner = request.env['res.partner'].sudo().search(domain, limit=1)

        if not partner:
            return request.redirect('/web/login/mobile?error=not_found')

        if not partner.email:
            return request.redirect('/web/login/mobile?error=no_email')

        # ✅ generate OTP
        otp = str(random.randint(100000, 999999))

        # ✅ GET CONFIG TIME
        expiry_min = int(
            request.env['ir.config_parameter']
            .sudo()
            .get_param('hospital.otp_expiry', 2)
        )

        # ✅ STORE SESSION
        request.session['login_input'] = login_input
        request.session['login_otp'] = otp
        request.session['otp_time'] = datetime.now().isoformat()

        # 🔥 IMPORTANT (UI TIMER SYNC)
        request.session['otp_expiry_seconds'] = expiry_min * 60

        # ✅ SEND EMAIL
        request.env['mail.mail'].sudo().create({
            'subject': 'Your OTP for Login',
            'body_html': f'<p>Your OTP is: <b>{otp}</b></p>',
            'email_to': partner.email,
            'email_from': 'workwithme5001@gmail.com',
        }).send()

        return request.redirect('/web/login/verify_otp')

    # -----------------------------------------
    # OTP PAGE + TIMER
    # -----------------------------------------
    @http.route('/web/login/verify_otp', type='http', auth='public', website=True)
    def verify_otp_page(self, **kw):

        # ✅ session mathi data levu
        otp_time_str = request.session.get('otp_time')
        expiry_seconds = request.session.get('otp_expiry_seconds', 120)

        remaining_seconds = expiry_seconds

        # ✅ calculate remaining time
        if otp_time_str:
            try:
                otp_time = datetime.fromisoformat(otp_time_str)
                diff = datetime.now() - otp_time

                remaining_seconds = max(0, expiry_seconds - int(diff.total_seconds()))
            except Exception:
                remaining_seconds = 0

        # ✅ render with correct remaining time
        return request.render('hospital_management.otp_verify_template', {
            'otp_seconds': remaining_seconds
        })

    # -----------------------------------------
    # VERIFY OTP + LOGIN
    # -----------------------------------------
    @http.route('/web/login/verify_otp_post', type='http', auth='public', website=True, methods=['POST'], csrf=False)
    def verify_otp_post(self, **post):

        otp_input = post.get('otp')
        session_otp = request.session.get('login_otp')
        login_input = request.session.get('login_input')

        if not otp_input or not session_otp:
            return request.redirect('/web/login/mobile?error=invalid_request')

        # ✅ GET CONFIG EXPIRY
        expiry_min = int(
            request.env['ir.config_parameter']
            .sudo()
            .get_param('hospital.otp_expiry', 2)
        )

        otp_time_str = request.session.get('otp_time')

        if otp_time_str:
            otp_time = datetime.fromisoformat(otp_time_str)

            # 🔥 FINAL EXPIRY CHECK
            if datetime.now() > otp_time + timedelta(minutes=expiry_min):

                # clear session
                request.session.pop('login_otp', None)
                request.session.pop('login_input', None)
                request.session.pop('otp_time', None)
                request.session.pop('otp_expiry_seconds', None)

                return request.redirect('/web/login/verify_otp?error=expired')

        # ❌ wrong otp
        if otp_input != session_otp:
            return request.redirect('/web/login/verify_otp?error=invalid')

        # ✅ find partner
        if '@' in login_input:
            domain = [('email', '=', login_input)]
        else:
            domain = [('phone', '=', login_input)]

        partner = request.env['res.partner'].sudo().search(domain, limit=1)

        if not partner or not partner.user_ids:
            return request.redirect('/web/login?error=no_user')

        user = partner.user_ids[0]

        # ✅ LOGIN
        request.session.uid = user.id
        request.session.login = user.login
        request.session.session_token = user._compute_session_token(request.session.sid)

        # cleanup
        request.session.pop('login_otp', None)
        request.session.pop('login_input', None)
        request.session.pop('otp_time', None)
        request.session.pop('otp_expiry_seconds', None)

        return request.redirect('/my/home')

    # RESEND OTP
    # -----------------------------------------
    @http.route('/web/login/resend_otp', type='jsonrpc', auth='public', csrf=False)
    def resend_otp(self):

        login_input = request.session.get('login_input')

        if not login_input:
            return {"error": "session_expired"}

        if '@' in login_input:
            domain = [('email', '=', login_input)]
        else:
            domain = [('phone', '=', login_input)]

        partner = request.env['res.partner'].sudo().search(domain, limit=1)

        # ✅ NEW OTP
        otp = str(random.randint(100000, 999999))

        # ✅ GET CONFIG TIME AGAIN
        expiry_min = int(
            request.env['ir.config_parameter']
            .sudo()
            .get_param('hospital.otp_expiry', 2)
        )

        # 🔥 RESET SESSION
        request.session['login_otp'] = otp
        request.session['otp_time'] = datetime.now().isoformat()
        request.session['otp_expiry_seconds'] = expiry_min * 60

        # ✅ SEND MAIL
        if partner and partner.email:
            request.env['mail.mail'].sudo().create({
                'subject': 'Resend OTP',
                'body_html': f'<p>Your OTP is: <b>{otp}</b></p>',
                'email_to': partner.email,
                'email_from': 'workwithme5001@gmail.com',
            }).send()

        # 🔥 FINAL RETURN (IMPORTANT)
        return {
            "status": "resent",
            "seconds": expiry_min * 60
        }