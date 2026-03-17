from odoo import models, fields, api
from datetime import date

class HospitalPatient(models.Model):
    _inherit = 'res.partner'

    is_patient = fields.Boolean(string="Is Patient")

    code = fields.Char(
    string="Patient Code",
    readonly=True,
    copy=False,
    default='New'
)

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string="Gender")

    date_of_birth = fields.Date(string="Date of Birth")

    age = fields.Integer(
        string="Age",
        compute="_compute_age",
        store=True
    )

    blood_group = fields.Selection([
        ('a+', 'A+'),
        ('a-', 'A-'),
        ('b+', 'B+'),
        ('b-', 'B-'),
        ('ab+', 'AB+'),
        ('ab-', 'AB-'),
        ('o+', 'O+'),
        ('o-', 'O-')
    ], string="Blood Group")

    appointment_count = fields.Integer(
        string="Appointments",
        compute="_compute_appointment_count"
    )

    # AUTO PATIENT CODE
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', 'New') == 'New':
                vals['code'] = self.env['ir.sequence'].next_by_code('hospital.patient') or 'New'
        return super(HospitalPatient, self).create(vals_list)

    # AGE COMPUTE
    @api.depends('date_of_birth')
    def _compute_age(self):
        for rec in self:
            if rec.date_of_birth:
                today = date.today()
                rec.age = today.year - rec.date_of_birth.year - (
                    (today.month, today.day) < (rec.date_of_birth.month, rec.date_of_birth.day)
                )
            else:
                rec.age = 0

    # APPOINTMENT COUNT
    def _compute_appointment_count(self):
        for rec in self:
            rec.appointment_count = self.env['hospital.appointment'].search_count([
                ('patient_id', '=', rec.id)
            ])

    # SMART BUTTON ACTION
    def action_patient_appointments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Appointments',
            'view_mode': 'list,form',
            'res_model': 'hospital.appointment',
            'domain': [('patient_id', '=', self.id)],
        }