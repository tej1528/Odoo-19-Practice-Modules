{
    "name": "Hide Tax",
    "version": "19.0.1.0.0",
    "category": "account",
    "summary": "Hide Tax from account module",
    "description": "",
    "author": "Tejash Ardeshna",
    "website": "",
    "license": "LGPL-3",
    "depends": ["account","portal",],
    "data": [
        'views/res_config_settings_views.xml',
    'views/account_move_views.xml',
    ],

    "installable": True,
    "application": False,
    "auto_install": False,
}