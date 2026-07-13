# -*- coding: utf-8 -*-
{
    "name": "Restrict Login",
    "version": "19.0.1.0.0",
    "summary": "Restrict Multiple Login and Login Attempt Security",
    "category": "Tools",
    "author": "Tejash Ardeshna",
    "license": "LGPL-3",
    "depends": [
        "base",
        "web",
    ],
    "data": [
        "views/res_config_settings_views.xml",
        "views/login_template.xml",
        "data/ir_cron.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "restrict_login/static/src/js/login_countdown.js",
        ],
    },
    "installable": True,
    "application": False,
}