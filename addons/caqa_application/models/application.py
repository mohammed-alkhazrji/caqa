from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CaqaApplication(models.Model):
    _name = 'caqa.application'
    _description = 'Accreditation Application'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'intake_date desc, id desc'

    name = fields.Char(required=True, tracking=True)
    reference = fields.Char(default=lambda self: _('New'), copy=False, readonly=True, tracking=True)
    institution_id = fields.Many2one('res.partner', required=True, ondelete='restrict', domain=[('is_caqa_institution', '=', True)], tracking=True)
    institution_type_id = fields.Many2one(related='institution_id.institution_type_id', store=True, readonly=True)
    program_id = fields.Many2one('caqa.program', required=True, ondelete='restrict', tracking=True)
    eligibility_id = fields.Many2one('caqa.eligibility.request', ondelete='set null', tracking=True)
    profile_id = fields.Many2one('caqa.institution.profile', ondelete='set null', tracking=True)
    accreditation_type_id = fields.Many2one('caqa.accreditation.type', required=True, ondelete='restrict', tracking=True)
    cycle_id = fields.Many2one('caqa.accreditation.cycle', required=True, ondelete='restrict', tracking=True)
    standard_version_id = fields.Many2one('caqa.standard.version', required=True, ondelete='restrict', tracking=True)

    intake_date = fields.Date(default=fields.Date.context_today, tracking=True)
    submission_date = fields.Datetime(tracking=True)
    resubmission_date = fields.Datetime(tracking=True)
    initial_review_date = fields.Datetime(tracking=True)
    evaluation_date = fields.Datetime(tracking=True)
    site_visit_date = fields.Datetime(tracking=True)
    committee_review_date = fields.Datetime(tracking=True)
    decision_date = fields.Datetime(tracking=True)
    closed_date = fields.Datetime(tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('under_initial_review', 'Under Initial Review'),
        ('need_more_information', 'Need More Information'),
        ('resubmitted', 'Resubmitted'),
        ('under_evaluation', 'Under Evaluation'),
        ('under_site_visit', 'Under Site Visit'),
        ('under_committee_review', 'Under Committee Review'),
        ('approved', 'Approved'),
        ('conditional_approved', 'Conditionally Approved'),
        ('rejected', 'Rejected'),
        ('appealed', 'Appealed'),
        ('closed', 'Closed'),
    ], default='draft', required=True, tracking=True)

    formal_intake_user_id = fields.Many2one('res.users', tracking=True)
    case_owner_id = fields.Many2one('res.users', tracking=True)
    review_coordinator_id = fields.Many2one('res.users', tracking=True)
    applicant_contact_id = fields.Many2one('res.partner', tracking=True)

    summary_note = fields.Html()
    review_summary = fields.Html()
    decision_summary = fields.Html()

    completion_rate = fields.Float(compute='_compute_scores', store=True)
    readiness_score = fields.Float(compute='_compute_scores', store=True)

    chapter_ids = fields.One2many('caqa.application.chapter', 'application_id', string='Application Chapters')
    subchapter_ids = fields.One2many('caqa.application.subchapter', 'application_id', string='Application Subchapters')
    indicator_ids = fields.One2many('caqa.application.indicator', 'application_id', string='Application Indicators')
    checkpoint_ids = fields.One2many('caqa.application.checkpoint', 'application_id', string='Application Checkpoints')
    deficiency_ids = fields.One2many('caqa.application.deficiency', 'application_id', string='Deficiencies')
    state_history_ids = fields.One2many('caqa.application.state.history', 'application_id', string='State History')

    chapter_count = fields.Integer(compute='_compute_counts')
    indicator_count = fields.Integer(compute='_compute_counts')
    checkpoint_count = fields.Integer(compute='_compute_counts')
    deficiency_count = fields.Integer(compute='_compute_counts')
    open_deficiency_count = fields.Integer(compute='_compute_counts')
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        seq = self.env['ir.sequence']
        for rec in records:
            if rec.reference == _('New'):
                rec.reference = seq.next_by_code('caqa.application') or _('New')
            if not rec.profile_id:
                rec.profile_id = rec.institution_id.active_profile_id
            rec._log_state_change(False, rec.state, _('Application created'))
        return records

    @api.depends('indicator_ids.completion_rate', 'profile_id.profile_completion', 'eligibility_id.readiness_score')
    def _compute_scores(self):
        for rec in self:
            indicator_scores = rec.indicator_ids.mapped('completion_rate')
            rec.completion_rate = round(sum(indicator_scores) / len(indicator_scores), 2) if indicator_scores else 0.0
            profile_score = rec.profile_id.profile_completion or 0.0
            eligibility_score = rec.eligibility_id.readiness_score or 0.0
            rec.readiness_score = round((rec.completion_rate + profile_score + eligibility_score) / 3.0, 2)

    @api.depends('chapter_ids', 'indicator_ids', 'checkpoint_ids', 'deficiency_ids.state')
    def _compute_counts(self):
        for rec in self:
            rec.chapter_count = len(rec.chapter_ids)
            rec.indicator_count = len(rec.indicator_ids)
            rec.checkpoint_count = len(rec.checkpoint_ids)
            rec.deficiency_count = len(rec.deficiency_ids)
            rec.open_deficiency_count = len(rec.deficiency_ids.filtered(lambda d: d.state not in ('resolved', 'closed')))

    def _log_state_change(self, from_state, to_state, action_name, note=False):
        for rec in self:
            self.env['caqa.application.state.history'].create({
                'application_id': rec.id,
                'from_state': from_state,
                'to_state': to_state,
                'action_name': action_name,
                'changed_by': self.env.user.id,
                'note': note or '',
            })

    def _validate_submission(self):
        for rec in self:
            if not rec.indicator_ids:
                raise ValidationError(_('Application structure must be generated before submission.'))
            if rec.readiness_score < 40:
                raise ValidationError(_('Readiness score is too low for submission.'))
            if rec.indicator_ids.filtered(lambda i: i.response_state == 'draft'):
                raise ValidationError(_('All indicators must be started before submission.'))

    def action_generate_structure(self):
        for rec in self:
            if rec.chapter_ids:
                continue
            version = rec.standard_version_id
            for chapter in version.chapter_ids:
                chapter_line = self.env['caqa.application.chapter'].create({
                    'application_id': rec.id,
                    'chapter_id': chapter.id,
                    'name': chapter.name,
                    'code': chapter.code,
                    'weight': chapter.weight,
                })
                for subchapter in chapter.subchapter_ids:
                    subchapter_line = self.env['caqa.application.subchapter'].create({
                        'application_id': rec.id,
                        'chapter_line_id': chapter_line.id,
                        'subchapter_id': subchapter.id,
                        'name': subchapter.name,
                        'code': subchapter.code,
                        'weight': subchapter.weight,
                    })
                    for indicator in subchapter.indicator_ids:
                        indicator_line = self.env['caqa.application.indicator'].create({
                            'application_id': rec.id,
                            'chapter_line_id': chapter_line.id,
                            'subchapter_line_id': subchapter_line.id,
                            'indicator_id': indicator.id,
                            'name': indicator.name,
                            'code': indicator.code,
                            'indicator_type': indicator.indicator_type,
                            'weight': indicator.weight,
                        })
                        for checkpoint in indicator.checkpoint_ids:
                                self.env['caqa.application.checkpoint'].create({
                                    'application_id': rec.id,
                                    'chapter_line_id': chapter_line.id,
                                    'subchapter_line_id': subchapter_line.id,
                                    'application_indicator_id': indicator_line.id,
                                    'checkpoint_id': checkpoint.id,
                                    'name': checkpoint.name,
                                    'code': checkpoint.code,
                                    'weight': checkpoint.weight,
                                    'max_score': checkpoint.max_score,
                                })
            rec.state = 'in_progress'
            rec._log_state_change('draft', 'in_progress', _('Generate structure'))

    def action_formal_intake(self):
        for rec in self:
            old = rec.state
            rec.write({'state': 'in_progress', 'formal_intake_user_id': self.env.user.id})
            rec._log_state_change(old, rec.state, _('Formal intake'))

    def action_submit(self):
        self._validate_submission()
        for rec in self:
            old = rec.state
            rec.write({'state': 'submitted', 'submission_date': fields.Datetime.now()})
            rec._log_state_change(old, rec.state, _('Submit application'))
            rec.activity_schedule('mail.mail_activity_data_todo', user_id=rec.review_coordinator_id.id or self.env.user.id, summary=_('Initial review required'))

    def action_under_initial_review(self):
        for rec in self:
            old = rec.state
            rec.write({'state': 'under_initial_review', 'initial_review_date': fields.Datetime.now()})
            rec._log_state_change(old, rec.state, _('Move to initial review'))

    def action_need_more_information(self):
        for rec in self:
            old = rec.state
            rec.write({'state': 'need_more_information'})
            rec._log_state_change(old, rec.state, _('Request more information'))
            rec.activity_schedule('mail.mail_activity_data_todo', user_id=rec.case_owner_id.id or self.env.user.id, summary=_('Institution response required'))

    def action_resubmit(self):
        for rec in self:
            old = rec.state
            rec.write({'state': 'resubmitted', 'resubmission_date': fields.Datetime.now()})
            rec._log_state_change(old, rec.state, _('Resubmit application'))

    def action_under_evaluation(self):
        for rec in self:
            old = rec.state
            rec.write({'state': 'under_evaluation', 'evaluation_date': fields.Datetime.now()})
            rec._log_state_change(old, rec.state, _('Move to evaluation'))

    def action_under_site_visit(self):
        for rec in self:
            old = rec.state
            rec.write({'state': 'under_site_visit', 'site_visit_date': fields.Datetime.now()})
            rec._log_state_change(old, rec.state, _('Move to site visit'))

    def action_under_committee_review(self):
        for rec in self:
            old = rec.state
            rec.write({'state': 'under_committee_review', 'committee_review_date': fields.Datetime.now()})
            rec._log_state_change(old, rec.state, _('Move to committee review'))

    def action_approve(self):
        for rec in self:
            old = rec.state
            rec.write({'state': 'approved', 'decision_date': fields.Datetime.now()})
            rec._log_state_change(old, rec.state, _('Approve application'))

    def action_conditional_approve(self):
        for rec in self:
            old = rec.state
            rec.write({'state': 'conditional_approved', 'decision_date': fields.Datetime.now()})
            rec._log_state_change(old, rec.state, _('Conditional approval'))

    def action_reject(self):
        for rec in self:
            old = rec.state
            rec.write({'state': 'rejected', 'decision_date': fields.Datetime.now()})
            rec._log_state_change(old, rec.state, _('Reject application'))

    def action_mark_appealed(self):
        for rec in self:
            old = rec.state
            rec.write({'state': 'appealed'})
            rec._log_state_change(old, rec.state, _('Mark as appealed'))

    def action_close(self):
        for rec in self:
            old = rec.state
            rec.write({'state': 'closed', 'closed_date': fields.Datetime.now()})
            rec._log_state_change(old, rec.state, _('Close application'))

    def action_view_indicators(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Indicators'),
            'res_model': 'caqa.application.indicator',
            'view_mode': 'tree,form',
            'domain': [('application_id', '=', self.id)],
            'context': {'default_application_id': self.id},
        }

    def action_view_deficiencies(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Deficiencies'),
            'res_model': 'caqa.application.deficiency',
            'view_mode': 'tree,form',
            'domain': [('application_id', '=', self.id)],
            'context': {'default_application_id': self.id},
        }

    def action_view_state_history(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('State History'),
            'res_model': 'caqa.application.state.history',
            'view_mode': 'tree,form',
            'domain': [('application_id', '=', self.id)],
            'context': {'default_application_id': self.id},
        }


class CaqaApplicationDeficiency(models.Model):
    _name = 'caqa.application.deficiency'
    _description = 'Application Deficiency'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'severity desc, due_date, id'

    application_id = fields.Many2one('caqa.application', required=True, ondelete='cascade')
    institution_id = fields.Many2one(related='application_id.institution_id', store=True, readonly=True)
    application_indicator_id = fields.Many2one('caqa.application.indicator', ondelete='set null', domain="[('application_id', '=', application_id)]")
    title = fields.Char(required=True)
    description = fields.Html()
    severity = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='medium', required=True, tracking=True)
    state = fields.Selection([('open', 'Open'), ('responded', 'Responded'), ('resolved', 'Resolved'), ('closed', 'Closed')], default='open', required=True, tracking=True)
    assigned_user_id = fields.Many2one('res.users')
    due_date = fields.Date()
    institution_response = fields.Html()
    resolution_note = fields.Html()
    source_reference = fields.Char()
    attachment = fields.Binary(string='Attachment')
    attachment_name = fields.Char(string='Attachment Name')
    # ── Traceability fields ──────────────────────────────────────────────────
    source_note_id = fields.Many2one(
        'caqa.review.note', ondelete='set null', readonly=True,
        string='Source Review Note',
        help='The review note that generated this deficiency (if any).'
    )
    source_recommendation_id = fields.Many2one(
        'caqa.recommendation', ondelete='set null', readonly=True,
        string='Source Recommendation',
        help='The recommendation that generated this deficiency (if any).'
    )

    def action_mark_responded(self):
        self.write({'state': 'responded'})

    def action_resolve(self):
        self.write({'state': 'resolved'})

    def action_close(self):
        self.write({'state': 'closed'})


class CaqaApplicationStateHistory(models.Model):
    _name = 'caqa.application.state.history'
    _description = 'Application State History'
    _order = 'changed_on desc, id desc'

    application_id = fields.Many2one('caqa.application', required=True, ondelete='cascade')
    from_state = fields.Char()
    to_state = fields.Char()
    action_name = fields.Char(required=True)
    changed_by = fields.Many2one('res.users', default=lambda self: self.env.user)
    changed_on = fields.Datetime(default=fields.Datetime.now)
    note = fields.Text()
