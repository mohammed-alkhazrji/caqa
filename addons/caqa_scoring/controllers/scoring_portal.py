# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers.portal import CustomerPortal
import json

class CaqaCustomerPortalScore(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        # Count cycles where user is reviewer or manager
        domain = ['|', ('reviewer_ids', 'in', request.env.user.id), ('manager_id', '=', request.env.user.id)]
        cycle_count = request.env['caqa.score.cycle'].search_count(domain)
        values['cycle_count'] = cycle_count
        return values

class CaqaScoringPortal(http.Controller):

    @http.route(['/my/caqa/assessment'], type='http', auth="user", website=True)
    def portal_assessment_workspace(self, **kw):
        """ Main Dashboard for the Elite Reviewer Workspace """
        user_id = request.env.user.id
        domain = ['|', ('reviewer_ids', 'in', user_id), ('manager_id', '=', user_id)]
        cycles = request.env['caqa.score.cycle'].search(domain)
        
        my_lines = request.env['caqa.score.line'].search([
            ('cycle_id', 'in', cycles.ids),
            ('reviewer_id', '=', user_id)
        ])
        
        total_assignments = len(cycles)
        open_cycles = len(cycles.filtered(lambda c: c.state == 'in_progress'))
        completed_lines = len(my_lines.filtered(lambda l: l.rubric_level_id))
        total_lines = len(my_lines)
        completion_rate = round((completed_lines / total_lines * 100) if total_lines else 0)
        remaining_lines = total_lines - completed_lines

        values = {
            'cycles': cycles,
            'my_lines': my_lines,
            'total_assignments': total_assignments,
            'open_cycles': open_cycles,
            'completed_lines': completed_lines,
            'remaining_lines': remaining_lines,
            'completion_rate': completion_rate,
            'page_name': 'assessment_workspace_dashboard',
        }
        return request.render('caqa_scoring.portal_workspace_dashboard', values)

    @http.route(['/my/caqa/assessment/assignments'], type='http', auth="user", website=True)
    def portal_my_scoring_cycles(self, **kw):
        """ List of cycles where the current user is a reviewer or manager """
        domain = ['|', ('reviewer_ids', 'in', request.env.user.id), ('manager_id', '=', request.env.user.id)]
        cycles = request.env['caqa.score.cycle'].search(domain)
        values = {
            'cycles': cycles,
            'page_name': 'scoring_cycles',
        }
        return request.render('caqa_scoring.portal_workspace_assignments', values)

    @http.route(['/my/caqa/assessment/<int:cycle_id>'], type='http', auth="user", website=True)
    def portal_scoring_detail(self, cycle_id, **kw):
        """ Show the detailed focus mode grid for a specific cycle """
        cycle = request.env['caqa.score.cycle'].browse(cycle_id)
        is_manager = cycle.manager_id == request.env.user
        
        if not cycle.exists() or (request.env.user not in cycle.reviewer_ids and not is_manager):
            raise AccessError(_("You don't have access to this assessment."))

        # Normal reviewers only see their lines. Managers see all lines.
        domain = [('cycle_id', '=', cycle.id)]
        if not is_manager:
            domain.append(('reviewer_id', '=', request.env.user.id))
            
        lines = request.env['caqa.score.line'].search(domain)
        
        grouped_lines = {}
        for line in lines:
            crit = line.criterion_id
            if crit not in grouped_lines:
                grouped_lines[crit] = []
            grouped_lines[crit].append(line)

        rubrics = request.env['caqa.score.rubric.level'].search([('rubric_id.is_default', '=', True)])
        if not rubrics:
            rubrics = request.env['caqa.score.rubric.level'].search([], order='sequence, value_numeric')

        # Determine if the current reviewer has submitted
        my_submit_status = False
        if not is_manager:
            my_lines = lines.filtered(lambda l: l.reviewer_id == request.env.user)
            my_submit_status = all(l.reviewer_state == 'completed' for l in my_lines) if my_lines else False

        # Preload all application evidence for inline tabs/collapses
        all_evidences = request.env['caqa.evidence'].search([
            ('application_id', '=', cycle.application_id.id),
            ('state', 'not in', ('draft', 'rejected', 'closed'))
        ])
        
        evidence_by_indicator = {}
        for ev in all_evidences:
            if ev.application_indicator_id and ev.application_indicator_id.indicator_id:
                ind_id = ev.application_indicator_id.indicator_id.id
                if ind_id not in evidence_by_indicator:
                    evidence_by_indicator[ind_id] = []
                evidence_by_indicator[ind_id].append(ev)

        values = {
            'cycle': cycle,
            'grouped_lines': grouped_lines.items(),
            'rubrics': rubrics,
            'page_name': 'scoring_detail',
            'is_editable': cycle.state == 'in_progress' and not my_submit_status and not is_manager,
            'is_manager': is_manager,
            'my_submit_status': my_submit_status,
            'evidence_data': evidence_by_indicator,
        }
        return request.render('caqa_scoring.portal_workspace_detail', values)

    @http.route(['/my/caqa/assessment/<int:cycle_id>/save'], type='json', auth="user")
    def portal_scoring_save(self, cycle_id, scores=None, **kw):
        """ Save draft scores via AJAX, enforces justification on low scores """
        cycle = request.env['caqa.score.cycle'].browse(cycle_id)
        if not cycle.exists() or request.env.user not in cycle.reviewer_ids:
            return {'error': 'Access Denied'}
            
        if cycle.state != 'in_progress':
            return {'error': 'Cycle is not in progress.'}
        if scores:
            for score in scores:
                line_id = score.get('line_id')
                rubric_level_id = score.get('rubric_level_id')
                justification = score.get('justification')
                
                line = request.env['caqa.score.line'].browse(int(line_id))
                if not line.exists():
                    return {'error': f'Line ID {line_id} not found in database!'}
                

                # Rule: If score <= 2, justification is mandatory
                if rubric_level_id:
                    rubric = request.env['caqa.score.rubric.level'].browse(int(rubric_level_id))
                    if rubric.value_numeric <= 2 and not justification:
                        return {'error': f'Justification required for "{line.indicator_id.name}" due to low score.'}

                try:
                    if rubric_level_id:

                        # Fetch the actual numeric score for Moderation
                        raw_val = request.env['caqa.score.rubric.level'].browse(int(rubric_level_id)).value_numeric
                        
                        request.env['caqa.score.moderation'].sudo().create({
                            'cycle_id': cycle.id,
                            'indicator_id': line.indicator_id.id,
                            'reviewer_1_score': raw_val,
                            'reviewer_2_score': 0,
                            'moderation_decision': 'Auto-Generated for Manager Review',
                            'final_agreed_score': 0,
                        })
                except Exception as e:
                    return {'error': str(e)}

        return {'success': True}

    @http.route(['/my/caqa/assessment/<int:cycle_id>/submit'], type='http', auth="user", website=True)
    def portal_scoring_submit(self, cycle_id, **kw):
        """ Deprecated: Forwarded directly back to assessment """
        return request.redirect('/my/caqa/assessment?success=submitted')

    @http.route(['/my/caqa/assessment/<int:cycle_id>/evidence/<int:indicator_id>'], type='http', auth="user", website=True)
    def portal_scoring_evidence_view(self, cycle_id, indicator_id, **kw):
        """ Quick popup view for Evidence related to a specific Indicator in a Cycle """
        cycle = request.env['caqa.score.cycle'].browse(cycle_id)
        if not cycle.exists() or (request.env.user not in cycle.reviewer_ids and cycle.manager_id != request.env.user):
            raise AccessError(_("You don't have access to this assessment."))

        indicator = request.env['caqa.standard.indicator'].browse(indicator_id)
        
        evidences = request.env['caqa.evidence'].search([
            ('application_id', '=', cycle.application_id.id),
            ('application_indicator_id.indicator_id', '=', indicator.id),
            ('state', 'not in', ('draft', 'rejected', 'closed'))
        ])

        values = {
            'cycle': cycle,
            'indicator': indicator,
            'evidences': evidences,
            'page_name': 'scoring_evidence_popup',
        }
        return request.render('caqa_scoring.portal_workspace_evidence_popup', values)
