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
        string="Status",
        domain="[('field_id.model', '=', 'hospital.appointment'), ('field_id.name', '=', 'status')]"
    )

    group_by_ids = fields.Many2many(
        'ir.model.fields',
        string="Group By",
        domain="""
            [
                ('model', '=', 'hospital.appointment'),
                ('name', 'in', ['patient_id', 'doctor_id', 'status'])
            ]
        """
    )

    def _get_report_domain(self):
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
            values = self.status_ids.mapped('value')
            if values:
                domain.append(('status', 'in', values))
        return domain

    def action_show_data(self):
        selected_statuses = self.status_ids.ids

        context = {
            'selected_statuses': selected_statuses,
        }

        if self.group_by_ids:
            context['group_by'] = self.group_by_ids.mapped('name')

        return {
            'type': 'ir.actions.act_window',
            'name': 'Filtered Appointments',
            'res_model': 'hospital.appointment',
            'view_mode': 'list,form',
            'domain': self._get_report_domain(),
            'target': 'current',
            'context': context,
        }

    def _get_total(self, records):
        return sum(records.mapped('fees'))

    def _group_data(self, records):

        group_fields = self.group_by_ids.mapped('name')

        if not group_fields:
            group_fields = ['doctor_id']  # default

        grouped = {}

        for rec in records:

            current = grouped

            for i, field in enumerate(group_fields):

                if field == 'doctor_id':
                    key = rec.doctor_id.name or "Undefined Doctor"

                elif field == 'patient_id':
                    key = rec.patient_id.name or "Undefined Patient"

                elif field == 'status':
                    key = dict(
                        self.env['hospital.appointment']._fields['status'].selection
                    ).get(rec.status, rec.status)

                else:
                    key = "Undefined"

                if i == len(group_fields) - 1:
                    current.setdefault(key, [])
                    current[key].append(rec.id)
                else:
                    current.setdefault(key, {})
                    current = current[key]

        return grouped


    def action_print_pdf(self):
        self.ensure_one()

        domain = self._get_report_domain()
        appointments = self.env['hospital.appointment'].search(domain)

        if not appointments:
            raise UserError("No data found")

        grouped_data = self._group_data(appointments)

        return self.env.ref(
            'hospital_management.action_appointment_report_pdf'
        ).with_context(
            from_date=self.start_date,
            to_date=self.end_date,
            grouped_data=grouped_data,
            group_by_labels=self.group_by_ids.mapped('name'),
        ).report_action(appointments)