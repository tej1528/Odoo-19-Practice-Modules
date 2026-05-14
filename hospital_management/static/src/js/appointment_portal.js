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

        // =====================================================
        // DOCTOR CHANGE
        // =====================================================

        _onDoctorChange(ev) {

            const doctor = ev.currentTarget.selectedOptions[0];
            if (!doctor) return;

            const specSelect = this.el.querySelector("#specialization_id");
            const doctorSelect = this.el.querySelector("#doctor_id");
            const feesInput = this.el.querySelector("#fees");

            const specId = doctor.dataset.specialization;
            const fees = doctor.dataset.fees;

            // ✅ SET SPECIALIZATION
            if (specId && specSelect) {
                specSelect.value = specId;
            }

            // ✅ SET FEES
            if (feesInput && fees) {
                feesInput.value = parseFloat(fees).toFixed(2);
            }

            // 🔥🔥 MAIN FIX: FILTER DOCTORS BASED ON THIS SPECIALIZATION

            if (doctorSelect && specId) {

                // store selected doctor
                const selectedDoctorId = doctor.value;

                // reset all doctors
                doctorSelect.innerHTML = this.allDoctors;

                const options = doctorSelect.querySelectorAll("option");

                options.forEach(option => {

                    if (!option.value) return;

                    const doctorSpec = option.dataset.specialization;

                    if (doctorSpec !== specId) {
                        option.remove();
                    }
                });

                // reselect same doctor
                doctorSelect.value = selectedDoctorId;
            }
        },

        // =====================================================
        // SPECIALIZATION CHANGE
        // =====================================================

        _onSpecializationChange(ev) {

            const specId = ev.currentTarget.value;
            const doctorSelect = this.el.querySelector("#doctor_id");

            if (!doctorSelect) return;

            // ✅ STORE CURRENT SELECTED DOCTOR
            const currentDoctorId = doctorSelect.value;

            // ✅ RESET ALL DOCTORS
            doctorSelect.innerHTML = this.allDoctors;

            const options = doctorSelect.querySelectorAll("option");

            options.forEach(option => {

                if (!option.value) return;

                const doctorSpec = option.dataset.specialization;

                // ❌ REMOVE NON-MATCH
                if (specId && doctorSpec !== specId) {
                    option.remove();
                }
            });

            const remainingDoctors =
                doctorSelect.querySelectorAll("option[value]");

            // ✅ TRY TO KEEP SAME DOCTOR SELECTED
            if (currentDoctorId) {
                const exists = doctorSelect.querySelector(
                    `option[value="${currentDoctorId}"]`
                );

                if (exists) {
                    doctorSelect.value = currentDoctorId;
                } else if (remainingDoctors.length > 0) {
                    doctorSelect.value = remainingDoctors[0].value;
                }
            } else if (remainingDoctors.length > 0) {
                doctorSelect.value = remainingDoctors[0].value;
            }

            // 🔥 IMPORTANT → TRIGGER DOCTOR CHANGE AGAIN
            doctorSelect.dispatchEvent(new Event('change'));
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