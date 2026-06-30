{
    "name": "Hide Tax",
    "version": "19.0.1.0.0",
    "category": "account",
    "summary": "Hide taxes from forms, lists, reports and portal",
    
    "description": """
    Hide taxes from
    - Invoice Form
    - Vendor Bill Form
    - Invoice List
    - Vendor Bill List
    - Journal Items
    - Invoice PDF
    - Vendor Bill PDF
    - Customer Portal
    using a company setting.
    """,

    "author": "Tejash Ardeshna",
    "website": "",
    "license": "LGPL-3",
    "depends": ["account","portal",],
    "data": [
    'views/res_config_settings_views.xml',
    'views/account_move_views.xml',
    "report/account_invoice_report.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}