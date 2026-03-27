from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CaqaReviewAssignment(models.Model):
    _name = 'caqa.review.assignment'
    _description = 'Review Assignment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'due_date, id'

    reference = fields.Char(default=lambda self: _('New'), copy=False, readonly=True, tracking=True)
    application_id = fields.Many2one('caqa.application', required=True, ondelete='cascade', tracking=True)
    institution_id = fields.Many2one(related='application_id.institution_id', store=True, readonly=True)
    reviewer_id = fields.Many2one('res.users', required=True, tracking=True)
    role = fields.Selection([('reviewer', 'Reviewer'), ('senior', 'Senior Reviewer')], default='reviewer', required=True)
    due_date = fields.Date()
    state = fields.Selection([('new', 'New'), ('in_progress', 'In Progress'), ('submitted', 'Submitted'), ('closed', 'Closed')], default='new', tracking=True)
    review_ids = fields.One2many('caqa.review', 'assignment_id')
    review_count = fields.Integer(compute='_compute_review_count')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        seq = self.env['ir.sequence']
        for rec in records:
            if rec.reference == _('New'):
                rec.reference = seq.next_by_code('caqa.review.assignment') or _('New')
        return records

    @api.depends('review_ids')
    def _compute_review_count(self):
        for rec in self:
            rec.review_count = len(rec.review_ids)

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_close(self):
        self.write({'state': 'closed'})


class CaqaReview(models.Model):
    _name = 'caqa.review'
    _description = 'Review'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(required=True)
    assignment_id = fields.Many2one('caqa.review.assignment', required=True, ondelete='cascade', tracking=True)
    application_id = fields.Many2one(related='assignment_id.application_id', store=True, readonly=True)
    reviewer_id = fields.Many2one(related='assignment_id.reviewer_id', store=True, readonly=True)
    stage = fields.Selection([('initial', 'Initial'), ('technical', 'Technical'), ('moderation', 'Moderation')], default='technical', tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('in_progress', 'In Progress'), ('submitted', 'Submitted'), ('moderated', 'Moderated'), ('closed', 'Closed')], default='draft', tracking=True)
    score = fields.Float()
    summary = fields.Html()
    note_ids = fields.One2many('caqa.review.note', 'review_id')
    recommendation_ids = fields.One2many('caqa.recommendation', 'review_id')

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_submit(self):
        for rec in self:
            rec.state = 'submitted'
            if rec.summary:
                rec.application_id.review_summary = rec.summary

    def action_moderate(self):
        self.write({'state': 'moderated'})

    def action_close(self):
        self.write({'state': 'closed'})


class CaqaReviewNote(models.Model):
    _name = 'caqa.review.note'
    _description = 'Review Note'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'severity desc, id'

    review_id = fields.Many2one('caqa.review', required=True, ondelete='cascade')
    application_id = fields.Many2one(related='review_id.application_id', store=True, readonly=True)
    application_indicator_id = fields.Many2one('caqa.application.indicator', ondelete='set null')
    title = fields.Char(required=True)
    note_type = fields.Selection([('compliance', 'Compliance'), ('evidence', 'Evidence'), ('narrative', 'Narrative'), ('general', 'General')], default='general')
    description = fields.Html()
    severity = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='medium', tracking=True)
    state = fields.Selection([('open', 'Open'), ('responded', 'Responded'), ('accepted', 'Accepted'), ('rejected', 'Rejected'), ('closed', 'Closed')], default='open', tracking=True)
    institution_response = fields.Html()
    internal_only = fields.Boolean(default=False)
    deficiency_id = fields.Many2one('caqa.application.deficiency', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.severity in ('medium', 'high', 'critical') and not rec.internal_only and not rec.deficiency_id:
                deficiency = self.env['caqa.application.deficiency'].create({
                    'application_id': rec.application_id.id,
                    'application_indicator_id': rec.application_indicator_id.id,
                    'title': rec.title,
                    'description': rec.description,
                    'severity': rec.severity,
                    'source_reference': rec.review_id.name,
                })
                rec.deficiency_id = deficiency.id
        return records

    def action_mark_responded(self):
        self.write({'state': 'responded'})

    def action_accept(self):
        self.write({'state': 'accepted'})
        self.mapped('deficiency_id').action_resolve()

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_close(self):
        self.write({'state': 'closed'})


class CaqaRecommendation(models.Model):
    _name = 'caqa.recommendation'
    _description = 'Review Recommendation'
    _order = 'create_date desc, id desc'

    review_id = fields.Many2one('caqa.review', required=True, ondelete='cascade')
    application_id = fields.Many2one(related='review_id.application_id', store=True, readonly=True)
    recommendation = fields.Selection([('approve', 'Approve'), ('conditional', 'Conditional Approval'), ('reject', 'Reject'), ('site_visit', 'Need Site Visit'), ('more_info', 'Need More Information')], required=True)
    justification = fields.Html()
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('accepted', 'Accepted'), ('closed', 'Closed')], default='draft')

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_accept(self):
        self.write({'state': 'accepted'})

    def action_close(self):
        self.write({'state': 'closed'})


class CaqaModerationLog(models.Model):
    _name = 'caqa.moderation.log'
    _description = 'Moderation Log'
    _order = 'create_date desc, id desc'

    application_id = fields.Many2one('caqa.application', required=True, ondelete='cascade')
    review_id = fields.Many2one('caqa.review', ondelete='set null')
    senior_reviewer_id = fields.Many2one('res.users')
    action = fields.Char(required=True)
    note = fields.Text()
