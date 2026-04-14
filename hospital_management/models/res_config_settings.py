from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    appointment_duration = fields.Integer(
        string="Duration (Minutes)",
        config_parameter='hospital.appointment_duration',
        default=30
    )

    @api.constrains('appointment_duration')
    def _check_appointment_duration(self):
        for rec in self:
            if not (1 <= rec.appointment_duration <= 60):
                raise ValidationError("Duration must be 1 to 60 minute")