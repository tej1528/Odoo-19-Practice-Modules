# -*- coding: utf-8 -*-
{
    "name": "Project Task Status Management",
    "version": "19.0.1.0.0",
    "category": "Project",
    "summary": "Manage project task stage transitions and custom statuses",
    "author": "Tejash Ardeshna",
    "license": "LGPL-3",
    "depends": [
        "project",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/project_task_status_data.xml",
        'data/project_task_approval_mail.xml',
        "wizard/task_reject_wizard_views.xml",
        "views/project_task_status_views.xml",
        "views/project_task_type_views.xml",
        "views/project_task_views.xml",
        "views/project_task_hide_recurring_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "project_task_status_management3/static/src/js/status_selection.js",
            "project_task_status_management3/static/src/xml/status_selection.xml",
            "project_task_status_management3/static/src/scss/status_selection.scss",
        ],
    },
    "installable": True,
    "application": False,
}