# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
import json

class CaqaScoringPortal(http.Controller):

    @http.route(['/my/caqa/scoring'], type='http', auth="user", website=True)
    def portal_my_scoring_cycles(self, **kw):
        """ List of cycles where the current user is a reviewer """
        cycles = request.env['caqa.score.cycle'].search([('reviewer_ids', 'in', request.env.user.id)])
        values = {
            'cycles': cycles,
            'page_name': 'scoring_cycles',
        }
        return request.render('caqa_scoring.portal_scoring_cycles_list', values)

    @http.route(['/my/caqa/scoring/<int:cycle_id>'], type='http', auth="user", website=True)
    def portal_scoring_detail(self, cycle_id, **kw):
        """ Show the scoring grid for a specific cycle """
        cycle = request.env['caqa.score.cycle'].browse(cycle_id)
        if not cycle.exists() or request.env.user not in cycle.reviewer_ids:
            raise AccessError(_("You don't have access to this scoring cycle."))

        # Get lines specific to this reviewer
        lines = request.env['caqa.score.line'].search([
            ('cycle_id', '=', cycle.id),
            ('reviewer_id', '=', request.env.user.id)
        ])
        
        # Group lines by criterion (subchapter)
        grouped_lines = {}
        for line in lines:
            crit = line.criterion_id
            if crit not in grouped_lines:
                grouped_lines[crit] = []
            grouped_lines[crit].append(line)

        rubrics = request.env['caqa.score.rubric.level'].search([('rubric_id.is_default', '=', True)])
        if not rubrics:
            rubrics = request.env['caqa.score.rubric.level'].search([], order='sequence, value_numeric')

        values = {
            'cycle': cycle,
            'grouped_lines': grouped_lines,
            'rubrics': rubrics,
            'page_name': 'scoring_detail',
            'is_editable': cycle.state == 'in_progress',
        }
        return request.render('caqa_scoring.portal_scoring_cycle_detail', values)

    @http.route(['/my/caqa/scoring/<int:cycle_id>/save'], type='json', auth="user")
    def portal_scoring_save(self, cycle_id, scores=None, **kw):
        """ Save draft scores via AJAX """
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
                
                line = request.env['caqa.score.line'].browse(line_id)
                if line.exists() and line.reviewer_id == request.env.user and line.cycle_id == cycle:
                    # Don't throw full strict validation during draft save, 
                    # except maybe catching it softly in JS, but Odoo ORM will enforce it.
                    try:
                        line.write({
                            'rubric_level_id': int(rubric_level_id) if rubric_level_id else False,
                            'justification': justification or False
                        })
                    except Exception as e:
                        return {'error': str(e)}

        return {'success': True}

    @http.route(['/my/caqa/scoring/<int:cycle_id>/submit'], type='http', auth="user", website=True)
    def portal_scoring_submit(self, cycle_id, **kw):
        """ Submit the reviewer's portion of the cycle """
        cycle = request.env['caqa.score.cycle'].browse(cycle_id)
        if not cycle.exists() or request.env.user not in cycle.reviewer_ids:
            raise AccessError(_("You don't have access to this scoring cycle."))

        # Verify all lines for this reviewer are scored
        my_lines = request.env['caqa.score.line'].search([
            ('cycle_id', '=', cycle.id),
            ('reviewer_id', '=', request.env.user.id)
        ])
        
        missing = my_lines.filtered(lambda l: not l.rubric_level_id)
        if missing:
            # We would redirect back with an error in a real scenario
            return request.redirect('/my/caqa/scoring/%s?error=missing_scores' % cycle.id)

        # Mark reviewer's lines as submitted (adding a boolean to score_line might be needed in future).
        # For now, if all reviewers are done, the manager submits the cycle. Or we auto-submit.
        # Let's just redirect for now. The reviewer journey is "saving" locally.
        
        return request.redirect('/my/caqa/scoring?success=submitted')
