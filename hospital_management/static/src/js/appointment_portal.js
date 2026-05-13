/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

console.log("Appointment Portal JS Loaded");

publicWidget.registry.AppointmentPortal =
    publicWidget.Widget.extend({

        selector: '.o_portal_appointment_form',

        events: {
            'change #doctor_id': '_onDoctorChange',
            'change #specialization_id': '_onSpecializationChange',
            'change #start_time': '_onStartTimeChange',
        },

        init() {

            this._super(...arguments);

            // default duration
            this.last_duration = 30;
        },

        start() {

            console.log("Widget Started");

            // store all doctor options
            this.allDoctors =
                this.el.querySelector("#doctor_id").innerHTML;

            return this._super(...arguments);
        },

        // =====================================================
        // DOCTOR CHANGE
        // =====================================================

        _onDoctorChange(ev) {

            const doctor =
                ev.currentTarget.selectedOptions[0];

            if (!doctor) {
                return;
            }

            // specialization id from option
            const specId =
                doctor.dataset.specialization;

            const specSelect =
                this.el.querySelector("#specialization_id");

            const feesInput =
                this.el.querySelector("#fees");

            // AUTO SELECT SPECIALIZATION
            if (specId && specSelect) {

                specSelect.value = specId;
            }

            // FEES
            const fees =
                doctor.dataset.fees;

            if (feesInput && fees) {

                feesInput.value =
                    parseFloat(fees).toFixed(2);
            }
        },

        // =====================================================
        // SPECIALIZATION CHANGE
        // =====================================================

        _onSpecializationChange(ev) {

            const specId =
                ev.currentTarget.value;

            const doctorSelect =
                this.el.querySelector("#doctor_id");

            if (!doctorSelect) {
                return;
            }

            // restore all doctors
            doctorSelect.innerHTML =
                this.allDoctors;

            // filter doctors
            const options =
                doctorSelect.querySelectorAll("option");

            options.forEach(option => {

                // skip empty option
                if (!option.value) {
                    return;
                }

                const doctorSpec =
                    option.dataset.specialization;

                // remove unmatched doctors
                if (
                    specId &&
                    doctorSpec !== specId
                ) {

                    option.remove();
                }
            });

            // auto select first doctor
            const remainingDoctors =
                doctorSelect.querySelectorAll("option[value]");

            if (
                remainingDoctors.length > 0 &&
                remainingDoctors[0].value
            ) {

                doctorSelect.value =
                    remainingDoctors[0].value;

                doctorSelect.dispatchEvent(
                    new Event('change')
                );
            }
        },

        // =====================================================
        // START TIME CHANGE
        // =====================================================

        _onStartTimeChange() {

            this._updateEndTime();
        },

        // =====================================================
        // AUTO END TIME
        // =====================================================

        _updateEndTime() {

            const start =
                this.el.querySelector("#start_time")?.value;

            const endInput =
                this.el.querySelector("#end_time");

            if (!start || !endInput) {
                return;
            }

            let date = new Date(start);

            date.setMinutes(
                date.getMinutes() + this.last_duration
            );

            const year = date.getFullYear();

            const month = String(
                date.getMonth() + 1
            ).padStart(2, '0');

            const day = String(
                date.getDate()
            ).padStart(2, '0');

            const hour = String(
                date.getHours()
            ).padStart(2, '0');

            const minute = String(
                date.getMinutes()
            ).padStart(2, '0');

            endInput.value =
                `${year}-${month}-${day}T${hour}:${minute}`;
        },

    });