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
    # mobile = fields.Char(string="Mobile Number")

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

    # =====================
    # COMMON
    # =====================
    display_code = fields.Char(string="Code", compute="_compute_display_code", store=True)

    appointment_count = fields.Integer(compute="_compute_appointment_count")
    requested_appointment_count = fields.Integer(compute="_compute_requested_appointment_count")

    user_id = fields.Many2one('res.users', string="Related User")

    # =====================
    # SQL CONSTRAINT (NO DUPLICATE)
    # =====================
    # @api.constrains('code', 'doctor_code')
    # def _check_unique_codes(self):
    #     for rec in self:
    #         if rec.code:
    #             domain = [('code', '=', rec.code)]
    #             if rec.id:
    #                 domain.append(('id', '!=', rec.id))

    #             if self.search_count(domain) > 1:
    #                 raise ValidationError("Patient code must be unique!")

    #         if rec.doctor_code:
    #             domain = [('doctor_code', '=', rec.doctor_code)]
    #             if rec.id:
    #                 domain.append(('id', '!=', rec.id))

    #             if self.search_count(domain) > 1:
    #                 raise ValidationError("Doctor code must be unique!")

    # =====================
    # CREATE (MAIN LOGIC)
    # =====================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:

            # Default currency
            if not vals.get('currency_id'):
                vals['currency_id'] = self.env.company.currency_id.id

            # PATIENT CODE
            if vals.get('is_patient') or self.env.context.get('default_is_patient'):
                if vals.get('code', 'New') == 'New':
                    vals['code'] = self.env['ir.sequence'].sudo().next_by_code('hospital.patient')

            # DOCTOR CODE
            if vals.get('is_doctor') or self.env.context.get('default_is_doctor'):
                if vals.get('doctor_code', 'New') == 'New':
                    vals['doctor_code'] = self.env['ir.sequence'].sudo().next_by_code('hospital.doctor')

        return super().create(vals_list)

    # =====================
    # VALIDATION (ONLY ONE ROLE)
    # =====================
    @api.constrains('is_patient', 'is_doctor')
    def _check_only_one_role(self):
        for rec in self:
            if rec.is_patient and rec.is_doctor:
                raise UserError("A record cannot be both Patient and Doctor.")

    # =====================
    # DISPLAY CODE
    # =====================
    @api.depends('code', 'doctor_code', 'is_patient', 'is_doctor')
    def _compute_display_code(self):
        for rec in self:
            rec.display_code = rec.code if rec.is_patient else rec.doctor_code if rec.is_doctor else ''

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

    # =====================
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

    # =====================
    # REQUESTED APPOINTMENT
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

    # =====================
    # ACTIONS
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

    
    def action_create_user(self):
        for rec in self:

            if rec.user_id:
                raise UserError("User already exists.")

            if not rec.email:
                raise UserError("Email is required.")

            Users = self.env['res.users'].sudo()

            # 🔍 search
            user = Users.search([
                ('login', '=', rec.email)
            ], limit=1)

            # ➕ create with group
            if not user:

                if rec.is_patient:

                    user = Users.with_context(
                        no_reset_password=True
                    ).create({

                        'name': rec.name,
                        'login': rec.email,
                        'email': rec.email,
                        'partner_id': rec.id,

                        'group_ids': [(6, 0, [
                            self.env.ref(
                                'base.group_portal'
                            ).id
                        ])]

                    })

                elif rec.is_doctor:

                    user = Users.with_context(
                        no_reset_password=True
                    ).create({

                        'name': rec.name,
                        'login': rec.email,
                        'email': rec.email,
                        'partner_id': rec.id,

                        'group_ids': [(6, 0, [
                            self.env.ref(
                                'hospital_management.group_doctor'
                            ).id
                        ])]

                    })

            # 🔗 link
            rec.user_id = user.id

            # 🔐 send password mail
            user.with_context(create_user=True).action_reset_password()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'User created & email sent!',
                'type': 'success',
            }
        }