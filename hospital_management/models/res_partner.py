from odoo import models, fields, api
from datetime import date

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # =====================
    # FLAGS
    # =====================
    is_patient = fields.Boolean(string="Is Patient")
    is_doctor = fields.Boolean(string="Is Doctor")

    # =====================
    # PATIENT
    # =====================
    code = fields.Char(string="Patient Code", readonly=True, copy=False, default='New')

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ])

    date_of_birth = fields.Date()
    age = fields.Integer(compute="_compute_age", store=True)

    blood_group = fields.Selection([
        ('a+', 'A+'), ('a-', 'A-'),
        ('b+', 'B+'), ('b-', 'B-'),
        ('ab+', 'AB+'), ('ab-', 'AB-'),
        ('o+', 'O+'), ('o-', 'O-')
    ])

    # =====================
    # DOCTOR
    # =====================
    doctor_code = fields.Char(string="Doctor Code", readonly=True, copy=False, default='New')

    specialization_id = fields.Many2one('hospital.specialization', string="Specialization")
    
    
    fees = fields.Monetary(
    string="Consultation Fees",
    currency_field='currency_id'
)

    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    #  COMBINED CODE FIELD
    # =====================
    display_code = fields.Char(string="Code", compute="_compute_display_code", store=True)

    # =====================
    # COMMON
    # =====================
    appointment_count = fields.Integer(compute="_compute_appointment_count")

    # =====================
    # COMPUTE DISPLAY CODE
    # =====================
    @api.depends('code', 'doctor_code', 'is_patient', 'is_doctor')
    def _compute_display_code(self):
        for rec in self:
            if rec.is_patient:
                rec.display_code = rec.code
            elif rec.is_doctor:
                rec.display_code = rec.doctor_code
            else:
                rec.display_code = ''

    # =====================
    # AUTO PREVIEW (ONCHANGE )
    # =====================
    @api.onchange('is_patient', 'is_doctor')
    def _onchange_preview_code(self):
        if self.is_patient and self.code == 'New':
            self.code = self.env['ir.sequence'].next_by_code('hospital.patient') or 'PT000'

        if self.is_doctor and self.doctor_code == 'New':
            self.doctor_code = self.env['ir.sequence'].next_by_code('hospital.doctor') or 'DR000'

    # =====================
    # CREATE (FINAL SAVE)
    # =====================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:

            # 🔥 currency fix
            if not vals.get('currency_id'):
                vals['currency_id'] = self.env.company.currency_id.id

            # Patient
            if vals.get('is_patient') or self.env.context.get('default_is_patient'):
                if vals.get('code', 'New') == 'New':
                    vals['code'] = self.env['ir.sequence'].next_by_code('hospital.patient') or 'PT000'

            # Doctor
            if vals.get('is_doctor') or self.env.context.get('default_is_doctor'):
                if vals.get('doctor_code', 'New') == 'New':
                    vals['doctor_code'] = self.env['ir.sequence'].next_by_code('hospital.doctor') or 'DR000'

                # 🔥 ADD THIS LINE
                if not vals.get('user_id'):
                    vals['user_id'] = self.env.uid

        return super().create(vals_list)

    # =====================
    # AGE COMPUTE
    # =====================
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
    # =====================
    def _compute_appointment_count(self):
        for rec in self:
            if rec.is_patient:
                rec.appointment_count = self.env['hospital.appointment'].search_count([
                    ('patient_id', '=', rec.id)
                ])
            elif rec.is_doctor:
                rec.appointment_count = self.env['hospital.appointment'].search_count([
                    ('doctor_id', '=', rec.id)
                ])
            else:
                rec.appointment_count = 0


    requested_appointment_count = fields.Integer(
    compute="_compute_requested_appointment_count")

    user_id = fields.Many2one('res.users', string="Related User")
    
    # Doctor Request Button
    # =====================
    def _compute_requested_appointment_count(self):
        for rec in self:
            if rec.is_doctor:
                rec.requested_appointment_count = self.env['hospital.appointment'].search_count([
                    ('doctor_id', '=', rec.id),
                    ('status', '=', 'requested')
                ])
            else:
                rec.requested_appointment_count = 0

    def action_view_requested_appointments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Requested Appointments',
            'res_model': 'hospital.appointment',
            'view_mode': 'list,form',
            'domain': [
                ('doctor_id', '=', self.id),
                ('status', '=', 'requested')
            ],
            'context': {'default_doctor_id': self.id}
        }

    # SMART BUTTON ACTION
    # =====================
    def action_view_appointments(self):
        self.ensure_one()

        if self.is_patient:
            domain = [('patient_id', '=', self.id)]
            context = {'default_patient_id': self.id}
        else:
            domain = [('doctor_id', '=', self.id)]
            context = {'default_doctor_id': self.id}

        return {
            'type': 'ir.actions.act_window',
            'name': 'Appointments',
            'res_model': 'hospital.appointment',
            'view_mode': 'list,form',
            'domain': domain,
            'context': context,
        }