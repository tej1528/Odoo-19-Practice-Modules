{
    "name": "Restrict Login",
    "version": "19.0.1.0.0",
    "category": "Tools",
    "summary": "Restrict multiple user logins",
    "author": "Tejash Ardeshna",
    "depends": ["base", "web","mail",],
    "license": "LGPL-3",
    "data": [
        "views/res_config_settings_views.xml",
        "views/login_template.xml",
        'data/ir_cron.xml',
    ],
    "assets": {
    "web.assets_frontend": [
        "restrict_login/static/src/js/login_countdown.js",
    ],
},
    "installable": True,
    "application": False,
}