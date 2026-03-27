from odoo import api, fields, models


class CaqaReviewerCockpit(models.TransientModel):
    _name = 'caqa.reviewer.cockpit'
    _description = 'Reviewer Cockpit'

    reviewer_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    assignment_count = fields.Integer(compute='_compute_values')
    submitted_count = fields.Integer(compute='_compute_values')
    open_note_count = fields.Integer(compute='_compute_values')
    summary_html = fields.Html(compute='_compute_values')

    def _compute_values(self):
        Assignment = self.env['caqa.review.assignment']
        Note = self.env['caqa.review.note']
        for rec in self:
            rec.assignment_count = Assignment.search_count([('reviewer_id', '=', rec.reviewer_id.id)])
            rec.submitted_count = Assignment.search_count([('reviewer_id', '=', rec.reviewer_id.id), ('state', '=', 'submitted')])
            rec.open_note_count = Note.search_count([('review_id.reviewer_id', '=', rec.reviewer_id.id), ('state', 'not in', ['accepted', 'closed'])])
            rec.summary_html = (
                '<div class="row g-3">'
                '<div class="col-4"><div class="alert alert-primary mb-0"><strong>%s</strong><br/>Assignments</div></div>'
                '<div class="col-4"><div class="alert alert-success mb-0"><strong>%s</strong><br/>Submitted</div></div>'
                '<div class="col-4"><div class="alert alert-warning mb-0"><strong>%s</strong><br/>Open Notes</div></div>'
                '</div>'
            ) % (rec.assignment_count, rec.submitted_count, rec.open_note_count)

    def action_open_assignments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Review Assignments',
            'res_model': 'caqa.review.assignment',
            'view_mode': 'tree,form',
            'domain': [('reviewer_id', '=', self.reviewer_id.id)],
        }
