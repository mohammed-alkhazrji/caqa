from odoo import fields, models, api


class CaqaApplicationReviewExtension(models.Model):
    _inherit = 'caqa.application'

    review_assignment_ids = fields.One2many('caqa.review.assignment', 'application_id')
    review_ids = fields.One2many('caqa.review', 'application_id')
    recommendation_ids = fields.One2many('caqa.recommendation', 'application_id')
    review_assignment_count = fields.Integer(compute='_compute_review_assignment_count')

    @api.depends('review_assignment_ids')
    def _compute_review_assignment_count(self):
        for rec in self:
            rec.review_assignment_count = len(rec.review_assignment_ids)

    def action_view_review_assignments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Review Assignments',
            'res_model': 'caqa.review.assignment',
            'view_mode': 'tree,form',
            'domain': [('application_id', '=', self.id)],
            'context': {'default_application_id': self.id},
        }
