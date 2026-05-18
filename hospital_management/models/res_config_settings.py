from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    appointment_duration = fields.Integer(
        string="Duration (Minutes)",
        config_parameter='hospital.appointment_duration',
        default=30
    )
        
    otp_expiry = fields.Integer(
        string="OTP Expiry (Minutes)",
        config_parameter='hospital.otp_expiry',
        default=2
    )

    @api.constrains('appointment_duration')
    def _check_appointment_duration(self):
        for rec in self:
            if not (1 <= rec.appointment_duration <= 60):
                raise ValidationError("Duration must be 1 to 60 minute")

    @api.constrains('otp_expiry')
    def _check_otp_expiry(self):
        for rec in self:
            if not (1 <= rec.otp_expiry <= 10):
                raise ValidationError("OTP expiry must be between 1 to 10 minutes")