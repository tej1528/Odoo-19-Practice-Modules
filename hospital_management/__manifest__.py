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
    'data/mail_templates.xml',
    'data/appointment_status_data.xml',
    'reports/appointment_report_template.xml',
    'reports/appointment_report.xml',
    'reports/appointment_report_Filtering_template.xml',
    'wizard/appointment_report_wizard.xml',
    'views/res_partner_views.xml',
    'views/appointment_views.xml',
    'views/appointment_action.xml',
    'views/res_config_settings_view.xml',
    'views/specialization_views.xml',
    'views/menu.xml',
],

    'assets': {
        'web.assets_backend': [
            'hospital_management/static/src/js/processing_timer.js',
            'hospital_management/static/src/js/calendar_reload.js',
            'hospital_management/static/src/css/hide_action.css',
            'hospital_management/static/src/xml/processing_timer.xml',
        ],
    },

    'installable': True,
    'application': True,
}