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

        all_appointments = request.env['hospital.appointment'].search([], order='id asc')
        ids = all_appointments.ids
        current_index = ids.index(appointment_id)

        prev_id = ids[current_index - 1] if current_index > 0 else False
        next_id = ids[current_index + 1] if current_index < len(ids) - 1 else False
        
        user_tz = timezone(request.env.user.tz or 'UTC')
        start_time_local = UTC.localize(appointment.start_time).astimezone(user_tz) if appointment.start_time else False
        end_time_local = UTC.localize(appointment.end_time).astimezone(user_tz) if appointment.end_time else False
        
        return request.render(
            "hospital_management.portal_appointment_detail",
            {
                'appointment': appointment,
                'start_time_local': start_time_local,
                'end_time_local': end_time_local,
                'prev_id': prev_id,
                'next_id': next_id,
                'page_name': 'appointment_detail',
            }
        )
    
    @http.route(['/my/appointments/pdf/<int:appointment_id>'], type='http', auth="user", website=True)
    def portal_appointment_report_download(self, appointment_id, **kw):
        appointment = request.env['hospital.appointment'].sudo().browse(appointment_id)
        if not appointment.exists():
            return request.render('website.404')

        # અહીં 'hospital_management.action_report_appointment' માં તમારા રિપોર્ટની સાચી ID લખવી
        try:
            report_sudo = request.env.ref('hospital_management.action_report_appointment').sudo()
        except:
            # જો એક્શન આઈડી ન મળે તો ભૂલ અટકાવવા
            return request.render('website.404')

        pdf_content, content_type = report_sudo._render_qweb_pdf(appointment.id)
        
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf_content)),
            ('Content-Disposition', 'attachment; filename="Appointment_%s.pdf"' % appointment.code)
        ]
        return request.make_response(pdf_content, headers=pdfhttpheaders)
    
    @http.route(['/my/appointments/pdf/<int:appointment_id>'], type='http', auth="public", website=True)
    def portal_appointment_report_pdf(self, appointment_id, **kw):
        # એપોઇન્ટમેન્ટ રેકોર્ડ શોધો
        appointment = request.env['hospital.appointment'].sudo().browse(appointment_id)
        
        # PDF રિપોર્ટ જનરેટ કરો (રિપોર્ટની XML ID અહીં વાપરો)
        pdf, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'your_module_name.action_report_appointment_details', [appointment.id]
        )
        
        # PDF ડાઉનલોડ રિસ્પોન્સ
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', 'attachment; filename="Appointment_Details.pdf"')
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)
    
    @http.route(['/my/appointments/pdf/<int:appointment_id>'], type='http', auth="user", website=True)
    def download_appointment_report(self, appointment_id, **kw):
        # ૧. એપોઇન્ટમેન્ટનો રેકોર્ડ મેળવો
        appointment = request.env['hospital.appointment'].sudo().browse(appointment_id)
        
        if not appointment.exists():
            return request.render('website.404')

        # ૨. રિપોર્ટ એક્શનની XML ID નો ઉપયોગ કરીને PDF જનરેટ કરો
        # અહીં 'your_module_name.action_report_appointment_details' માં તમારા મોડ્યુલનું નામ લખવું
        report_action_id = 'hospital_management.action_report_appointment_details'
        
        pdf, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(report_action_id, [appointment.id])

        # ૩. PDF ફાઇલ તરીકે રિસ્પોન્સ મોકલો
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', 'attachment; filename="Appointment_%s.pdf"' % appointment.code)
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)