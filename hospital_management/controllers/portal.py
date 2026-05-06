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
            values['appointment_count'] = request.env['hospital.appointment'].search_count([])
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
        request_obj = request.env['hospital.appointment']
        values = self._prepare_portal_layout_values()

        searchbar_sortings = self._get_appointment_searchbar_sortings()
        searchbar_filters = self._get_appointment_searchbar_filters()
        searchbar_inputs = self._get_appointment_searchbar_inputs()
        searchbar_groupby = self._get_appointment_searchbar_groupby()

        # Defaults
        sortby = sortby or 'code' 
        filterby = filterby or 'all'
        search_in = search_in or 'all' # સુધારો
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

        # ૩. સર્ચ લોજિક - Odoo 19 Standard
        if search and search_in:
            search_domain = [] # અહીં સાદું લિસ્ટ વાપરો
            
            if search_in == 'all':
                # 'all' માટે 4 ફિલ્ડ છે, એટલે 3 વખત '|' આવશે
                search_domain = [
                    '|', '|', '|',
                    ('code', 'ilike', search),
                    ('patient_id.name', 'ilike', search),
                    ('doctor_id.name', 'ilike', search),
                    ('specialization_id.name', 'ilike', search)
                ]
            else:
                # ચોક્કસ ફિલ્ડ માટે કોઈ '|' ની જરૂર નથી, કારણ કે શરત એક જ છે
                if search_in == 'code':
                    search_domain = [('code', 'ilike', search)]
                elif search_in == 'patient':
                    search_domain = [('patient_id.name', 'ilike', search)]
                elif search_in == 'doctor':
                    search_domain = [('doctor_id.name', 'ilike', search)]
                elif search_in == 'specialization':
                    search_domain = [('specialization_id.name', 'ilike', search)]
            
            # ફિલ્ટર અને સર્ચ ડોમેનને ભેગા કરો
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
                    if not val:
                        return _("None")
                    if interval == 'day':
                        return val.strftime('%d %b %Y')
                    if interval == 'week':
                        return _("Week %s") % val.strftime('%U (%b %Y)')
                    if interval == 'month':
                        return val.strftime('%B %Y')
                    if interval == 'year':
                        return val.strftime('%Y')
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
        appointment = request.env['hospital.appointment'].browse(appointment_id)
        if not appointment.exists():
            return request.render("website.404")

        # Navigation: Prev/Next from session history
        history_ids = request.session.get('my_appointments_history', [])
        current_index = history_ids.index(appointment_id) if appointment_id in history_ids else None
        
        prev_id = history_ids[current_index - 1] if current_index is not None and current_index > 0 else False
        next_id = history_ids[current_index + 1] if current_index is not None and current_index < len(history_ids) - 1 else False
        
        user_tz = timezone(request.env.user.tz or 'UTC')
        start_time_local = UTC.localize(appointment.start_time).astimezone(user_tz) if appointment.start_time else False
        
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
    @http.route(
        ['/my/appointments/create'],
        type='http',
        auth="user",
        website=True
    )
    def portal_appointment_create(self, **kw):

        patients = request.env['res.partner'].sudo().search([
            ('is_patient', '=', True)
        ])

        doctors = request.env['res.partner'].sudo().search([
            ('is_doctor', '=', True)
        ])

        values = {
            'patients': patients,
            'doctors': doctors,
            'page_name': 'create_appointment',
        }

        return request.render(
            "hospital_management.portal_create_appointment_template",
            values
        )

    # =========================================================
    # Get Doctor Details (AJAX)
    # =========================================================
    @http.route('/get_doctor_details', type='jsonrpc', auth="user", website=True)
    def get_doctor_details(self, doctor_id):

        doctor = request.env['res.partner'].sudo().browse(
            int(doctor_id)
        )

        if doctor.exists():

            duration = int(
                request.env['ir.config_parameter']
                .sudo()
                .get_param(
                    'hospital.appointment_duration',
                    default=30
                )
            )

            return {

                'fees': doctor.fees or 0,

                'specialization': (
                    doctor.specialization_id.name
                    if doctor.specialization_id
                    else ''
                ),

                'duration': duration,
            }

        return {}

    @http.route(['/my/appointment/save'], type='http', auth="user", website=True, methods=['POST'], csrf=True )
    def portal_appointment_save(self, **post):

        patient_id = int(post.get('patient_id'))

        doctor_id = int(post.get('doctor_id'))

        # =========================
        # Datetime Fix
        # =========================
        user_tz = pytz.timezone(
            request.env.user.tz or 'UTC'
        )

        # Parse local time
        start_time = datetime.strptime(
            post.get('start_time'),
            '%Y-%m-%dT%H:%M'
        )

        end_time = datetime.strptime(
            post.get('end_time'),
            '%Y-%m-%dT%H:%M'
        )

        # Convert to UTC
        start_time = user_tz.localize(start_time).astimezone(pytz.UTC).replace(tzinfo=None)
        end_time = user_tz.localize(end_time).astimezone(pytz.UTC).replace(tzinfo=None)

        notes = post.get('notes')

        doctor = request.env['res.partner'].sudo().browse(
            doctor_id
        )

        request.env['hospital.appointment'].sudo().create({

            'patient_id': patient_id,

            'doctor_id': doctor_id,

            'specialization_id': (
                doctor.specialization_id.id
                if doctor.specialization_id
                else False
            ),

            'fees': doctor.fees or 0,

            'start_time': start_time,

            'end_time': end_time,

            'notes': notes,

            'status': 'requested',
        })

        return request.redirect('/my/appointments')