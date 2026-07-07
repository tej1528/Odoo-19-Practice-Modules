from datetime import timedelta

from odoo import fields, http
from odoo.http import request


class AttendanceSummaryController(http.Controller):

    @http.route("/attendance/checkout_summary",type="jsonrpc",auth="user",methods=["POST"],csrf=False,)
    def checkout_summary(self):
        user = request.env.user
        employee = user.employee_id

        if not employee:
            return {}

        today = fields.Date.context_today(employee)
        tomorrow = today + timedelta(days=1)
        now = fields.Datetime.context_timestamp( employee, fields.Datetime.now(), )

        current_attendance = request.env["hr.attendance"].sudo().search(
            [
                ("employee_id", "=", employee.id),
                ("check_out", "=", False),
            ],
            limit=1,
        )

        check_in_time = ""
        if current_attendance and current_attendance.check_in:
            check_in = fields.Datetime.context_timestamp( employee, current_attendance.check_in, )
            check_in_time = check_in.strftime("%I:%M %p")

        attendances = request.env["hr.attendance"].sudo().search(
            [("employee_id", "=", employee.id),
             ( "check_in", ">=", fields.Datetime.to_datetime(today), ),
             ( "check_in", "<", fields.Datetime.to_datetime(today + timedelta(days=1)), ), ],
            order="check_in",
        )

        attendance_sessions = []
        for attendance in attendances:
            check_in = fields.Datetime.context_timestamp( employee, attendance.check_in, )
            if attendance.check_out:
                check_out = fields.Datetime.context_timestamp(employee,attendance.check_out,)
                duration = check_out - check_in
                check_out_time = check_out.strftime("%I:%M %p")
            else:

                duration = now - check_in
                check_out_time = ""

            total_minutes = int(duration.total_seconds() // 60)
            hours, minutes = divmod(total_minutes, 60)
            attendance_sessions.append({
                "check_in": check_in.strftime("%I:%M %p"),
                "check_out": check_out_time,
                "worked": f"{hours}:{minutes:02d}",
            })

        timesheets = request.env["account.analytic.line"].sudo().search(
            [
                ("employee_id", "=", employee.id),
                ("date", "=", today),
            ]
        )

        activities = []
        for line in timesheets:
            hrs = int(line.unit_amount)
            mins = round((line.unit_amount - hrs) * 60)
            if mins == 60:
                hrs += 1
                mins = 0
            activities.append({
                "id": line.id,
                "description": line.name or "",
                "project": line.project_id.name or "",
                "task": line.task_id.name or "",
                "hours": f"{hrs:02d}:{mins:02d}",
            })

        leaves = request.env["hr.leave"].sudo().search(
            [
                ("employee_id", "=", employee.id),
                ("state", "=", "validate"),
                ("request_date_from", "<=", tomorrow),
                ("request_date_to", ">=", tomorrow),
            ],
            order="request_date_from",
        )

        leave_list = []
        for leave in leaves:
            if leave.request_unit_half:
                period = (
                    "Morning"
                    if leave.request_date_from_period == "am"
                    else "Afternoon"
                )
            else:
                period = "Full Day"

            leave_list.append({
                "type": leave.holiday_status_id.name,
                "period": period,
            })

        public_holiday = request.env["resource.calendar.leaves"].sudo().search(
            [
                (
                    "date_from",
                    "<=",
                    fields.Datetime.to_datetime(tomorrow),
                ),
                (
                    "date_to",
                    ">=",
                    fields.Datetime.to_datetime(tomorrow),
                ),
                "|",
                ("calendar_id", "=", False),
                (
                    "calendar_id",
                    "=",
                    employee.resource_calendar_id.id,
                ),
            ],
            limit=1,)

        if leave_list:
            tomorrow_summary = {
                "leaves": leave_list,
                "message": "",
                "good_message": "Enjoy your leave. Have a relaxing day!",
            }

        elif public_holiday:
            tomorrow_summary = {
                "leaves": [],
                "message": f"Holiday : {public_holiday.name}",
                "good_message": "Happy Holiday! Enjoy your day.",
            }

        else:
            tomorrow_summary = {
                "leaves": [],
                "message": "Working Day",
                "good_message": "Have a productive day ahead. See you tomorrow!",
            }

        return {
            "employee": employee.name,
            "check_in": check_in_time,
            "attendance_sessions": attendance_sessions,
            "activities": activities,
            "tomorrow": tomorrow_summary,
        }