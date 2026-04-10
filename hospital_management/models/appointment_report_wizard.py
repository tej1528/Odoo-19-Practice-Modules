from odoo import models, fields
from datetime import datetime, time

class AppointmentReportWizard(models.TransientModel):
    _name = 'appointment.report.wizard'
    _description = 'Appointment Report Wizard'

    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)

    def action_generate_report(self):
        self.ensure_one()

        # Convert date → full datetime range (IMPORTANT 🔥)
        start = datetime.combine(self.start_date, time.min)
        end = datetime.combine(self.end_date, time.max)

        domain = [
            ('start_time', '>=', start),
            ('start_time', '<=', end)
        ]

        return {
            'type': 'ir.actions.act_window',
            'name': 'Filtered Appointments',
            'res_model': 'hospital.appointment',
            'view_mode': 'tree,form',
            'domain': domain,
        }