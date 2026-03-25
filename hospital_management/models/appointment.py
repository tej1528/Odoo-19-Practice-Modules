from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HospitalAppointment(models.Model):
    _name = 'hospital.appointment'
    _description = 'Hospital Appointment'
   
    _rec_name = 'code'

    # =========================
    # BASIC
    # =========================
    code = fields.Char(
        string="Appointment Code",
        readonly=True,
        copy=False,
        default="New"
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
        # required=True,
        # ondelete='cascade'
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

    notes = fields.Text(string="")
    cancel_reason = fields.Text(string="Cancel Reason")

    start_time = fields.Datetime(string="Start Time")
    end_time = fields.Datetime(string="End Time")

    is_doctor_user = fields.Boolean(compute="_compute_is_doctor_user")
    @api.depends('doctor_id')
    def _compute_is_doctor_user(self):
        for rec in self:
            rec.is_doctor_user = (
                rec.doctor_id.user_id.id == self.env.uid
            ) if rec.doctor_id and rec.doctor_id.user_id else False

    # =========================
    # STATUS
    # =========================
    status = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], default='draft', tracking=True)

    # =========================
    # BUTTON ACTIONS
    # =========================
    def action_requested(self):
        for rec in self:
            rec.status = 'requested'

    def action_confirm(self):
        for rec in self:
            rec.status = 'confirmed'

            template = self.env.ref(
                'hospital_management.email_template_confirm',
                raise_if_not_found=False
            )

            if template:
                template.send_mail(rec.id, force_send=True)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Appointment confirmed & email sent!',
                'type': 'success',
            }
        }

    def action_done(self):
        for rec in self:
            rec.status = 'done'

    def action_cancel(self):
        for rec in self:
            rec.status = 'cancel'

            template = self.env.ref(
                'hospital_management.email_template_cancel',
                raise_if_not_found=False
            )

            if template:
                template.send_mail(rec.id, force_send=True)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Cancelled',
                'message': 'Appointment cancelled & email sent!',
                'type': 'warning',
            }
        }

    # =========================
    # AUTO DOCTOR SELECT 🔥
    # =========================
    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)

        doctor = self.env['res.partner'].search([
            ('user_id', '=', self.env.uid),
            ('is_doctor', '=', True)
        ], limit=1)

        if doctor:
            res['doctor_id'] = doctor.id

        return res

    # =========================
    # ONCHANGE
    # =========================
    @api.onchange('doctor_id')
    def _onchange_doctor(self):
        for rec in self:
            if rec.doctor_id:
                rec.fees = rec.doctor_id.fees
                rec.specialization_id = rec.doctor_id.specialization_id
            else:
                rec.fees = 0.0
                rec.specialization_id = False

    # =========================
    # VALIDATIONS
    # =========================
    @api.constrains('start_time', 'end_time')
    def check_appointment_time(self):
        for rec in self:
            if rec.start_time and rec.end_time:
                if rec.end_time <= rec.start_time:
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

    # =========================
    # SEQUENCE
    # =========================
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for rec in records:
            # sequence logic already applied above
            if rec.code == 'New':
                rec.code = self.env['ir.sequence'].next_by_code('appointment.code') or 'New'

            # EMAIL SEND 🔥
            template = self.env.ref(
                'hospital_management.email_template_appointment',
                raise_if_not_found=False
            )

            # if template and rec.status == 'requested':
            #     template.send_mail(rec.id, force_send=True)

        return records