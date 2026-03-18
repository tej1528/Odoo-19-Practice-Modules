from odoo import models, fields, api


class HospitalSpecialization(models.Model):
    _name = 'hospital.specialization'
    _description = 'Doctor Specialization'

    name = fields.Char(string="Specialization", required=True)

    # Relation with partner (doctor)
    doctor_ids = fields.One2many('res.partner', 'specialization_id', string="Doctors")

    # Counts
    doctor_count = fields.Integer(string="Doctors", compute="_compute_counts")
    patient_count = fields.Integer(string="Patients", compute="_compute_counts")

    # =====================
    # COUNT LOGIC
    # =====================
    def _compute_counts(self):
        for rec in self:
            doctors = rec.doctor_ids.filtered(lambda d: d.is_doctor)
            rec.doctor_count = len(doctors)

            rec.patient_count = self.env['hospital.appointment'].search_count([
                ('doctor_id.specialization_id', '=', rec.id)
            ])