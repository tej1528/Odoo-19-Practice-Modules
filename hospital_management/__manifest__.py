{
    'name': 'Hospital Management system',
    'version': '1.0',
    'category': 'Healthcare',
    'summary': 'Manage doctors and patients',
    'author': 'Tejash Ardeshna',
    'license': 'LGPL-3',

    'depends': ['base', 'mail', 'base_setup', 'web'],
    'images': ['static/description/icon.png'],

    'data': [
    'security/ir.model.access.csv',
    'data/sequence.xml',          
    'views/res_partner_views.xml',
    'reports/appointment_report.xml',
    'data/mail_templates.xml',     
    'views/appointment_views.xml',
    'views/appointment_action.xml',
    'views/res_config_settings_view.xml',
    'views/specialization_views.xml',
    'views/menu.xml',
    'reports/appointment_report_template.xml',
],

    'assets': {
        'web.assets_backend': [
            'hospital_management/static/src/js/calendar_reload.js',
            'hospital_management/static/src/css/hide_action.css',
        ],
    },

    'installable': True,
    'application': True,
}