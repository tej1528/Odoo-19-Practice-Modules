{
    'name': 'POS CHANGES',
    'version': '1.0',
    'summary': 'Manage order on POS module',
    'license': 'LGPL-3',
    'author': 'Tejash Ardeshna',
    'category': 'Point of Sale',
    'depends': ['point_of_sale'],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_changes/static/src/js/discount_popup.js',
            'pos_changes/static/src/js/order_discount.js',
            'pos_changes/static/src/js/discount_amount_button.js',
            'pos_changes/static/src/xml/control_buttons.xml',
            'pos_changes/static/src/xml/discount_popup.xml',
            'pos_changes/static/src/xml/receipt_template.xml',
            
            'pos_changes/static/src/js/receipt_cashier.js',
        ],
        
    },
    'data': [
        'views/pos_config_view.xml',
    ],
    'installable': True,
}