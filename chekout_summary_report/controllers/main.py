from odoo import fields, http
from odoo.http import request

class AttendanceSummaryController(http.Controller):

    @http.route(
        "/attendance/checkout_summary",
        type="jsonrpc",
        auth="user",
    )
    def checkout_summary(self):
        employee = request.env.user.employee_id
        if not employee:
            return {}

        attendance = request.env["hr.attendance"].sudo().search(
            [
                ("employee_id", "=", employee.id),
                ("check_out", "=", False),
            ],
            limit=1,
        )

        today = fields.Date.context_today(request.env.user)
        current_time = fields.Datetime.context_timestamp(request.env.user,fields.Datetime.now(),)
        check_in_time = ""
        worked_time = "0:00"
        if attendance and attendance.check_in:
            check_in = fields.Datetime.context_timestamp(
                request.env.user,
                attendance.check_in,
            )

            check_in_time = check_in.strftime("%I:%M %p")
            duration = current_time - check_in
            total_minutes = int(duration.total_seconds() // 60)
            hours, minutes = divmod(total_minutes, 60)
            worked_time = f"{hours}:{minutes:02d}"

        timesheets = request.env["account.analytic.line"].sudo().search([
            ("employee_id", "=", employee.id),
            ("date", "=", today),
        ])

        activities = [
            {   
                "id": line.id,
                "description": line.name or "",
                "project": line.project_id.name or "",
                "task": line.task_id.name or "",
                "hours": line.unit_amount,
            }
            for line in timesheets
        ]

        leave = request.env["hr.leave"].sudo().search(
            [
                ("employee_id", "=", employee.id),
                ("state", "=", "validate"),
                ("request_date_from", "=", today),
            ],
            limit=1,
        )

        return {
            "employee": employee.name,
            "check_in": check_in_time,
            "check_out": current_time.strftime("%I:%M %p"),
            "worked_time": worked_time,
            "activities": activities,
            "tomorrow": {
                "message": (
                    f"Leave : {leave.holiday_status_id.name}"
                    if leave
                    else "Working Day"
                ),
            },
        }