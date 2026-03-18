from odoo import models, fields, api


class HospitalDoctor(models.Model):
    _inherit = 'res.partner'

    # Doctor flag
    is_doctor = fields.Boolean(string="Is Doctor")

    # Doctor Code
    doctor_code = fields.Char(
        string="Doctor Code",
        readonly=True,
        copy=False,
        default='New'
    )

    # Doctor Details
    specialization = fields.Char(string="Specialization")

    fees = fields.Float(string="Consultation Fees")

    # Appointment Smart Button Counter
    appointment_count = fields.Integer(
        string="Appointments",
        compute="_compute_appointment_count"
    )

    # AUTO DOCTOR CODE
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('doctor_code', 'New') == 'New':
                vals['doctor_code'] = self.env['ir.sequence'].next_by_code('doctor.code') or 'New'
        return super().create(vals_list)

    # COMPUTE APPOINTMENT COUNT
    def _compute_appointment_count(self):
        for rec in self:
            rec.appointment_count = self.env['hospital.appointment'].search_count([
                ('doctor_id', '=', rec.id)
            ])

    # SMART BUTTON ACTION
    def action_doctor_appointments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Appointments',
            'res_model': 'hospital.appointment',
            'view_mode': 'list,form',
            'domain': [('doctor_id', '=', self.id)],
            'context': {'default_doctor_id': self.id},
        }