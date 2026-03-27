from odoo import http
from odoo.http import request
from .portal import CaqaCustomerPortal


class CaqaProgramPortal(CaqaCustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        institution = self._get_caqa_institution()
        if institution:
            values['caqa_program_count'] = request.env['caqa.program'].sudo().search_count([('institution_id', '=', institution.id)])
        return values

    @http.route(['/my/caqa/programs'], type='http', auth='user', website=True)
    def portal_caqa_programs(self, **kw):
        institution = self._get_caqa_institution()
        if not institution:
            return request.redirect('/my/home')
        programs = request.env['caqa.program'].sudo().search([('institution_id', '=', institution.id)])
        return request.render('caqa_portal.portal_caqa_programs', {
            'programs': programs,
            'institution': institution,
        })

    @http.route(['/my/caqa/program/new'], type='http', auth='user', website=True, methods=['GET', 'POST'])
    def portal_caqa_program_new(self, **post):
        institution = self._get_caqa_institution()
        if not institution:
            return request.redirect('/my/home')
            
        if request.httprequest.method == 'POST':
            # Create program
            program = request.env['caqa.program'].sudo().create({
                'name': post.get('name', 'New Program'),
                'arabic_name': post.get('arabic_name'),
                'code': post.get('code'),
                'institution_id': institution.id,
                'degree_level': post.get('degree_level', 'bachelor'),
                'delivery_mode': post.get('delivery_mode', 'onsite'),
                'language': post.get('language', 'ar'),
                'college_name': post.get('college_name'),
                'department_name': post.get('department_name'),
                'duration_years': float(post.get('duration_years', 4.0)),
                'credit_hours': float(post.get('credit_hours', 120.0)),
                'state': 'draft'  # Explicitly set status to draft
            })
            return request.redirect('/my/caqa/program/%s' % program.id)
            
        return request.render('caqa_portal.portal_caqa_program_form_new', {'institution': institution})

    @http.route(['/my/caqa/program/<int:program_id>'], type='http', auth='user', website=True, methods=['GET', 'POST'])
    def portal_caqa_program_detail(self, program_id, **post):
        program = self._check_caqa_record('caqa.program', program_id)
        if hasattr(program, 'status_code'):
            return program
            
        if request.httprequest.method == 'POST':
            # Only allow update if state is draft
            if program.state == 'draft':
                program.sudo().write({
                    'name': post.get('name', program.name),
                    'arabic_name': post.get('arabic_name', program.arabic_name),
                    'code': post.get('code', program.code),
                    'degree_level': post.get('degree_level', program.degree_level),
                    'delivery_mode': post.get('delivery_mode', program.delivery_mode),
                    'language': post.get('language', program.language),
                    'college_name': post.get('college_name', program.college_name),
                    'department_name': post.get('department_name', program.department_name),
                    'duration_years': float(post.get('duration_years', program.duration_years)),
                    'credit_hours': float(post.get('credit_hours', program.credit_hours)),
                    'vision': post.get('vision', program.vision),
                    'mission': post.get('mission', program.mission),
                    'description': post.get('description', program.description),
                })
            # Redirect to GET to avoid resubmit on refresh
            return request.redirect('/my/caqa/program/%s' % program.id)

        # Render detail template (which detects if state == 'draft' to make it editable or readonly)
        return request.render('caqa_portal.portal_caqa_program_detail', {'program': program})
        
    @http.route(['/my/caqa/program/<int:program_id>/course/add'], type='http', auth='user', website=True, methods=['POST'])
    def portal_caqa_program_add_course(self, program_id, **post):
        program = self._check_caqa_record('caqa.program', program_id)
        if hasattr(program, 'status_code'):
            return program
            
        if program.state == 'draft':
            request.env['caqa.program.course'].sudo().create({
                'program_id': program.id,
                'name': post.get('name'),
                'code': post.get('code'),
                'credit_hours': float(post.get('credit_hours', 3.0)),
            })
            
        return request.redirect('/my/caqa/program/%s' % program.id)
        
    @http.route(['/my/caqa/program/<int:program_id>/lo/add'], type='http', auth='user', website=True, methods=['POST'])
    def portal_caqa_program_add_lo(self, program_id, **post):
        program = self._check_caqa_record('caqa.program', program_id)
        if hasattr(program, 'status_code'):
            return program
            
        if program.state == 'draft':
            request.env['caqa.program.learning.outcome'].sudo().create({
                'program_id': program.id,
                'code': post.get('code'),
                'name': post.get('name', 'New Outcome'),
                'description': post.get('description'),
                'outcome_type': post.get('outcome_type', 'knowledge'),
            })
            
        return request.redirect('/my/caqa/program/%s' % program.id)
