from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64

class HospitalAppointment(models.Model):
    _name = 'hospital.appointment'
    _description = 'Hospital Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']  
    _rec_name = 'code'

    # BASIC
    code = fields.Char(
        string="Appointment Code",
        readonly=True,
        copy=False,
        default="New"
    )

    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True
    )
    
    patient_id = fields.Many2one(
        'res.partner',
        string="Patient",
        domain=[('is_patient', '=', True)],
        required=True
    )

    doctor_id = fields.Many2one(
        'res.partner',
        string="Doctor",
        domain=[('is_doctor', '=', True)],
        ondelete='set null'
    )

    specialization_id = fields.Many2one(
        'hospital.specialization',
        string="Specialization"
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='doctor_id.currency_id',
        store=True,
        readonly=True
    )

    fees = fields.Monetary(
        string="Doctor Fees",
        currency_field='currency_id'
    )

    notes = fields.Text()
    cancel_reason = fields.Text(string="Cancel Reason")

    start_time = fields.Datetime()
    end_time = fields.Datetime()

    is_doctor_user = fields.Boolean(compute="_compute_is_doctor_user")

    doctor_description = fields.Text(string="Doctor Description")
    
    @api.depends('doctor_id')
    def _compute_is_doctor_user(self):
        for rec in self:
            rec.is_doctor_user = (
                rec.doctor_id.user_id.id == self.env.uid
            ) if rec.doctor_id and rec.doctor_id.user_id else False

    # STATUS
    status = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], default='draft', tracking=True)


    # COMMON EMAIL FUNCTION
    def _send_email(self, template_xmlid, email_to=None):
        template = self.env.ref(template_xmlid, raise_if_not_found=False)

        if not template:
            return

        for rec in self:
            email_values = {}

            if email_to:
                email_values = {
                    'email_to': email_to,
                    'recipient_ids': [],
                }

            pdf = self.env['ir.actions.report']._render_qweb_pdf(
                'hospital_management.report_appointment_pdf',
                [rec.id]
            )[0]

            
            attachment = self.env['ir.attachment'].create({
                'name': f'Appointment-{rec.code}.pdf',
                'type': 'binary',
                'datas': base64.b64encode(pdf),
                'res_model': self._name,
                'res_id': rec.id,
                'mimetype': 'application/pdf',
            })

            email_values.update({
                'attachment_ids': [attachment.id]
            })

            template.send_mail(
                rec.id,
                force_send=True,
                email_values=email_values
            )

    # BUTTON ACTIONS
    def action_requested(self):
        for rec in self:

            if not rec.doctor_id.email:
                raise ValidationError("Doctor email missing!")

            rec.status = 'requested'

            rec.message_post(
            body=f" Appointment requested & mail send successfully"
            )

            # doctor ne mail
            rec._send_email(
                'hospital_management.email_template_appointment_requested',
                rec.doctor_id.email
            )
        return True
    
    def action_confirm(self):
        for rec in self:

            if not rec.patient_id.email:
                raise ValidationError("Patient email missing!")

            rec.status = 'confirmed'

            template = self.env.ref('hospital_management.email_template_confirm')
            
            rec.message_post(
            body=f" Appointment Confirmed & mail send successfully"
            )

            # patient ne mail
            rec._send_email(
                'hospital_management.email_template_confirm',
                rec.patient_id.email
            )

        return True
    
    def action_processing(self):
        for rec in self:
            rec.status = 'processing'

    def action_done(self):
        self.write({'status': 'done'})
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_cancel(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Cancel Appointment',
            'res_model': 'appointment.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_appointment_id': self.id}
        }

    def action_reset_to_draft(self):
        for rec in self:
            rec.status = 'draft'

    def action_cancel_confirm(self):
        for rec in self:

            rec.status = 'cancel'

            if rec.patient_id.email:
                rec._send_email(
                    'hospital_management.email_template_cancel',
                    rec.patient_id.email
                )
        return True

    # ================= SEQUENCE =================
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.code == 'New':
                rec.code = self.env['ir.sequence'].next_by_code('appointment.code') or 'New'
        return records

    # ONCHANGE
    @api.onchange('doctor_id')
    def _onchange_doctor(self):
        for rec in self:
            if rec.doctor_id:
                rec.fees = rec.doctor_id.fees
                rec.specialization_id = rec.doctor_id.specialization_id
            else:
                rec.fees = 0.0
                rec.specialization_id = False

    # VALIDATIONS
    @api.constrains('start_time', 'end_time')
    def check_appointment_time(self):
        for rec in self:
            if rec.start_time and rec.end_time and rec.end_time <= rec.start_time:
                raise ValidationError("End Time must be greater than Start Time.")

    @api.constrains('patient_id', 'doctor_id', 'start_time', 'end_time')
    def _check_time_overlap(self):
        for rec in self:
            if not rec.start_time or not rec.end_time:
                continue

            doctor_conflict = self.search([
                ('id', '!=', rec.id),
                ('doctor_id', '=', rec.doctor_id.id),
                ('start_time', '<', rec.end_time),
                ('end_time', '>', rec.start_time),
            ])

            if doctor_conflict:
                raise ValidationError("Doctor already has an appointment in this time slot!")

            patient_conflict = self.search([
                ('id', '!=', rec.id),
                ('patient_id', '=', rec.patient_id.id),
                ('start_time', '<', rec.end_time),
                ('end_time', '>', rec.start_time),
            ])

            if patient_conflict:
                raise ValidationError("Patient already has an appointment in this time slot!")

