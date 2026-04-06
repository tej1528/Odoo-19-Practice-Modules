/** @odoo-module **/

import { CalendarController } from "@web/views/calendar/calendar_controller";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { DateTime } from "luxon";

class CustomCalendarController extends CalendarController {

    setup() {
        super.setup();
        this.action = useService("action");
    }

    formatDateTime(date) {
        const d = new Date(date);

        return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ` +
            `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`;
    }

    async createRecord(data) {

        const start = DateTime.fromJSDate(data.start).toFormat('yyyy-MM-dd HH:mm:ss');

        const end = data.end
            ? DateTime.fromJSDate(data.end).toFormat('yyyy-MM-dd HH:mm:ss')
            : DateTime.fromJSDate(data.start)
                .plus({ minutes: 30 })
                .toFormat('yyyy-MM-dd HH:mm:ss');

        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Create Appointment",
            res_model: "appointment.wizard",
            views: [[false, "form"]],
            target: "new",
            context: {
                default_start_time: start,
                default_end_time: end,
            },
        });
    }
}

registry.category("views").add("custom_calendar", {
    ...registry.category("views").get("calendar"),
    Controller: CustomCalendarController,
});