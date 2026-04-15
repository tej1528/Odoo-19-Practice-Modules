from odoo import models, fields

class AppointmentReportWizard(models.TransientModel):
    _name = 'appointment.report.wizard'
    _description = 'Appointment Report Wizard'

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    currency_id = fields.Many2one(
    'res.currency',
    string="Currency",
    default=lambda self: self.env.company.currency_id)
    
    patient_ids = fields.Many2many(
    'res.partner',
    'wizard_patient_rel',   
    'wizard_id',
    'partner_id',
    string="Patients",
    domain=[('is_patient', '=', True)])

    doctor_ids = fields.Many2many(
    'res.partner',
    'wizard_doctor_rel',  
    'wizard_id',
    'partner_id',
    string="Doctors",
    domain=[('is_doctor', '=', True)])

    specialization_ids = fields.Many2many('hospital.specialization', string="Specializations")
    
    status_ids = fields.Many2many(
    'hospital.appointment.status',
    'wizard_status_rel',
    'wizard_id',
    'status_id',
    string="Status")
    
    def action_show_data(self):
        domain = []

        if self.patient_ids:
            domain.append(('patient_id', 'in', self.patient_ids.ids))

        if self.doctor_ids:
            domain.append(('doctor_id', 'in', self.doctor_ids.ids))

        if self.specialization_ids:
            domain.append(('specialization_id', 'in', self.specialization_ids.ids))

        if self.start_date:
            domain.append(('start_time', '>=', self.start_date))

        if self.end_date:
            domain.append(('end_time', '<=', self.end_date))
        
        if self.status_ids:
            domain.append(('status', 'in', self.status_ids.mapped('code')))

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

        if self.patient_ids:
            domain.append(('patient_id', 'in', self.patient_ids.ids))

        if self.doctor_ids:
            domain.append(('doctor_id', 'in', self.doctor_ids.ids))

        if self.specialization_ids:
            domain.append(('specialization_id', 'in', self.specialization_ids.ids))

        if self.start_date:
            domain.append(('start_time', '>=', self.start_date))

        if self.end_date:
            domain.append(('end_time', '<=', self.end_date))

        if self.status_ids:
            domain.append(('status', 'in', self.status_ids.mapped('code')))

        appointments = self.env['hospital.appointment'].search(domain)

        return self.env.ref('hospital_management.action_appointment_report_pdf').report_action(appointments)