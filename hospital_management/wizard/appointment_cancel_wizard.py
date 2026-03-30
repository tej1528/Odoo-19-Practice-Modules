from odoo import models, fields


class AppointmentCancelWizard(models.TransientModel):
    _name = 'appointment.cancel.wizard'
    _description = 'Cancel Appointment Wizard'

    appointment_id = fields.Many2one('hospital.appointment', required=True)
    reason = fields.Text(string="Reason", required=True)

    def action_confirm_cancel(self):

        appointment = self.appointment_id

        if not appointment:
            return

        # ================= UPDATE =================
        appointment.write({
            'status': 'cancel',
            'cancel_reason': self.reason
        })

        # ================= EMAIL =================
        if appointment.patient_id.email:
            appointment._send_email(
                'hospital_management.email_template_cancel',
                appointment.patient_id.email   # ✅ IMPORTANT FIX
            )

        # ================= CHATTER =================
        appointment.message_post(
            body=f"Appointment Cancelled<br/><b>Reason:</b> {self.reason}",
            message_type='comment',
            subtype_xmlid="mail.mt_note"
        )

        return {'type': 'ir.actions.act_window_close'}