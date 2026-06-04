{
    "name": "Sale Merge order",
    "version": "19.0.1.0.0",
    "category": "Sales",
    "summary": "Merge multiple order into one order",
    "description": "",
    "author": "Tejash Ardeshna",
    "website": "",
    "license": "LGPL-3",
    "depends": ["sale"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/sale_order_merge_wizard_views.xml",
        "data/server_action.xml",
    ],

    "installable": True,
    "application": False,
    "auto_install": False,
}