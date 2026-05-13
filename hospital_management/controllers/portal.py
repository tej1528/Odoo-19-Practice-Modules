from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
import pytz
from pytz import timezone, UTC
from odoo import http, fields, _
from odoo.http import request
from odoo.fields import Domain  # આ મુખ્ય છે
from odoo.tools import groupby as group_by_func
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

class HospitalPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)

        if 'appointment_count' in counters:

            partner = request.env.user.partner_id

            if partner.is_patient:
                count = request.env['hospital.appointment'].search_count([
                    ('patient_id', '=', partner.id)
                ])
            else:
                count = 0

            values['appointment_count'] = count

        return values

    # -------------------------------------------------------------------------
    # Searchbar & Filter Configurations
    # -------------------------------------------------------------------------

    def _get_appointment_searchbar_sortings(self):
        return {
            'date': {'label': _('Date'), 'order': 'start_time desc'},
            'code': {'label': _('Appointment No'), 'order': 'code asc'},
            'patient': {'label': _('Patient'), 'order': 'patient_id asc'},
            'doctor': {'label': _('Doctor'), 'order': 'doctor_id asc'},
            'specialization': {'label': _('Specialization'), 'order': 'specialization_id'},
            'fees': {'label': _('Fees'), 'order': 'fees desc'},
        }

    def _get_appointment_searchbar_filters(self):
        today = fields.Date.today()
        
        # સમયગાળાની ગણતરી
        start_of_week = today - timedelta(days=today.weekday())
        last_week_start = start_of_week - timedelta(weeks=1)
        start_of_month = today.replace(day=1)
        last_month_start = start_of_month - relativedelta(months=1)
        next_month_start = start_of_month + relativedelta(months=1)

        # OrderedDict થી સિક્વન્સ ફિક્સ થશે
        filters = OrderedDict([
            ('all', {'label': _('All'), 'domain': []}),
            
            # ૧. સ્ટેટસ મુજબ (image_b7bfdc.png મુજબનો ક્રમ)
            ('draft', {'label': _('Draft'), 'domain': [('status', '=', 'draft')]}),
            ('requested', {'label': _('Requested'), 'domain': [('status', '=', 'requested')]}),
            ('confirmed', {'label': _('Confirmed'), 'domain': [('status', '=', 'confirmed')]}),
            ('processing', {'label': _('Processing'), 'domain': [('status', '=', 'processing')]}),
            ('done', {'label': _('Done'), 'domain': [('status', '=', 'done')]}),
            ('cancel', {'label': _('Cancelled'), 'domain': [('status', '=', 'cancel')]}),
            
            # ૨. સમયગાળા મુજબ
            ('this_week', {
                'label': _('This Week'), 
                'domain': [('start_time', '>=', start_of_week), ('start_time', '<=', start_of_week + timedelta(days=6))]
            }),
            ('last_week', {
                'label': _('Last Week'), 
                'domain': [('start_time', '>=', last_week_start), ('start_time', '<', start_of_week)]
            }),
            ('this_month', {
                'label': _('This Month'), 
                'domain': [('start_time', '>=', start_of_month), ('start_time', '<', next_month_start)]
            }),
            ('last_month', {
                'label': _('Last Month'), 
                'domain': [('start_time', '>=', last_month_start), ('start_time', '<', start_of_month)]
            }),
            ('next_month', {
                'label': _('Next Month'), 
                'domain': [('start_time', '>=', next_month_start), ('start_time', '<', next_month_start + relativedelta(months=1))]
            }),
            ('this_year', {
                'label': _('This Year'), 
                'domain': [
                    ('start_time', '>=', today.replace(month=1, day=1)), 
                    ('start_time', '<=', today.replace(month=12, day=31))
                ]
            }),
        ])
        return filters

    def _get_appointment_searchbar_inputs(self):
        return {
        'all': {'input': 'all', 'label': _('Search in All')},
        'code': {'input': 'code', 'label': _('Search in Code')},
        'patient': {'input': 'patient', 'label': _('Search in Patient')},
        'doctor': {'input': 'doctor', 'label': _('Search in Doctor')},
        'specialization': {'input': 'specialization', 'label': _('Search in Specialization')},
    }

    def _get_appointment_searchbar_groupby(self):
        return {
            'none': {'label': _('None')},
            'patient_id': {'label': _('Patient')},
            'doctor_id': {'label': _('Doctor')},
            'specialization_id': {'label': _('Specialization')},
            'status': {'label': _('Status')},
            'start_time:day': {'label': _('Day')},
            'start_time:week': {'label': _('Week')},
            'start_time:month': {'label': _('Month')},
            'start_time:year': {'label': _('Year')},
        }

    # -------------------------------------------------------------------------
    # Main Portal Route
    # -------------------------------------------------------------------------

    @http.route(['/my/appointments', '/my/appointments/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_appointments(self, page=1, sortby=None, filterby=None, search=None, search_in='all', groupby=None, **kw):
        request_obj = request.env['hospital.appointment'].sudo()
        values = self._prepare_portal_layout_values()

        searchbar_sortings = self._get_appointment_searchbar_sortings()
        searchbar_filters = self._get_appointment_searchbar_filters()
        searchbar_inputs = self._get_appointment_searchbar_inputs()
        searchbar_groupby = self._get_appointment_searchbar_groupby()

        # Defaults
        sortby = sortby or 'code' 
        filterby = filterby or 'all'
        search_in = search_in or 'all'
        groupby_value = groupby or 'none'

        # ૧. સોર્ટિંગ ઓર્ડર
        if groupby_value != 'none':
            sort_field = groupby_value.split(':')[0] if ':' in groupby_value else groupby_value
            order = f"{sort_field}, {searchbar_sortings[sortby]['order']}"
        else:
            order = searchbar_sortings[sortby]['order']

        # ૨. ફિલ્ટર ડોમેન
        raw_filter_domain = searchbar_filters.get(filterby, searchbar_filters.get('all'))['domain']
        domain = Domain(raw_filter_domain)

        # ---------------------------------------------------------
        # ✅ નવો ઉમેરેલો ભાગ: User Security Filtering
        # ---------------------------------------------------------
        user = request.env.user
        partner = user.partner_id

        if partner.is_patient:
            domain = domain & Domain([('patient_id', '=', partner.id)])

        elif partner.is_doctor:
            domain = domain & Domain([('doctor_id', '=', partner.id)])

        # ✅ ADD THIS
        elif request.env.user.has_group('base.group_system'):
            domain = domain  

        else:
            domain = domain & Domain([('id', '=', 0)])  # safety
           
            pass
        # ---------------------------------------------------------

        # ૩. સર્ચ લોજિક
        if search and search_in:
            search_domain = []
            if search_in == 'all':
                search_domain = [
                    '|', '|', '|',
                    ('code', 'ilike', search),
                    ('patient_id.name', 'ilike', search),
                    ('doctor_id.name', 'ilike', search),
                    ('specialization_id.name', 'ilike', search)
                ]
            else:
                if search_in == 'code':
                    search_domain = [('code', 'ilike', search)]
                elif search_in == 'patient':
                    search_domain = [('patient_id.name', 'ilike', search)]
                elif search_in == 'doctor':
                    search_domain = [('doctor_id.name', 'ilike', search)]
                elif search_in == 'specialization':
                    search_domain = [('specialization_id.name', 'ilike', search)]
            
            if search_domain:
                domain = domain & Domain(search_domain)

        # ૪. પેજીનેશન
        appointment_count = request_obj.search_count(domain)
        pager = portal_pager(
            url="/my/appointments",
            url_args={
                'sortby': sortby, 
                'filterby': filterby, 
                'search': search, 
                'search_in': search_in, 
                'groupby': groupby_value
            },
            total=appointment_count,
            page=page,
            step=10
        )

        # ૫. ડેટા ફેચ કરો
        appointments_records = request_obj.search(domain, order=order, limit=10, offset=pager['offset'])
        
        # ૬. ગ્રુપિંગ લોજિક
        grouped_appointments = []
        if groupby_value != 'none':
            if ':' in groupby_value:
                field_name, interval = groupby_value.split(':')
                def groupby_key(record):
                    val = record[field_name]
                    if not val: return _("None")
                    if interval == 'day': return val.strftime('%d %b %Y')
                    if interval == 'week': return _("Week %s") % val.strftime('%U (%b %Y)')
                    if interval == 'month': return val.strftime('%B %Y')
                    if interval == 'year': return val.strftime('%Y')
                    return val
                grouped_appointments = [request_obj.concat(*g) for k, g in group_by_func(appointments_records, groupby_key)]
            else:
                grouped_appointments = [request_obj.concat(*g) for k, g in group_by_func(appointments_records, lambda a: a[groupby_value])]
        else:
            grouped_appointments = [appointments_records]

        # ૭. ફાઇનલ Values અપડેટ
        user_tz = timezone(request.env.user.tz or 'UTC')
        values.update({
            'appointments': appointments_records,
            'grouped_appointments': grouped_appointments,
            'page_name': 'appointments',
            'pager': pager,
            'default_url': '/my/appointments',  
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters, 
            'searchbar_inputs': searchbar_inputs,
            'searchbar_groupby': searchbar_groupby,
            'sortby': sortby,
            'filterby': filterby,
            'search_in': search_in,
            'search': search,
            'groupby': groupby_value,
        })
        return request.render("hospital_management.portal_my_appointments", values)

    @http.route(['/my/appointments/<int:appointment_id>'], type='http', auth="user", website=True)
    def portal_appointment_detail(self, appointment_id, **kw):
        user_partner = request.env.user.partner_id
        
        # ૧. ડોમેન સેટ કરો
        domain = [('id', '=', appointment_id)]
        
        # જો પેશન્ટ હોય તો એની જ દેખાવી જોઈએ, જો ડોક્ટર હોય તો એને મળેલ એપોઇન્ટમેન્ટ
        if user_partner.is_patient:
            domain.append(('patient_id', '=', user_partner.id))
        elif user_partner.is_doctor:
            domain.append(('doctor_id', '=', user_partner.id))
        
        # ૨. રેકોર્ડ સર્ચ (sudo() નો ઉપયોગ કરીને એક્સેસ રાઈટ્સની ચિંતા વગર ડેટા ફેચ થશે)
        appointment = request.env['hospital.appointment'].sudo().search(domain, limit=1)

        if not appointment:
            # લોગમાં ચેક કરવા માટે કે કયા ડોમેનથી સર્ચ કર્યું હતું
            print(f"--- Appointment Not Found for ID: {appointment_id} with Domain: {domain} ---")
            return request.render("website.404")

        # ૩. નેવિગેશન લોજિક
        history_ids = request.session.get('my_appointments_history', [])
        try:
            current_index = history_ids.index(appointment_id) if appointment_id in history_ids else None
        except ValueError:
            current_index = None

        prev_id = history_ids[current_index - 1] if current_index is not None and current_index > 0 else False
        next_id = history_ids[current_index + 1] if current_index is not None and current_index < len(history_ids) - 1 else False

        # ૪. ટાઈમઝોન કન્વર્ઝન
        user_tz = timezone(request.env.user.tz or 'UTC')
        start_time_local = False
        if appointment.start_time:
            # Odoo Datetime હંમેશા UTC માં હોય છે
            start_time_local = pytz.utc.localize(appointment.start_time).astimezone(user_tz)

        return request.render(
            "hospital_management.portal_appointment_detail",
            {
                'appointment': appointment,
                'start_time_local': start_time_local,
                'prev_id': prev_id,
                'next_id': next_id,
                'page_name': 'appointment_detail',
            }
        )
    
    @http.route(['/my/appointments/pdf/<int:appointment_id>'], type='http', auth="user", website=True)
    def download_appointment_report(self, appointment_id, **kw):
        appointment = request.env['hospital.appointment'].sudo().browse(appointment_id)
        if not appointment.exists():
            return request.render('website.404')

        report_action_id = 'hospital_management.action_report_appointment_details'
        pdf, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(report_action_id, [appointment.id])

        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', 'attachment; filename="Appointment_%s.pdf"' % appointment.code)
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

    #portal side appointment form
    from odoo import http
from odoo.http import request


class PortalAppointment(http.Controller):

    @http.route(['/my/appointments/create'], type='http', auth="user", website=True)
    def portal_appointment_create(self, **kw):

        user_partner = request.env.user.partner_id
        is_doctor = user_partner.is_doctor
        doctor = user_partner if is_doctor else False
        patient = user_partner if user_partner.is_patient else False

        doctors = request.env['res.partner'].sudo().search([
            ('is_doctor', '=', True)
        ])

        patients = request.env['res.partner'].sudo().search([
            ('is_patient', '=', True)
        ])

        specializations = request.env['hospital.specialization'].sudo().search([])

        # ✅ PREFILL VALUES (IMPORTANT)
        prefill = {
            'appointment_id': kw.get('appointment_id'),  # ✅ ADD THIS
            'patient_id': kw.get('patient_id'),
            'doctor_id': kw.get('doctor_id'),
            'specialization_id': kw.get('specialization_id'),
            'start_time': kw.get('start_time'),
            'end_time': kw.get('end_time'),
            'fees': kw.get('fees'),
        }

        # ✅ MAIN VALUES
        values = {
            'page_name': 'create_appointment',
            'is_doctor': is_doctor,
            'doctor': doctor,
            'patient': patient,            
            'doctors': doctors,
            'patients': patients,
            'specializations': specializations,
            'specialization': doctor.specialization_id if doctor else False,
            'fees': doctor.fees if doctor else 0.0,

            # ✅ ADD THIS
            'prefill': prefill,
        }

        return request.render("hospital_management.portal_create_appointment_template", values)

    # =========================================================
    # Get Doctor Details (AJAX)
    # =========================================================
    # controllers/portal.py

    # ૧. સ્પેશિયલાઈઝેશન મુજબ ડોક્ટરોનું લિસ્ટ ફિલ્ટર કરવા માટે
    @http.route('/get_doctors_by_specialization', type='jsonrpc', auth="user", website=True)
    def get_doctors_by_specialization(self, specialization_id=None):

        domain = [('is_doctor', '=', True)]

        if specialization_id:
            try:
                specialization_id = int(specialization_id)
                domain.append(('specialization_id', '=', specialization_id))
            except:
                pass  # safe fallback

        doctors = request.env['res.partner'].sudo().search(domain)

        return [
    {
        'id': d.id,
        'name': d.name,
        'fees': d.fees,
        'specialization_id': d.specialization_id.id,
        'specialization_name': d.specialization_id.name,
    }
    for d in doctors
]

    # =========================================================
    # DOCTOR → DETAILS
    # =========================================================

    @http.route('/get_doctor_details', type='jsonrpc', auth="user", website=True)
    def get_doctor_details(self, doctor_id=None):

        if not doctor_id:
            return {}

        try:
            doctor_id = int(doctor_id)
        except:
            return {}

        doctor = request.env['res.partner'].sudo().browse(doctor_id)

        if not doctor.exists():
            return {}

        return {
            'fees': doctor.fees or 0.0,
            'specialization_id': doctor.specialization_id.id if doctor.specialization_id else False,
            'specialization_name': doctor.specialization_id.name if doctor.specialization_id else '',
        }

    @http.route(['/my/appointment/save'], type='http', auth="user", website=True, methods=['POST'], csrf=True)
    def portal_appointment_save(self, **post):
        patient = request.env.user.partner_id

        if request.env.user.partner_id.is_doctor:
            doctor_id = request.env.user.partner_id.id
        else:
            doctor_id = post.get('doctor_id')

        spec_id = post.get('specialization_id')
        start_time_raw = post.get('start_time')
        end_time_raw = post.get('end_time')
        notes = post.get('notes')

        if not doctor_id:
            return request.redirect('/my/appointments/create?error=no_doctor')

        doctor = request.env['res.partner'].sudo().browse(int(doctor_id))

        # --- Timezone Logic ---
        user_tz = pytz.timezone(request.env.user.tz or 'UTC')
        try:
            start_dt = datetime.strptime(start_time_raw, '%Y-%m-%dT%H:%M')
            end_dt = datetime.strptime(end_time_raw, '%Y-%m-%dT%H:%M') if end_time_raw else start_dt + timedelta(minutes=30)

            start_utc = user_tz.localize(start_dt).astimezone(pytz.UTC).replace(tzinfo=None)
            end_utc = user_tz.localize(end_dt).astimezone(pytz.UTC).replace(tzinfo=None)
        except Exception:
            return request.redirect('/my/appointments/create?error=date_format')

        # --- COMMON VALUES ---
        appointment_id = post.get('appointment_id')

        vals = {
            'patient_id': int(post.get('patient_id')) if post.get('patient_id') else patient.id,
            'doctor_id': doctor.id,
            'specialization_id': int(spec_id) if spec_id else False,
            'fees': float(post.get('fees') or doctor.fees or 0.0),
            'start_time': start_utc,
            'end_time': end_utc,
            'notes': notes,
        }

        # =========================================================
        # ✅ UPDATE EXISTING APPOINTMENT
        # =========================================================
        if appointment_id:
            appointment = request.env['hospital.appointment'].sudo().browse(int(appointment_id))

            if appointment.exists():

                # 🔥 FIX: cancel → draft → requested
                if appointment.status == 'cancel':
                    appointment.write({'status': 'draft'})

                # update data
                appointment.write(vals)

                # final state
                appointment.write({'status': 'requested'})

        # =========================================================
        # ✅ CREATE NEW APPOINTMENT
        # =========================================================
        else:
            request.env['hospital.appointment'].sudo().create({
                **vals,
                'status': 'requested',
            })

        return request.redirect('/my/appointments')
    
    @http.route('/my/appointment/accept/<int:appointment_id>', type='http', auth="user", website=True)
    def accept_appointment(self, appointment_id, **kw):

        appointment = request.env['hospital.appointment'].sudo().browse(appointment_id)

        if request.env.user.partner_id.id == appointment.doctor_id.id:
            appointment.write({'status': 'confirmed'})

        return request.redirect('/my/appointments')


    @http.route(type='http', auth="user", website=True)
    def reject_appointment(self, appointment_id, **kw):

        appointment = request.env['hospital.appointment'].sudo().browse(appointment_id)

        if request.env.user.partner_id.id == appointment.doctor_id.id:
            appointment.write({'status': 'cancel'})

        return request.redirect('/my/appointments')
    

    @http.route('/my/appointment/start/<int:appointment_id>', type='http', auth="user", website=True)
    def start_processing(self, appointment_id, **kw):

        appointment = request.env['hospital.appointment'].sudo().browse(appointment_id)

        if request.env.user.partner_id.id == appointment.doctor_id.id:
            appointment.action_processing()

        return request.redirect('/my/appointments/%s' % appointment_id)
    
    @http.route('', type='http', auth="user", website=True)
    def mark_done(self, appointment_id, **kw):

        appointment = request.env['hospital.appointment'].sudo().browse(appointment_id)

        if request.env.user.partner_id.id == appointment.doctor_id.id:
            appointment.action_done()

        return request.redirect('/my/appointments/%s' % appointment_id)
    
    @http.route('/my/appointment/done', type='http', auth="user", website=True, methods=['POST'])
    def portal_done_with_note(self, **post):

        appointment_id = int(post.get('appointment_id'))
        note = post.get('doctor_note')

        appointment = request.env['hospital.appointment'].sudo().browse(appointment_id)

        if request.env.user.partner_id.id == appointment.doctor_id.id:

            if not note:
                return request.redirect('/my/appointments?error=no_note')

            appointment.write({
                'doctor_description': note
            })

            appointment.action_done()

        return request.redirect('/my/appointments')
    
    @http.route('/my/appointment/reject', type='http', auth="user", website=True, methods=['POST'], csrf=True)
    def reject_appointment(self, **post):

        appointment_id = int(post.get('appointment_id'))
        reason = post.get('cancel_reason')

        appointment = request.env['hospital.appointment'].sudo().browse(appointment_id)

        if request.env.user.partner_id.id == appointment.doctor_id.id:
            appointment.write({
                'status': 'cancel',
                'cancel_reason': reason
            })

        return request.redirect('/my/appointments/%s' % appointment_id)
    
    @http.route('/my/appointment/reset/<int:appointment_id>', type='http', auth="user", website=True)
    def reset_appointment(self, appointment_id, **kw):

        appointment = request.env['hospital.appointment'].sudo().browse(appointment_id)

        # security check
        if request.env.user.partner_id.id not in [
            appointment.patient_id.id,
            appointment.doctor_id.id
        ]:
            return request.redirect('/my/appointments')

        user_tz = pytz.timezone(request.env.user.tz or 'UTC')

        start_time = ''
        end_time = ''

        if appointment.start_time:
            start_time = pytz.utc.localize(appointment.start_time).astimezone(user_tz).strftime('%Y-%m-%dT%H:%M')

        if appointment.end_time:
            end_time = pytz.utc.localize(appointment.end_time).astimezone(user_tz).strftime('%Y-%m-%dT%H:%M')

        # 👉 Redirect with prefilled values
        return request.redirect(
            f"/my/appointments/create?"
            f"appointment_id={appointment.id}&"
            f"patient_id={appointment.patient_id.id}&"
            f"doctor_id={appointment.doctor_id.id}&"
            f"specialization_id={appointment.specialization_id.id if appointment.specialization_id else ''}&"
            f"start_time={start_time}&"
            f"end_time={end_time}&"
            f"fees={appointment.fees}"
        )