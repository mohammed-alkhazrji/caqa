from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request
import base64


class CaqaCustomerPortal(CustomerPortal):

    def _get_caqa_institution(self):
        user = request.env.user
        member = request.env['caqa.institution.member'].sudo().search([('user_id', '=', user.id), ('active', '=', True)], limit=1)
        return member.institution_id if member else False

    def _check_caqa_record(self, model, record_id, institution_field='institution_id'):
        institution = self._get_caqa_institution()
        if not institution:
            return request.not_found()
        record = request.env[model].sudo().browse(record_id)
        if not record.exists():
            return request.not_found()
        owner = record
        for part in institution_field.split('.'):
            owner = owner[part]
        if owner.id != institution.id:
            return request.not_found()
        return record

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        institution = self._get_caqa_institution()
        if institution:
            values.update({
                'caqa_institution': institution,
                'caqa_application_count': request.env['caqa.application'].sudo().search_count([('institution_id', '=', institution.id)]),
                'caqa_eligibility_count': request.env['caqa.eligibility.request'].sudo().search_count([('institution_id', '=', institution.id)]),
                'caqa_deficiency_count': request.env['caqa.application.deficiency'].sudo().search_count([('application_id.institution_id', '=', institution.id), ('state', 'not in', ['resolved', 'closed'])]),
                'caqa_decision_count': request.env['caqa.final.decision'].sudo().search_count([('institution_id', '=', institution.id)]),
            })
        return values

    @http.route(['/my/caqa', '/my/caqa/dashboard'], type='http', auth='user', website=True)
    def portal_caqa_dashboard(self, **kw):
        institution = self._get_caqa_institution()
        applications = request.env['caqa.application'].sudo().search([('institution_id', '=', institution.id)]) if institution else request.env['caqa.application']
        values = self._prepare_home_portal_values([])
        values.update({
            'applications': applications,
            'avg_completion': sum(applications.mapped('completion_rate')) / len(applications) if applications else 0.0,
            'avg_readiness': sum(applications.mapped('readiness_score')) / len(applications) if applications else 0.0,
        })
        return request.render('caqa_portal.portal_caqa_dashboard', values)

    @http.route(['/my/caqa/profile'], type='http', auth='user', website=True, methods=['GET', 'POST'])
    def portal_caqa_profile(self, **post):
        institution = self._get_caqa_institution()
        if not institution:
            return request.redirect('/my')
        profile = institution.active_profile_id or request.env['caqa.institution.profile'].sudo().search([('institution_id', '=', institution.id)], limit=1)
        if request.httprequest.method == 'POST':
            vals = {
                'overview': post.get('overview'),
                'vision': post.get('vision'),
                'mission': post.get('mission'),
                'strategic_goals': post.get('strategic_goals'),
                'governance_structure': post.get('governance_structure'),
                'quality_system_summary': post.get('quality_system_summary'),
            }
            if profile:
                profile.sudo().write(vals)
            else:
                profile = request.env['caqa.institution.profile'].sudo().create({
                    'name': '%s - Portal Profile' % institution.name,
                    'institution_id': institution.id,
                    **vals,
                })
        return request.render('caqa_portal.portal_caqa_profile', {'institution': institution, 'profile': profile})

    @http.route(['/my/caqa/applications'], type='http', auth='user', website=True, methods=['GET', 'POST'])
    def portal_caqa_applications(self, **post):
        institution = self._get_caqa_institution()
        if not institution:
            return request.redirect('/my')
        applications = request.env['caqa.application'].sudo().search([('institution_id', '=', institution.id)]) if institution else request.env['caqa.application']
        
        if request.httprequest.method == 'POST':
            errors = {}
            name = post.get('name', '').strip()
            program_id = post.get('program_id')
            accreditation_type_id = post.get('accreditation_type_id')
            cycle_id = post.get('cycle_id')
            standard_version_id = post.get('standard_version_id')
            eligibility_id = post.get('eligibility_id')
            
            if not name: errors['name'] = True
            if not program_id: errors['program_id'] = True
            if not accreditation_type_id: errors['accreditation_type_id'] = True
            if not cycle_id: errors['cycle_id'] = True
            if not standard_version_id: errors['standard_version_id'] = True
            
            if not errors:
                vals = {
                    'name': name,
                    'institution_id': institution.id,
                    'program_id': int(program_id),
                    'accreditation_type_id': int(accreditation_type_id),
                    'cycle_id': int(cycle_id),
                    'standard_version_id': int(standard_version_id),
                }
                if eligibility_id:
                    vals['eligibility_id'] = int(eligibility_id)
                app = request.env['caqa.application'].sudo().create(vals)
                return request.redirect('/my/caqa/application/%s' % app.id)
            
            # Return with errors
            programs = request.env['caqa.program'].sudo().search([('institution_id', '=', institution.id)])
            acc_types = request.env['caqa.accreditation.type'].sudo().search([('active', '=', True)])
            cycles = request.env['caqa.accreditation.cycle'].sudo().search([('active', '=', True)])
            std_versions = request.env['caqa.standard.version'].sudo().search([('active', '=', True)])
            eligibilities = request.env['caqa.eligibility.request'].sudo().search([('institution_id', '=', institution.id), ('state', '=', 'eligible')])
            return request.render('caqa_portal.portal_caqa_applications', {
                'applications': applications, 'institution': institution,
                'show_create': True, 'errors': errors, 'post': post,
                'programs': programs, 'acc_types': acc_types, 'cycles': cycles,
                'std_versions': std_versions, 'eligibilities': eligibilities,
            })
        
        programs = request.env['caqa.program'].sudo().search([('institution_id', '=', institution.id)])
        acc_types = request.env['caqa.accreditation.type'].sudo().search([('active', '=', True)])
        cycles = request.env['caqa.accreditation.cycle'].sudo().search([('active', '=', True)])
        std_versions = request.env['caqa.standard.version'].sudo().search([('active', '=', True)])
        eligibilities = request.env['caqa.eligibility.request'].sudo().search([('institution_id', '=', institution.id), ('state', '=', 'eligible')])
        return request.render('caqa_portal.portal_caqa_applications', {
            'applications': applications, 'institution': institution,
            'programs': programs, 'acc_types': acc_types, 'cycles': cycles,
            'std_versions': std_versions, 'eligibilities': eligibilities,
        })

    @http.route(['/my/caqa/application/<int:application_id>/start'], type='http', auth='user', website=True, methods=['POST'])
    def portal_caqa_application_start(self, application_id, **post):
        """Generate structure and move to in_progress state."""
        app = self._check_caqa_record('caqa.application', application_id)
        if hasattr(app, 'status_code'):
            return app
        if app.state == 'draft':
            app.sudo().action_generate_structure()
        return request.redirect('/my/caqa/application/%s' % application_id)


    @http.route(['/my/caqa/application/<int:application_id>'], type='http', auth='user', website=True)
    def portal_caqa_application_detail(self, application_id, **kw):
        app = self._check_caqa_record('caqa.application', application_id)
        if hasattr(app, 'status_code'):
            return app
        return request.render('caqa_portal.portal_caqa_application_detail', {
            'application': app,
            'breadcrumbs': [{'name': app.reference or app.name, 'url': None}],
        })

    @http.route(['/my/caqa/application/<int:application_id>/submit'], type='http', auth='user', website=True, methods=['POST'])
    def portal_caqa_application_submit(self, application_id, **post):
        app = self._check_caqa_record('caqa.application', application_id)
        if hasattr(app, 'status_code'):
            return app
        app.sudo().action_submit()
        return request.redirect('/my/caqa/application/%s' % application_id)

    @http.route(['/my/caqa/application/<int:application_id>/resubmit'], type='http', auth='user', website=True, methods=['POST'])
    def portal_caqa_application_resubmit(self, application_id, **post):
        app = self._check_caqa_record('caqa.application', application_id)
        if hasattr(app, 'status_code'):
            return app
        app.sudo().action_resubmit()
        return request.redirect('/my/caqa/application/%s' % application_id)

    @http.route(['/my/caqa/indicator/<int:indicator_id>'], type='http', auth='user', website=True, methods=['GET', 'POST'])
    def portal_caqa_indicator_detail(self, indicator_id, **post):
        indicator = self._check_caqa_record('caqa.application.indicator', indicator_id, 'application_id.institution_id')
        if hasattr(indicator, 'status_code'):
            return indicator
        if request.httprequest.method == 'POST':
            indicator.sudo().write({
                'narrative_html': post.get('narrative_html'),
                'response_state': post.get('response_state') or 'in_progress',
            })
            # Save per-checkpoint values submitted from the form
            for cp in indicator.checkpoint_ids:
                boolean_key = 'cp_boolean_%s' % cp.id
                text_key = 'cp_text_%s' % cp.id
                numeric_key = 'cp_numeric_%s' % cp.id
                note_key = 'cp_note_%s' % cp.id
                cp_state_key = 'cp_state_%s' % cp.id
                cp_vals = {}
                if boolean_key in post:
                    cp_vals['boolean_value'] = post.get(boolean_key) == '1'
                elif 'cp_boolean_submitted_%s' % cp.id in post:
                    # checkbox not submitted means False
                    cp_vals['boolean_value'] = False
                if text_key in post:
                    cp_vals['text_value'] = post.get(text_key)
                if numeric_key in post:
                    try:
                        cp_vals['numeric_value'] = float(post.get(numeric_key) or 0)
                    except ValueError:
                        pass
                if note_key in post:
                    cp_vals['note'] = post.get(note_key)
                if cp_state_key in post:
                    cp_vals['state'] = post.get(cp_state_key)
                if cp_vals:
                    if 'state' not in cp_vals and cp.state == 'draft':
                        cp_vals['state'] = 'in_progress'
                    cp.sudo().write(cp_vals)
        return request.render('caqa_portal.portal_caqa_indicator_detail', {
            'indicator': indicator,
            'application': indicator.application_id,
            'breadcrumbs': [
                {'name': indicator.application_id.reference or indicator.application_id.name, 'url': '/my/caqa/application/%s' % indicator.application_id.id},
                {'name': indicator.code + ' ' + indicator.name, 'url': None},
            ],
        })

    @http.route(['/my/caqa/evidences'], type='http', auth='user', website=True)
    def portal_caqa_evidences(self, **kw):
        institution = self._get_caqa_institution()
        evidences = request.env['caqa.evidence'].sudo().search([('institution_id', '=', institution.id)]) if institution else request.env['caqa.evidence']
        return request.render('caqa_portal.portal_caqa_evidences', {'evidences': evidences, 'institution': institution})

    @http.route(['/my/caqa/evidence/<int:evidence_id>'], type='http', auth='user', website=True, methods=['GET', 'POST'])
    def portal_caqa_evidence_detail(self, evidence_id, **post):
        evidence = self._check_caqa_record('caqa.evidence', evidence_id)
        if hasattr(evidence, 'status_code'):
            return evidence
        if request.httprequest.method == 'POST':
            if 'summary' in post:
                evidence.sudo().write({'summary': post.get('summary')})
            current_version = evidence.current_version_id or request.env['caqa.evidence.version'].sudo().create({
                'evidence_id': evidence.id,
                'name': '%s V1' % evidence.name,
                'sequence_no': 1,
            })
            upload = request.httprequest.files.get('attachment')
            if upload:
                data = upload.read()
                ir_attachment = request.env['ir.attachment'].sudo().create({
                    'name': upload.filename,
                    # 'datas_fname': upload.filename,
                    'datas': base64.b64encode(data),
                    'mimetype': upload.mimetype,
                    'res_model': 'caqa.evidence',
                    'res_id': evidence.id,
                })
                request.env['caqa.evidence.attachment'].sudo().create({
                    'evidence_id': evidence.id,
                    'version_id': current_version.id,
                    'attachment_id': ir_attachment.id,
                    'attachment_state': 'draft',
                })
                evidence.sudo().write({'state': 'uploaded', 'current_version_id': current_version.id})
            if post.get('submit_now'):
                evidence.sudo().action_submit()
        return request.render('caqa_portal.portal_caqa_evidence_detail', {
            'evidence': evidence,
            'breadcrumbs': [
                {'name': evidence.application_id.reference or evidence.application_id.name, 'url': '/my/caqa/application/%s' % evidence.application_id.id},
                {'name': evidence.name, 'url': None},
            ],
        })

    @http.route(['/my/caqa/deficiencies'], type='http', auth='user', website=True)
    def portal_caqa_deficiencies(self, **kw):
        institution = self._get_caqa_institution()
        deficiencies = request.env['caqa.application.deficiency'].sudo().search([('application_id.institution_id', '=', institution.id)]) if institution else request.env['caqa.application.deficiency']
        return request.render('caqa_portal.portal_caqa_deficiencies', {'deficiencies': deficiencies})

    @http.route(['/my/caqa/deficiency/<int:deficiency_id>/respond'], type='http', auth='user', website=True, methods=['POST'])
    def portal_caqa_deficiency_respond(self, deficiency_id, **post):
        deficiency = self._check_caqa_record('caqa.application.deficiency', deficiency_id, 'application_id.institution_id')
        if hasattr(deficiency, 'status_code'):
            return deficiency
        response_text = post.get('institution_response', '').strip()
        if response_text:
            deficiency.sudo().write({'institution_response': response_text})
            deficiency.sudo().action_mark_responded()
        return request.redirect('/my/caqa/application/%s#deficiencies' % deficiency.application_id.id)

    @http.route(['/my/caqa/decisions'], type='http', auth='user', website=True)
    def portal_caqa_decisions(self, **kw):
        institution = self._get_caqa_institution()
        decisions = request.env['caqa.final.decision'].sudo().search([('institution_id', '=', institution.id)]) if institution else request.env['caqa.final.decision']
        followups = request.env['caqa.followup.plan'].sudo().search([('institution_id', '=', institution.id)]) if institution else request.env['caqa.followup.plan']
        return request.render('caqa_portal.portal_caqa_decisions', {'decisions': decisions, 'followups': followups})
