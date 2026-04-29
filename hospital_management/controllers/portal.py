from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class HospitalPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)

        appointment_count = request.env['hospital.appointment'].search_count([])
        values['appointment_count'] = appointment_count

        return values

    @http.route(['/my/appointments'], type='http', auth="user", website=True)
    def portal_my_appointments(self, **kw):

        appointments = request.env['hospital.appointment'].search([])

        return request.render(
            "hospital_management.portal_my_appointments",
            {
                'appointments': appointments,
                'page_name': 'appointments',   # IMPORTANT (menu highlight mate)
            }
        )

    # DETAIL PAGE
    @http.route(['/my/appointments/<int:appointment_id>'], type='http', auth="user", website=True)
    def portal_appointment_detail(self, appointment_id, **kw):

        appointment = request.env['hospital.appointment'].browse(appointment_id)

        return request.render(
            "hospital_management.portal_appointment_detail",
            {
                'appointment': appointment
            }
        )