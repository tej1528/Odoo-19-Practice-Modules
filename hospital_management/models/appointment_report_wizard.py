from odoo import models, fields, api
from datetime import datetime

class AppointmentReportWizard(models.TransientModel):
    _name = 'appointment.report.wizard'
    _description = 'Appointment Report Wizard'

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    patient_ids = fields.Many2many(
        'res.partner',
        'wizard_patient_rel',
        'wizard_id',
        'partner_id',
        string="Patients",
        domain=[('is_patient', '=', True)]
    )

    doctor_ids = fields.Many2many(
        'res.partner',
        'wizard_doctor_rel',
        'wizard_id',
        'partner_id',
        string="Doctors",
        domain=[('is_doctor', '=', True)]
    )

    specialization_ids = fields.Many2many('hospital.specialization', string="Specializations")

    status_ids = fields.Many2many(
    'ir.model.fields.selection',
    string="Statuses",
    domain="[('field_id.model', '=', 'hospital.appointment'), ('field_id.name', '=', 'status')]")
    
#     group_by = fields.Selection([
#     ('doctor_id', 'Doctor'),
#     ('patient_id', 'Patient'),
#     ('status', 'Status'),
# ], default='doctor_id', string="Group By")
    
#     group_by_ids = fields.Many2many(
#     'ir.model.fields',
#     string="Group By",
#     domain="[('model', '=', 'hospital.appointment'), ('ttype', 'in', ['many2one', 'selection'])]"
# )

    group_by_ids = fields.Many2many('ir.model.fields',
    string="Group By",
    domain="""
        [
            ('model', '=', 'hospital.appointment'),
            ('name', 'in', ['patient_id', 'doctor_id', 'status'])
        ]
    """
)

    def _get_report_domain(self):
        """ Helper method to build the filter domain without causing recursion """
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
            domain.append(('status', 'in', self.status_ids.mapped('value')))
        return domain

    def action_show_data(self):
        selected_statuses = self.status_ids.ids

        context = {
            'selected_statuses': selected_statuses,
        }
        if self.group_by_ids:
            group_fields = self.group_by_ids.mapped('name')  
            context['group_by'] = group_fields

        return {
            'type': 'ir.actions.act_window',
            'name': 'Filtered Appointments',
            'res_model': 'hospital.appointment',
            'view_mode': 'list,form',
            'domain': self._get_report_domain(),
            'target': 'current',
            'context': context,
        }

        

    def action_print_pdf(self):
        self.ensure_one()
        
        # FIXED: Call the helper method, NOT action_print_pdf itself
        domain = self._get_report_domain()
        appointments = self.env['hospital.appointment'].search(domain)

        return self.env.ref('hospital_management.action_appointment_report_pdf').with_context(
            generated_on=fields.Datetime.now(),
            from_date=self.start_date,
            to_date=self.end_date,
        ).report_action(appointments)