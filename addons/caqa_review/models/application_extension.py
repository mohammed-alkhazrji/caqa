from odoo import fields, models, api, _


class CaqaApplicationReviewExtension(models.Model):
    _inherit = 'caqa.application'

    # ── Relations ────────────────────────────────────────────────
    review_assignment_ids = fields.One2many('caqa.review.assignment', 'application_id')
    review_ids = fields.One2many('caqa.review', 'application_id')
    recommendation_ids = fields.One2many('caqa.recommendation', 'application_id')

    # ── Computed Counts (for Smart Buttons) ──────────────────────
    review_assignment_count = fields.Integer(compute='_compute_review_counts', store=True)
    review_total_count = fields.Integer(compute='_compute_review_counts', store=True)

    @api.depends('review_assignment_ids', 'review_ids')
    def _compute_review_counts(self):
        for rec in self:
            rec.review_assignment_count = len(rec.review_assignment_ids)
            rec.review_total_count = len(rec.review_ids)

    # ── Smart Button Actions ──────────────────────────────────────
    def action_view_review_assignments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Review Assignments'),
            'res_model': 'caqa.review.assignment',
            'view_mode': 'tree,form',
            'domain': [('application_id', '=', self.id)],
            'context': {'default_application_id': self.id},
        }

    def action_view_reviews(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reviews'),
            'res_model': 'caqa.review',
            'view_mode': 'tree,form',
            'domain': [('application_id', '=', self.id)],
            'context': {'default_application_id': self.id},
        }

    def action_create_review_assignment(self):
        """Quick-create a new Review Assignment linked to this application."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('New Review Assignment'),
            'res_model': 'caqa.review.assignment',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_application_id': self.id},
        }
