from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HospitalAppointment(models.Model):
    _name = 'hospital.appointment'
    _description = 'Hospital Appointment'

    code = fields.Char(
        string="Appointment Code",
        readonly=True,
        copy=False,
        default="New"
    )

    patient_id = fields.Many2one(
        'res.partner',
        string="Patient",
        domain=[('is_patient', '=', True)]
    )

    doctor_id = fields.Many2one(
        'res.partner',
        string="Doctor",
        domain=[('is_doctor', '=', True)]
    )

    appointment_date = fields.Date(
        string="Appointment Date",
        default=fields.Date.context_today
    )

    start_time = fields.Datetime(string="Start Time")
    end_time = fields.Datetime(string="End Time")

    fees = fields.Float(string="Doctor Fees")
    notes = fields.Text(string="Notes")

    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], default='draft')

    # Status Buttons
    def action_confirm(self):
        for rec in self:
            rec.status = 'confirmed'

    def action_done(self):
        for rec in self:
            rec.status = 'done'

    def action_cancel(self):
        for rec in self:
            rec.status = 'cancel'

    # Validation
    @api.constrains('start_time', 'end_time', 'appointment_date')
    def check_appointment_time(self):
        for rec in self:

            if rec.start_time and rec.end_time:

                if rec.end_time <= rec.start_time:
                    raise ValidationError(
                        "End Time must be greater than Start Time."
                    )

                if rec.appointment_date and rec.start_time.date() != rec.appointment_date:
                    raise ValidationError(
                        "Start Time must be on the same date as Appointment Date."
                    )

                if rec.appointment_date and rec.end_time.date() != rec.appointment_date:
                    raise ValidationError(
                        "End Time must be on the same date as Appointment Date."
                    )

    # Sequence
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', 'New') == 'New':
                vals['code'] = self.env['ir.sequence'].next_by_code('appointment.code') or 'New'
        return super().create(vals_list)

    # Doctor Fees Autofill
    @api.onchange('doctor_id')
    def _onchange_doctor(self):
        if self.doctor_id:
            self.fees = self.doctor_id.fees