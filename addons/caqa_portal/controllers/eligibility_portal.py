from odoo import http, _
from odoo.http import request
from .portal import CaqaCustomerPortal


class CaqaEligibilityPortal(CaqaCustomerPortal):

    @http.route(['/my/caqa/eligibilities'], type='http', auth='user', website=True)
    def portal_caqa_eligibilities(self, **kw):
        institution = self._get_caqa_institution()
        if not institution:
            return request.redirect('/my/home')
        eligibilities = request.env['caqa.eligibility.request'].sudo().search([('institution_id', '=', institution.id)])
        return request.render('caqa_portal.portal_caqa_eligibilities', {
            'eligibilities': eligibilities, 
            'institution': institution
        })

    @http.route(['/my/caqa/eligibility/new'], type='http', auth='user', website=True, methods=['GET', 'POST'])
    def portal_caqa_eligibility_new(self, **post):
        institution = self._get_caqa_institution()
        if not institution:
            return request.redirect('/my/home')
            
        if request.httprequest.method == 'POST':
            try:
                program_id = int(post.get('program_id') or 0)
                accreditation_type_id = int(post.get('accreditation_type_id') or 0)
                cycle_id = int(post.get('cycle_id') or 0)
                standard_version_id = int(post.get('standard_version_id') or 0)
            except ValueError:
                program_id = accreditation_type_id = cycle_id = standard_version_id = 0
            
            if program_id and accreditation_type_id and cycle_id and standard_version_id:
                eligibility = request.env['caqa.eligibility.request'].sudo().create({
                    'name': post.get('name', 'New Eligibility Request'),
                    'institution_id': institution.id,
                    'program_id': program_id,
                    'accreditation_type_id': accreditation_type_id,
                    'cycle_id': cycle_id,
                    'standard_version_id': standard_version_id,
                    'state': 'draft'
                })
                # The model's create method automatically generates the checklist lines
                return request.redirect('/my/caqa/eligibility/%s' % eligibility.id)
                
        # GET request: fetch data for the dropdowns
        programs = request.env['caqa.program'].sudo().search([('institution_id', '=', institution.id), ('state', '=', 'active')])
        accreditation_types = request.env['caqa.accreditation.type'].sudo().search([])
        cycles = request.env['caqa.accreditation.cycle'].sudo().search([])
        standard_versions = request.env['caqa.standard.version'].sudo().search([])
        
        return request.render('caqa_portal.portal_caqa_eligibility_form_new', {
            'institution': institution,
            'programs': programs,
            'accreditation_types': accreditation_types,
            'cycles': cycles,
            'standard_versions': standard_versions,
        })

    @http.route(['/my/caqa/eligibility/<int:eligibility_id>'], type='http', auth='user', website=True, methods=['GET', 'POST'])
    def portal_caqa_eligibility_detail(self, eligibility_id, **post):
        eligibility = self._check_caqa_record('caqa.eligibility.request', eligibility_id)
        if hasattr(eligibility, 'status_code'):
            return eligibility
            
        if request.httprequest.method == 'POST':
            if eligibility.state == 'draft':
                # Update basic fields if provided
                if post.get('name'):
                    eligibility.sudo().write({'name': post.get('name')})
                if post.get('program_id'):
                    eligibility.sudo().write({'program_id': int(post.get('program_id'))})
                if post.get('accreditation_type_id'):
                    eligibility.sudo().write({'accreditation_type_id': int(post.get('accreditation_type_id'))})
                if post.get('cycle_id'):
                    eligibility.sudo().write({'cycle_id': int(post.get('cycle_id'))})
                if post.get('standard_version_id'):
                    eligibility.sudo().write({'standard_version_id': int(post.get('standard_version_id'))})
                    
                # Update checklist lines
                # The form will send the provided lines as a list of ids
                for line in eligibility.checklist_line_ids:
                    provided = post.get('provided_%s' % line.id) == 'on'
                    line.sudo().write({'provided': provided})
                    
            return request.redirect('/my/caqa/eligibility/%s' % eligibility.id)

        institution = self._get_caqa_institution()
        programs = request.env['caqa.program'].sudo().search([('institution_id', '=', institution.id), ('state', '=', 'active')])
        accreditation_types = request.env['caqa.accreditation.type'].sudo().search([])
        cycles = request.env['caqa.accreditation.cycle'].sudo().search([])
        standard_versions = request.env['caqa.standard.version'].sudo().search([])
        
        return request.render('caqa_portal.portal_caqa_eligibility_detail', {
            'eligibility': eligibility,
            'programs': programs,
            'accreditation_types': accreditation_types,
            'cycles': cycles,
            'standard_versions': standard_versions,
        })
        
    @http.route(['/my/caqa/eligibility/<int:eligibility_id>/submit'], type='http', auth='user', website=True, methods=['POST'])
    def portal_caqa_eligibility_submit(self, eligibility_id, **post):
        eligibility = self._check_caqa_record('caqa.eligibility.request', eligibility_id)
        if hasattr(eligibility, 'status_code'):
            return eligibility
            
        if eligibility.state in ('draft', 'in_progress'):
            try:
                # If checklist was also posted during submit, save it first
                for line in eligibility.checklist_line_ids:
                    provided = post.get('provided_%s' % line.id) == 'on'
                    line.sudo().write({'provided': provided})
                    
                eligibility.sudo().action_submit()
            except Exception as e:
                # Store the error message in the session or render a custom alert
                request.session['form_error'] = str(e)
                
        return request.redirect('/my/caqa/eligibility/%s' % eligibility.id)
