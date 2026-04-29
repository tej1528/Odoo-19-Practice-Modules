from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import UserError

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
    # =====================zz
    @api.onchange('is_patient', 'is_doctor')
    def _onchange_preview_code(self):
        pass
    
    # =====================
    # CREATE (FINAL SAVE)
    # =====================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:

            # currency fix
            if not vals.get('currency_id'):
                vals['currency_id'] = self.env.company.currency_id.id

            # =====================
            # PATIENT CODE
            # =====================
            if vals.get('is_patient') or self.env.context.get('default_is_patient'):
                if not vals.get('code') or vals.get('code') == 'New':
                    seq = self.env['ir.sequence'].next_by_code('hospital.patient')
                    if not seq:
                        raise UserError("Patient sequence not configured.")
                    vals['code'] = seq

            # =====================
            # DOCTOR CODE
            # =====================
            if vals.get('is_doctor') or self.env.context.get('default_is_doctor'):
                if not vals.get('doctor_code') or vals.get('doctor_code') == 'New':
                    seq = self.env['ir.sequence'].next_by_code('hospital.doctor')
                    if not seq:
                        raise UserError("Doctor sequence not configured.")
                    vals['doctor_code'] = seq

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
    
    def action_create_doctor_user(self):
        for rec in self:

            if not rec.is_doctor:
                raise UserError("This is not a doctor.")

            if rec.user_id:
                raise UserError("User already exists.")

            if not rec.email:
                raise UserError("Doctor must have an email.")

            # ✅ create user
            user = self.env['res.users'].create({
                'name': rec.name,
                'login': rec.email,
                'email': rec.email,
                'partner_id': rec.id,
            })

            # 🔗 link doctor → user
            rec.user_id = user.id

            # 📧 send invitation mail
            user.with_context(create_user=True).action_reset_password()

        # ✅ popup message
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Doctor user created successfully & invitation sent!'),
                'type': 'success',
                'sticky': False,
            }
        }