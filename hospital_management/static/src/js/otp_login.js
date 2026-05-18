/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.OTPLogin = publicWidget.Widget.extend({

    selector: '.otp_form',

    events: {
        'click #resend_btn': '_resendOTP',
        'submit': '_onSubmit',   // ✅ FIX: form submit control
    },

    start() {
        this._super(...arguments);

        this.interval = null;

        let seconds = document.getElementById("otp_seconds")?.value || 120;

        this.startTimer(parseInt(seconds));
    },

    startTimer(duration) {

        let timer = duration;

        let display = document.getElementById("timer_value");
        let resend = document.getElementById("resend_section");

        // ✅ reset resend button
        if (resend) resend.style.display = "none";

        // ✅ clear old timer
        if (this.interval) {
            clearInterval(this.interval);
        }

        this.interval = setInterval(() => {

            let minutes = Math.floor(timer / 60);
            let seconds = timer % 60;

            seconds = seconds < 10 ? "0" + seconds : seconds;

            if (display) {
                display.textContent = minutes + ":" + seconds;
            }

            // ✅ EXPIRED
            if (timer <= 0) {
                clearInterval(this.interval);

                if (display) {
                    display.textContent = "Expired";
                }

                if (resend) {
                    resend.style.display = "block";
                }

                return;
            }

            timer--;

        }, 1000);
    },

    // ✅ BLOCK SUBMIT IF EXPIRED
    _onSubmit(ev) {

        let timerText = document.getElementById("timer_value")?.textContent;

        if (timerText === "Expired") {
            ev.preventDefault();
            alert("OTP expired. Please resend OTP.");
        }
    },

    // ✅ RESEND OTP WITH TIMER SYNC
    async _resendOTP() {

        console.log("✅ Resend button clicked");

        let res = await rpc("/web/login/resend_otp", {});

        console.log("RPC RESPONSE:", res);

        if (res.error) {
            alert(res.error);
            return;
        }

        alert("OTP Resent");

        if (res.seconds) {
            document.getElementById("otp_seconds").value = res.seconds;
        }

        let seconds = document.getElementById("otp_seconds")?.value || 120;

        this.startTimer(parseInt(seconds));
    },
});