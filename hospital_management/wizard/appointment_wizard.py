from odoo import models, fields, api

class AppointmentWizard(models.TransientModel):
    _name = 'appointment.wizard'
    _description = 'Appointment Wizard'

    patient_id = fields.Many2one('res.partner', string="Patient", required=True)
    doctor_id = fields.Many2one('res.partner', string="Doctor", required=True)
    start_time = fields.Datetime(string="Start Time", required=True)
    end_time = fields.Datetime(string="End Time", required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        start = self.env.context.get('default_start_time')
        end = self.env.context.get('default_end_time')

        if start:
            res['start_time'] = start
        if end:
            res['end_time'] = end

        return res

    def action_create_appointment(self):
        appointment = self.env['hospital.appointment'].create({
            'patient_id': self.patient_id.id,
            'doctor_id': self.doctor_id.id,
            'start_time': self.start_time,
            'end_time': self.end_time,
        })

        return {
            'type': 'ir.actions.act_window_close'  
        }