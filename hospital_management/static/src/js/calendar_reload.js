/** @odoo-module **/

import { registry } from "@web/core/registry";
import { calendarView } from "@web/views/calendar/calendar_view";
import { CalendarController } from "@web/views/calendar/calendar_controller";
import { useService } from "@web/core/utils/hooks";
import { serializeDateTime } from "@web/core/l10n/dates";

class HospitalCalendarController extends CalendarController {
    setup() {
        super.setup();
        this.orm = useService("orm");
    }

    async createRecord(params) {
        const start = params.context?.default_start_time;
        if (start) {
            // Fetch the duration from Odoo Config Parameters
            const durationStr = await this.orm.call(
                "ir.config_parameter",
                "get_param",
                ["hospital.appointment_duration", "30"]
            );
            const duration = parseInt(durationStr);

            // Calculate end date
            const startDate = new Date(start);
            const endDate = new Date(startDate.getTime() + duration * 60000);

            // Set the default end time in context so the wizard picks it up
            params.context.default_end_time = serializeDateTime(luxon.DateTime.fromJSDate(endDate));
        }
        return super.createRecord(params);
    }
}

export const hospitalCalendarView = {
    ...calendarView,
    Controller: HospitalCalendarController,
};

registry.category("views").add("hospital_calendar", hospitalCalendarView);