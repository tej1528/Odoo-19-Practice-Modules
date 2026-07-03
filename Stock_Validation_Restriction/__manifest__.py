{
    "name": "Stock Control",
    "version": "19.0.1.0.0",
    "category": "Inventory",
    "summary": "Stock validation with barcode support",
    "author": "Tejash Ardeshna",
    "license": "LGPL-3",
    "depends": [ "sale_management", "stock", "purchase",],
    "data": [
        "security/ir.model.access.csv",
        "wizard/over_receipt_wizard.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "Stock_Validation_Restriction/static/src/js/barcode_scan.js",
            "Stock_Validation_Restriction/static/src/scss/notification.scss",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}