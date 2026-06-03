# -*- coding: utf-8 -*-
{
    'name': 'POS CHANGES',
    'version': '1.0',
    'summary': 'Manage order on POS module',
    'license': 'LGPL-3',
    'author': 'Tejash Ardeshna',
    'category': 'Point of Sale',

    'depends': [
        'point_of_sale',
        'pos_discount',
    ],

    'assets': {

        'point_of_sale._assets_pos': [
            'pos_changes/static/src/xml/custom_discount_number_popup.xml',
            'pos_changes/static/src/xml/control_buttons.xml',
            # 'pos_changes/static/src/xml/receipt_template.xml',
            'pos_changes/static/src/xml/order_summary.xml',
            'pos_changes/static/src/xml/receipt_discount.xml',

            'pos_changes/static/src/js/custom_discount_number_popup.js',
            'pos_changes/static/src/js/discount_buttons.js',
            'pos_changes/static/src/js/order_discount.js',
        ],

        
    },

    'data': [
        'views/pos_config_view.xml',
        'views/pos_order_view.xml',
    ],

    'installable': True,
}