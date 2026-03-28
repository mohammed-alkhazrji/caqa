# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CaqaScoreLine(models.Model):
    _name = 'caqa.score.line'
    _description = 'Evaluation Score Line'
    _order = 'cycle_id, indicator_id'

    cycle_id = fields.Many2one('caqa.score.cycle', string='Cycle', required=True, ondelete='cascade')
    reviewer_id = fields.Many2one('res.users', string='Reviewer', required=True, default=lambda self: self.env.user)
    
    # Target Context
    indicator_id = fields.Many2one('caqa.standard.indicator', string='Indicator', required=True)
    criterion_id = fields.Many2one('caqa.standard.subchapter', string='Criterion (Subchapter)', related='indicator_id.subchapter_id', store=True)
    
    # Scoring
    rubric_level_id = fields.Many2one('caqa.score.rubric.level', string='Rubric Level')
    raw_score = fields.Integer(string='Raw Score', related='rubric_level_id.value_numeric', store=True)
    indicator_weight = fields.Float(string='Weight', related='indicator_id.weight', store=True)
    weighted_score = fields.Float(string='Weighted Score', compute='_compute_weighted_score', store=True)
    
    # Details
    justification = fields.Text(string='Justification')
    evidence_link_count = fields.Integer(string='Evidence Count', compute='_compute_evidence_count')
    is_critical_indicator = fields.Boolean(string='Is Critical', related='indicator_id.is_critical', store=True)
    
    # Moderation & States
    variance_flag = fields.Boolean(string='Variance Detected', default=False)
    state = fields.Selection(related='cycle_id.state', store=True)
    moderated_score = fields.Integer(string='Moderated Score')
    final_score_used = fields.Integer(string='Final Score Used', compute='_compute_final_score_used', store=True)

    @api.depends('raw_score', 'indicator_weight')
    def _compute_weighted_score(self):
        for line in self:
            line.weighted_score = (line.raw_score or 0) * (line.indicator_weight or 1.0)

    @api.depends('raw_score', 'moderated_score')
    def _compute_final_score_used(self):
        for line in self:
            line.final_score_used = line.moderated_score if line.moderated_score else line.raw_score

    def _compute_evidence_count(self):
        """
        In a real implementation, this would count evidence linked in caqa_sar 
        associated with this indicator in the context of the application.
        """
        for line in self:
            line.evidence_link_count = 0

    @api.constrains('rubric_level_id', 'justification')
    def _check_justification(self):
        for line in self:
            if line.rubric_level_id and line.rubric_level_id.value_numeric <= 2 and not line.justification:
                raise ValidationError(_("A justification is required when scoring an indicator level 2 or below."))
                
    @api.constrains('cycle_id', 'reviewer_id', 'indicator_id')
    def _check_unique_reviewer_indicator(self):
        for line in self:
            domain = [
                ('cycle_id', '=', line.cycle_id.id),
                ('reviewer_id', '=', line.reviewer_id.id),
                ('indicator_id', '=', line.indicator_id.id),
                ('id', '!=', line.id)
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(_("A reviewer can only score an indicator once per cycle."))
