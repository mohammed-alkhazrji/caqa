from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


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

    def action_create_deficiencies_from_notes(self):
        """Bulk: create a Deficiency for every public note that doesn't already have one."""
        self.ensure_one()
        created = 0
        for note in self.note_ids.filtered(lambda n: not n.internal_only and not n.deficiency_id):
            note.action_create_deficiency()
            created += 1
        if not created:
            raise UserError(_('All public notes already have a linked deficiency, or there are no public notes.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Deficiencies'),
            'res_model': 'caqa.application.deficiency',
            'view_mode': 'tree,form',
            'domain': [('application_id', '=', self.application_id.id)],
            'context': {'default_application_id': self.application_id.id},
        }

    def action_create_deficiencies_from_recommendations(self):
        """Bulk: create a Deficiency for every recommendation that doesn't already have one."""
        self.ensure_one()
        created = 0
        for rec in self.recommendation_ids.filtered(lambda r: not r.deficiency_id):
            rec.action_create_deficiency()
            created += 1
        if not created:
            raise UserError(_('All recommendations already have a linked deficiency, or there are no recommendations.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Deficiencies'),
            'res_model': 'caqa.application.deficiency',
            'view_mode': 'tree,form',
            'domain': [('application_id', '=', self.application_id.id)],
            'context': {'default_application_id': self.application_id.id},
        }


class CaqaReviewNote(models.Model):
    _name = 'caqa.review.note'
    _description = 'Review Note'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'severity desc, id'

    review_id = fields.Many2one('caqa.review', required=True, ondelete='cascade')
    application_id = fields.Many2one(related='review_id.application_id', store=True, readonly=True)
    application_indicator_id = fields.Many2one('caqa.application.indicator', ondelete='set null',
                                                domain="[('application_id', '=', application_id)]")
    title = fields.Char(required=True)
    note_type = fields.Selection([
        ('compliance', 'Compliance'), ('evidence', 'Evidence'),
        ('narrative', 'Narrative'), ('general', 'General')
    ], default='general')
    description = fields.Html()
    severity = fields.Selection([
        ('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')
    ], default='medium', tracking=True)
    state = fields.Selection([
        ('open', 'Open'), ('responded', 'Responded'), ('accepted', 'Accepted'),
        ('rejected', 'Rejected'), ('closed', 'Closed')
    ], default='open', tracking=True)
    institution_response = fields.Html()
    internal_only = fields.Boolean(default=False)
    # Traceability: link to the deficiency that was explicitly created from this note
    deficiency_id = fields.Many2one('caqa.application.deficiency', readonly=True, ondelete='set null',
                                     string='Linked Deficiency')

    # ── NO auto-creation of Deficiency in create() ──────────────────────────

    def action_create_deficiency(self):
        """Explicitly create one Deficiency for this Note. Prevents duplicates."""
        self.ensure_one()
        if self.deficiency_id:
            raise UserError(_(
                'A deficiency already exists for this note: %s\n'
                'To view it, open the linked deficiency.'
            ) % self.deficiency_id.display_name)

        deficiency = self.env['caqa.application.deficiency'].create({
            'application_id': self.application_id.id,
            'application_indicator_id': self.application_indicator_id.id if self.application_indicator_id else False,
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'source_reference': self.review_id.name,
            'source_note_id': self.id,
        })
        self.deficiency_id = deficiency.id

        return {
            'type': 'ir.actions.act_window',
            'name': _('Deficiency'),
            'res_model': 'caqa.application.deficiency',
            'res_id': deficiency.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_mark_responded(self):
        self.write({'state': 'responded'})

    def action_accept(self):
        self.write({'state': 'accepted'})
        self.mapped('deficiency_id').filtered(lambda d: d.state == 'responded').action_resolve()

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
    recommendation = fields.Selection([
        ('approve', 'Approve'),
        ('conditional', 'Conditional Approval'),
        ('reject', 'Reject'),
        ('site_visit', 'Need Site Visit'),
        ('more_info', 'Need More Information'),
    ], required=True)
    justification = fields.Html()
    state = fields.Selection([
        ('draft', 'Draft'), ('submitted', 'Submitted'),
        ('accepted', 'Accepted'), ('closed', 'Closed')
    ], default='draft')
    # Traceability: link to deficiency created from this recommendation
    deficiency_id = fields.Many2one('caqa.application.deficiency', readonly=True, ondelete='set null',
                                     string='Linked Deficiency')

    def action_create_deficiency(self):
        """Explicitly create one Deficiency for this Recommendation. Prevents duplicates."""
        self.ensure_one()
        if self.deficiency_id:
            raise UserError(_(
                'A deficiency already exists for this recommendation: %s'
            ) % self.deficiency_id.display_name)

        # Map recommendation type to a meaningful deficiency title
        rec_label = dict(self._fields['recommendation'].selection).get(self.recommendation, '')
        deficiency = self.env['caqa.application.deficiency'].create({
            'application_id': self.application_id.id,
            'title': _('Recommendation: %s') % rec_label,
            'description': self.justification,
            'severity': 'high' if self.recommendation in ('reject', 'site_visit') else 'medium',
            'source_reference': self.review_id.name,
            'source_recommendation_id': self.id,
        })
        self.deficiency_id = deficiency.id

        return {
            'type': 'ir.actions.act_window',
            'name': _('Deficiency'),
            'res_model': 'caqa.application.deficiency',
            'res_id': deficiency.id,
            'view_mode': 'form',
            'target': 'current',
        }

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
