{
    "name": "Sale Payment Status",
    "version": "19.0.1.0.0",
    "category": "sale",
    "summary": "Show payment status and amount due on Sale Orders",
    "author": "Tejash Ardeshna",
    "license": "LGPL-3",
    "depends": [
        "sale",
        "account",
        "mail",
    ],
    "data": [
        "views/sale_order_views.xml",
        "views/sale_order_search_views.xml",
    ],
    'assets': {
    'web.assets_backend': [
            'sale_payment_status/static/src/js/payment_notification.js',
        ],
    },
    "installable": True,
}