from odoo import models, fields, api


class HospitalSpecialization(models.Model):
    _name = 'hospital.specialization'
    _description = 'Doctor Specialization'

    name = fields.Char(string="Specialization", required=True)

    # =====================
    # RELATION
    # =====================
    doctor_ids = fields.One2many(
        'res.partner',
        'specialization_id',
        string="Doctors"
    )

    # =====================
    # COUNTS
    # =====================
    doctor_count = fields.Integer(
        string="Doctor Count",
        compute="_compute_counts"
    )

    patient_count = fields.Integer(
        string="Patients",
        compute="_compute_counts"
    )

    # =====================
    # COMPUTE COUNTS
    # =====================
    def _compute_counts(self):
        for rec in self:
            rec.doctor_count = len(
                rec.doctor_ids.filtered(lambda d: d.is_doctor)
            )

            rec.patient_count = self.env['hospital.appointment'].search_count([
                ('doctor_id.specialization_id', '=', rec.id)
            ])

    # =====================
    # SMART BUTTON ACTIONS
    # =====================
    def action_view_doctors(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Doctors',
            'res_model': 'res.partner',
            'view_mode': 'list,form',
            'domain': [
                ('is_doctor', '=', True),
                ('specialization_id', '=', self.id)
            ],
            'context': dict(
                self.env.context,
                default_specialization_id=self.id,
                no_breadcrumbs=True,   
                no_control_panel=True,
                create=False,          
                edit=False,            
                delete=False           
            )
        }

    def action_view_patients(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Patients',
            'res_model': 'hospital.appointment',
            'view_mode': 'list,form',
            'domain': [
                ('doctor_id.specialization_id', '=', self.id)
            ],
            'context': dict(
                self.env.context,
                no_breadcrumbs=True,
                no_control_panel=True,
                create=False,
                edit=False,
                delete=False
            )
        }