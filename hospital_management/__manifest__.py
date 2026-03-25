{
    'name': 'Hospital Management system',
    'version': '1.0',
    'category': 'Healthcare',
    'summary': 'Manage doctors and patients',
    'author': 'Tejash Ardeshna',
    'license': 'LGPL-3',

    'depends': ['base', 'mail'],

    'data': [
    'security/ir.model.access.csv',
    'data/sequence.xml',          
    'views/res_partner_views.xml',
    'data/mail_templates.xml',     
    'views/appointment_views.xml',
    'views/appointment_action.xml',
    'views/specialization_views.xml',
    'views/menu.xml',
],

    'assets': {
        'web.assets_backend': [
            'hospital_management/static/src/css/hide_action.css',
        ],
    },

    'installable': True,
    'application': True,
}