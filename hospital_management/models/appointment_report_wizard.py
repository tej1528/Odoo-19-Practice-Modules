from odoo import models, fields

class AppointmentReportWizard(models.TransientModel):
    _name = 'appointment.report.wizard'
    _description = 'Appointment Report Wizard'

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    patient_id = fields.Many2one('res.partner', string="Patient", domain=[('is_patient', '=', True)])
    doctor_ids = fields.Many2many('res.partner', string="Doctors", domain=[('is_doctor', '=', True)]
)
    specialization_ids = fields.Many2many('hospital.specialization', string="Specializations")

    def action_show_data(self):
        domain = []

        if self.patient_id:
            domain.append(('patient_id', '=', self.patient_id.id))

        if self.doctor_ids:
            domain.append(('doctor_id', 'in', self.doctor_ids.ids))

        if self.specialization_ids:
            domain.append(('specialization_id', 'in', self.specialization_ids.ids))

        if self.start_date:
            domain.append(('start_time', '>=', self.start_date))

        if self.end_date:
            domain.append(('end_time', '<=', self.end_date))

        return {
            'type': 'ir.actions.act_window',
            'name': 'Filtered Appointments',
            'res_model': 'hospital.appointment',
            'view_mode': 'list,form',
            'domain': domain,
            'target': 'current',
        }

    def action_print_pdf(self):
        self.ensure_one()

        domain = []

        if self.patient_id:
            domain.append(('patient_id', '=', self.patient_id.id))

        if self.doctor_ids:
            domain.append(('doctor_id', 'in', self.doctor_ids.ids))

        if self.specialization_ids:
            domain.append(('specialization_id', 'in', self.specialization_ids.ids))

        if self.start_date:
            domain.append(('start_time', '>=', self.start_date))

        if self.end_date:
            domain.append(('end_time', '<=', self.end_date))

        appointments = self.env['hospital.appointment'].search(domain)

        return self.env.ref('hospital_management.action_appointment_report_pdf').report_action(appointments)