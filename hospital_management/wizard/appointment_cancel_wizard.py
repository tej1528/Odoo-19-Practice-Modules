from odoo import models, fields

class AppointmentCancelWizard(models.TransientModel):
    _name = 'appointment.cancel.wizard'
    _description = 'Cancel Appointment Wizard'

    appointment_id = fields.Many2one('hospital.appointment')
    reason = fields.Text(string="Reason", required=True)

    def action_confirm_cancel(self):
        self.appointment_id.status = 'cancel'
        self.appointment_id.cancel_reason = self.reason