{
    'name': 'Hospital Management system',
    'version': '1.0',
    'category': 'Healthcare',
    'summary': 'Manage doctors and patients',
    'author': 'Tejash Ardeshna',
    'license': 'LGPL-3',

    'depends': ['base'],

    'data': [

'security/ir.model.access.csv',

'views/patient_sequence.xml',

'views/patient_views.xml',
'views/patient_action.xml',

'views/doctor_views.xml',
'views/doctor_action.xml',

'views/appointment_views.xml',
'views/appointment_action.xml',   # 👈 આ add કરવું

'views/menu.xml',

],

    'installable': True,
    'application': True,
}