from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    appointment_duration = fields.Integer(
        string="Appointment Duration (Minutes)",
        config_parameter='hospital.appointment_duration',
        default=30
    )