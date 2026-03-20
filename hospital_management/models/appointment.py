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
        required=True
    )

    # =========================
    # AUTO FIELDS FROM DOCTOR
    # =========================
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

    # =========================
    # DATE & TIME
    # =========================
    start_time = fields.Datetime(string="Start Time")
    end_time = fields.Datetime(string="End Time")

 
    #  DOUBLE BOOKING BLOCK (DATETIME BASED)
    # =========================
    @api.constrains('patient_id', 'doctor_id', 'start_time', 'end_time')
    def _check_time_overlap(self):
        for rec in self:

            if not rec.start_time or not rec.end_time:
                continue

            #  Doctor overlap check
            doctor_conflict = self.search([
                ('id', '!=', rec.id),
                ('doctor_id', '=', rec.doctor_id.id),
                ('start_time', '<', rec.end_time),
                ('end_time', '>', rec.start_time),
            ])

            if doctor_conflict:
                raise ValidationError(" Doctor already has an appointment in this time slot!")

            #  Patient overlap check
            patient_conflict = self.search([
                ('id', '!=', rec.id),
                ('patient_id', '=', rec.patient_id.id),
                ('start_time', '<', rec.end_time),
                ('end_time', '>', rec.start_time),
            ])

            if patient_conflict:
                raise ValidationError(" Patient already has an appointment in this time slot!")

    # =========================
    # STATUS
    # =========================
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], default='draft')

    # =========================
    # ONCHANGE (MAIN LOGIC 🔥)
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
    # VALIDATION
    # =========================
    @api.constrains('start_time', 'end_time')
    def check_appointment_time(self):
        for rec in self:

            if rec.start_time and rec.end_time:

                if rec.end_time <= rec.start_time:
                    raise ValidationError("End Time must be greater than Start Time.")

    # =========================
    # SEQUENCE
    # =========================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', 'New') == 'New':
                vals['code'] = self.env['ir.sequence'].next_by_code('appointment.code') or 'New'
        return super().create(vals_list)

    # =========================
    # STATUS BUTTONS
    # =========================
    def action_confirm(self):
        self.status = 'confirmed'

    def action_done(self):
        self.status = 'done'

    def action_cancel(self):
        self.status = 'cancel'