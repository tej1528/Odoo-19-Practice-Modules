{
    "name": "Attendance Checkout Summary",
    "version": "19.0.1.0.0",
    "category": "Human Resources",
    "summary": "Show checkout summary dialog before checkout",
    "author": "Tejash Ardeshna",
    "license": "LGPL-3",
    "depends": ["hr_attendance", "hr_timesheet", "hr_holidays",],
    "data": [
    ],
    "assets": {
    "web.assets_backend": [
        "chekout_summary_report/static/src/css/attendance_summary.css",
        "chekout_summary_report/static/src/js/attendance_summary_dialog.js",
        "chekout_summary_report/static/src/js/systray_patch.js",
        "chekout_summary_report/static/src/xml/attendance_summary_dialog.xml",
    ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}