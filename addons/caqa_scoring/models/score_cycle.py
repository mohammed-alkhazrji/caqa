# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class CaqaScoreCycle(models.Model):
    _name = 'caqa.score.cycle'
    _description = 'Evaluation Score Cycle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    application_id = fields.Many2one('caqa.application', string='Application', required=True, ondelete='cascade', tracking=True)
    program_id = fields.Many2one('caqa.program', string='Program', related='application_id.program_id', store=True)
    standard_version_id = fields.Many2one('caqa.standard.version', string='Standard Version', required=True)
    
    cycle_type = fields.Selection([
        ('self_assessment', 'Self Assessment'),
        ('desk_review', 'Desk Review'),
        ('site_visit', 'Site Visit'),
        ('moderation', 'Moderation'),
        ('final_committee', 'Final Committee')
    ], string='Cycle Type', required=True, default='desk_review', tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('moderated', 'Moderated'),
        ('frozen', 'Frozen')
    ], string='Status', required=True, default='draft', tracking=True)

    reviewer_ids = fields.Many2many('res.users', 'caqa_score_cycle_reviewer_rel', 'cycle_id', 'user_id', string='Reviewers')
    manager_id = fields.Many2one('res.users', string='Cycle Manager', tracking=True)
    line_ids = fields.One2many('caqa.score.line', 'cycle_id', string='Score Lines')
    moderation_ids = fields.One2many('caqa.score.moderation', 'cycle_id', string='Moderation Logs')
    snapshot_id = fields.Many2one('caqa.score.snapshot', string='Frozen Snapshot', readonly=True)

    # Computed Overall Results
    final_score = fields.Float(string='Final Score', compute='_compute_final_score', store=True)
    decision_status = fields.Selection([
        ('eligible', 'Eligible'),
        ('conditionally_eligible', 'Conditionally Eligible'),
        ('not_eligible', 'Not Eligible'),
        ('needs_moderation', 'Needs Moderation'),
        ('incomplete', 'Incomplete')
    ], string='Decision Status', compute='_compute_decision_status', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('caqa.score.cycle') or _('New')
        return super().create(vals_list)

    @api.depends('line_ids.weighted_score', 'line_ids.indicator_weight', 'state')
    def _compute_final_score(self):
        for rec in self:
            total_weighted = sum(rec.line_ids.mapped('weighted_score'))
            total_weight = sum(rec.line_ids.mapped('indicator_weight'))
            rec.final_score = (total_weighted / total_weight) if total_weight > 0 else 0.0

    @api.depends('final_score', 'state', 'line_ids.variance_flag')
    def _compute_decision_status(self):
        for rec in self:
            if rec.state in ['draft', 'in_progress']:
                rec.decision_status = 'incomplete'
            elif any(line.variance_flag for line in rec.line_ids):
                rec.decision_status = 'needs_moderation'
            else:
                # Basic mock logic for Phase 1. Real logic will depend on thresholds.
                if rec.final_score >= 80:
                    rec.decision_status = 'eligible'
                elif rec.final_score >= 60:
                    rec.decision_status = 'conditionally_eligible'
                else:
                    rec.decision_status = 'not_eligible'

    def action_start_progress(self):
        self.ensure_one()
        if not self.reviewer_ids:
            raise UserError(_('You must assign at least one reviewer before starting the scoring cycle.'))
            
        # Fetch indicators for the configured standard version
        indicators = self.env['caqa.standard.indicator'].search([
            ('subchapter_id.chapter_id.version_id', '=', self.standard_version_id.id)
        ])
        if not indicators:
            raise UserError(_('No indicators found for the selected Standard Version.'))
            
        # Generate lines for each reviewer & indicator combination
        line_vals = []
        for reviewer in self.reviewer_ids:
            for ind in indicators:
                line_vals.append({
                    'cycle_id': self.id,
                    'reviewer_id': reviewer.id,
                    'indicator_id': ind.id,
                })
                
        if line_vals:
            self.env['caqa.score.line'].create(line_vals)
            
        self.state = 'in_progress'

    def action_submit(self):
        self.ensure_one()
        # Ensure all lines are scored
        if any(not line.rubric_level_id for line in self.line_ids):
            raise UserError(_('All indicators must be scored before submitting.'))
            
        # Variance Detection Logic (Basic implementation)
        if len(self.reviewer_ids) > 1:
            indicators = self.line_ids.mapped('indicator_id')
            moderation_vals = []
            for ind in indicators:
                lines = self.line_ids.filtered(lambda l: l.indicator_id.id == ind.id)
                scores = lines.mapped('raw_score')
                if scores and max(scores) - min(scores) > 1:  # Simple threshold > 1 point variance
                    for line in lines:
                        line.variance_flag = True
                    # In a real implementation we would dynamically link the exact reviewers,
                    # for now we'll create a single moderation record to track it
                    if len(scores) >= 2:
                        moderation_vals.append({
                            'cycle_id': self.id,
                            'indicator_id': ind.id,
                            'reviewer_1_score': scores[0],
                            'reviewer_2_score': scores[1],
                            'moderation_decision': 'Pending Review',
                            'final_agreed_score': 0,
                        })
            if moderation_vals:
                self.env['caqa.score.moderation'].create(moderation_vals)
                
        self.state = 'submitted'

    def action_finalize_moderation(self):
        self.ensure_one()
        if any(line.variance_flag for line in self.line_ids):
            raise UserError(_('You cannot finalize moderation. Some indicators still have unresolved variances.'))
        self.state = 'moderated'

    def action_freeze(self):
        self.ensure_one()
        if self.state not in ['submitted', 'moderated']:
            raise UserError(_('You cannot freeze a cycle that is not submitted or moderated.'))
        if any(line.variance_flag for line in self.line_ids):
            raise UserError(_('Please resolve all variances before freezing the cycle.'))
            
        import json
        snapshot_dict = {
            'cycle_ref': self.name,
            'application_ref': self.application_id.name,
            'standard_version': self.standard_version_id.name,
            'final_score': self.final_score,
            'lines': []
        }
        for line in self.line_ids:
            snapshot_dict['lines'].append({
                'indicator': line.indicator_id.name,
                'weight': line.indicator_weight,
                'raw_score': line.raw_score,
                'moderated_score': line.moderated_score,
                'final_score_used': line.final_score_used,
                'weighted_score': line.weighted_score,
                'justification': line.justification,
                'reviewer': line.reviewer_id.name,
            })
            
        snapshot = self.env['caqa.score.snapshot'].create({
            'application_id': self.application_id.id,
            'cycle_id': self.id,
            'snapshot_data': json.dumps(snapshot_dict, ensure_ascii=False, indent=2)
        })
        
        self.snapshot_id = snapshot.id
        self.state = 'frozen'
        self._compute_decision_status()
