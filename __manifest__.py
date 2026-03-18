{
    'name': 'Hospital Management system',
    'version': '1.0',
    'category': 'Healthcare',
    'summary': 'Manage doctors and patients',
    'author': 'Tejash Ardeshna',
    'license': 'LGPL-3',

    'depends': ['base'],

    'data': [

<<<<<<< HEAD
    'security/ir.model.access.csv',

    'Data/sequence.xml',

    'views/res_partner_views.xml',
    'views/appointment_views.xml',
    'views/appointment_action.xml',
    'views/specialization_views.xml',
    'views/menu.xml',
=======
'security/ir.model.access.csv',

'views/patient_sequence.xml',

'views/patient_views.xml',
'views/patient_action.xml',

'views/doctor_views.xml',
'views/doctor_action.xml',

'views/appointment_views.xml',
'views/appointment_action.xml',   # 👈 આ add કરવું

'views/menu.xml',

>>>>>>> a696a75f8807b8629a81fc61083237e383570b85
],

    'installable': True,
    'application': True,
}