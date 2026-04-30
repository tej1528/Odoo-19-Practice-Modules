from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from pytz import timezone, UTC

class HospitalPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'appointment_count' in counters:
            values['appointment_count'] = request.env['hospital.appointment'].search_count([])
        return values

    @http.route(['/my/appointments', '/my/appointments/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_appointments(self, page=1, **kw):
        request_obj = request.env['hospital.appointment']
        
        # Pager configuration
        total = request_obj.search_count([])
        pager = portal_pager(
            url="/my/appointments",
            total=total,
            page=page,
            step=10
        )

        appointments_records = request_obj.search([], limit=10, offset=pager['offset'])
        user_tz = timezone(request.env.user.tz or 'UTC')
        
        appointment_list = []
        for app in appointments_records:
            # Timezone conversion for Start and End time
            st_local = UTC.localize(app.start_time).astimezone(user_tz) if app.start_time else False
            et_local = UTC.localize(app.end_time).astimezone(user_tz) if app.end_time else False
            
            appointment_list.append({
                'id': app.id,
                'code': app.code,
                'patient_name': app.patient_id.name,
                'doctor_name': app.doctor_id.name,
                'fees': app.fees,
                'status': app.status,
                'start_time_local': st_local,
                'end_time_local': et_local,
            })

        return request.render("hospital_management.portal_my_appointments", {
            'appointments': appointment_list,
            'page_name': 'appointments',
            'pager': pager,
        })

    @http.route(['/my/appointments/<int:appointment_id>'], type='http', auth="user", website=True)
    def portal_appointment_detail(self, appointment_id, **kw):
        appointment = request.env['hospital.appointment'].browse(appointment_id)
        if not appointment.exists():
            return request.render("website.404")

        user_tz = timezone(request.env.user.tz or 'UTC')
        start_time_local = UTC.localize(appointment.start_time).astimezone(user_tz) if appointment.start_time else False
        end_time_local = UTC.localize(appointment.end_time).astimezone(user_tz) if appointment.end_time else False
        
        return request.render(
            "hospital_management.portal_appointment_detail",
            {
                'appointment': appointment,
                'start_time_local': start_time_local,
                'end_time_local': end_time_local,
                'page_name': 'appointment_detail',
            }
        )