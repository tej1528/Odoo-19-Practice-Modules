/** @odoo-module **/

console.log("JS FILE LOADED");

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.AppointmentCreate = publicWidget.Widget.extend({

    selector: '.js_website_submit_form',

    events: {
        'change #doctor_id': '_onDoctorChange',
        'change #start_time': '_onStartTimeChange',
    },

    //------------------------------------------------------------------
    // START
    //------------------------------------------------------------------
    start() {

        console.log("Appointment Widget Started");

        this.last_duration = 30;

        return this._super(...arguments);
    },

    //------------------------------------------------------------------
    // Doctor Change
    //------------------------------------------------------------------
    _onDoctorChange: function (ev) {

        const self = this;

        const doctorId = parseInt(ev.currentTarget.value);

        console.log("Doctor Changed:", doctorId);

        // Empty
        if (!doctorId) {

            self.$('#fees').val('0.00');

            self.$('#specialization').val('');

            return;
        }

        // OLD STYLE AJAX RPC
        $.ajax({

            url: '/get_doctor_details',

            type: 'POST',

            contentType: 'application/json',

            data: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: {
                    doctor_id: doctorId
                },
                id: 1,
            }),

            success: function (response) {

                console.log("Doctor Data:", response);

                if (response.result) {

                    // Fees
                    self.$('#fees').val(
                        response.result.fees || 0
                    );

                    // Specialization
                    self.$('#specialization').val(
                        response.result.specialization || ''
                    );

                    // Duration
                    self.last_duration =
                        response.result.duration || 30;

                    // Update end time
                    self._updateEndTime();
                }
            },

            error: function (error) {

                console.error(
                    "Doctor fetch error:",
                    error
                );
            }

        });
    },

    //------------------------------------------------------------------
    // Start Time Change
    //------------------------------------------------------------------
    _onStartTimeChange: function () {

        this._updateEndTime();
    },

    //------------------------------------------------------------------
    // End Time Update
    //------------------------------------------------------------------
    _updateEndTime: function () {

        const startInput =
            this.$('#start_time').val();

        if (!startInput) {
            return;
        }

        let startDate = new Date(startInput);

        startDate.setMinutes(
            startDate.getMinutes() +
            this.last_duration
        );

        const year = startDate.getFullYear();

        const month = String(
            startDate.getMonth() + 1
        ).padStart(2, '0');

        const day = String(
            startDate.getDate()
        ).padStart(2, '0');

        const hours = String(
            startDate.getHours()
        ).padStart(2, '0');

        const minutes = String(
            startDate.getMinutes()
        ).padStart(2, '0');

        const endVal =
            `${year}-${month}-${day}T${hours}:${minutes}`;

        self = this;

        self.$('#end_time').val(endVal);

        console.log("End Time:", endVal);
    },

});