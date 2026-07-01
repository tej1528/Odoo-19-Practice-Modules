{
    "name": "Hide Tax",
    "version": "19.0.1.0.0",
    "category": "account",
    "summary": "Hide taxes from forms, lists, reports and portal based on company settings.",
    "description": """
        Provides a company-level configuration to completely hide tax information across:
        - Invoice & Vendor Bill Forms
        - Invoice & Vendor Bill Tree/List Views
        - Journal Items List View
        - Customer Portal
        - PDF Printed Reports
    """,
    "author": "Tejash Ardeshna",
    "website": "",
    "license": "LGPL-3",
    "depends": ["account","portal",],
    "data": [
        "security/hide_tax_groups.xml",
        "views/account_move_views.xml",
        "views/account_move_list_views.xml",
        "report/account_invoice_report.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "Hide_Tax_from_Invoice/static/src/js/tax_totals_patch.js",
            "Hide_Tax_from_Invoice/static/src/js/account_move_list_renderer_patch.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}