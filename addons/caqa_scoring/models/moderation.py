# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class CaqaScoreModeration(models.Model):
    _name = 'caqa.score.moderation'
    _description = 'Score Variance Moderation'
    _order = 'moderated_at desc, id desc'

    cycle_id = fields.Many2one('caqa.score.cycle', string='Cycle', required=True, ondelete='cascade')
    indicator_id = fields.Many2one('caqa.standard.indicator', string='Indicator', required=True)
    
    # Store scores directly to log the variance at the time of creation
    reviewer_1_score = fields.Integer(string='Reviewer 1 Score')
    reviewer_2_score = fields.Integer(string='Reviewer 2 Score')
    variance_value = fields.Integer(string='Variance', compute='_compute_variance', store=True)

    moderation_decision = fields.Text(string='Moderation Decision/Notes', required=True)
    final_agreed_score = fields.Integer(string='Final Agreed Score', required=True)
    
    moderator_id = fields.Many2one('res.users', string='Moderated By', default=lambda self: self.env.user)
    moderated_at = fields.Datetime(string='Moderated At', default=fields.Datetime.now)

    @api.depends('reviewer_1_score', 'reviewer_2_score')
    def _compute_variance(self):
        for record in self:
            record.variance_value = abs(record.reviewer_1_score - record.reviewer_2_score)

    def action_apply_moderation(self):
        """
        Apply the final_agreed_score to the corresponding caqa.score.line records
        and clear the variance_flag.
        """
        for record in self:
            lines = self.env['caqa.score.line'].search([
                ('cycle_id', '=', record.cycle_id.id),
                ('indicator_id', '=', record.indicator_id.id)
            ])
            lines.write({
                'moderated_score': record.final_agreed_score,
                'variance_flag': False,
            })
