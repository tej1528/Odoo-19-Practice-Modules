{
    "name": "Stock Control",
    "version": "19.0.1.0.0",
    "category": "Product Category",
    "summary": "Merge multiple order into one order",
    "author": "Tejash Ardeshna",
    "license": "LGPL-3",
    "depends": [ "sale_management", "stock", "purchase", ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/over_receipt_wizard.xml"
    ],

    "installable": True,
    "application": False,
    "auto_install": False,
}