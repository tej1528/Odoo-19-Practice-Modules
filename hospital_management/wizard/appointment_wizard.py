from odoo import models, fields, api

class AppointmentWizard(models.TransientModel):
    _name = 'appointment.wizard'
    _description = 'Appointment Wizard'

    patient_id = fields.Many2one('res.partner')
    doctor_id = fields.Many2one('res.partner')
    start_time = fields.Datetime()
    end_time = fields.Datetime()

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res['start_time'] = self.env.context.get('default_start_time')
        res['end_time'] = self.env.context.get('default_end_time')
        return res

    def action_create_appointment(self):
        self.env['hospital.appointment'].create({
            'patient_id': self.patient_id.id,
            'doctor_id': self.doctor_id.id,
            'start_time': self.start_time,
            'end_time': self.end_time,
        })