from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CaqaCommitteeSession(models.Model):
    _name = 'caqa.committee.session'
    _description = 'Committee Session'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'session_date desc, id desc'

    reference = fields.Char(default=lambda self: _('New'), copy=False, readonly=True, tracking=True)
    name = fields.Char(required=True, tracking=True)
    session_date = fields.Datetime(required=True, tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('in_session', 'In Session'), ('completed', 'Completed'), ('closed', 'Closed')], default='draft', tracking=True)
    note = fields.Html()
    member_ids = fields.One2many('caqa.committee.member', 'session_id')
    decision_pack_ids = fields.One2many('caqa.decision.pack', 'session_id')
    vote_ids = fields.One2many('caqa.committee.vote', 'session_id')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        seq = self.env['ir.sequence']
        for rec in records:
            if rec.reference == _('New'):
                rec.reference = seq.next_by_code('caqa.committee.session') or _('New')
        return records

    def action_start(self):
        self.write({'state': 'in_session'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_close(self):
        self.write({'state': 'closed'})


class CaqaCommitteeMember(models.Model):
    _name = 'caqa.committee.member'
    _description = 'Committee Member'
    _order = 'session_id, id'

    session_id = fields.Many2one('caqa.committee.session', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', required=True)
    role = fields.Selection([('chair', 'Chair'), ('member', 'Member'), ('secretary', 'Secretary')], default='member')
    present = fields.Boolean(default=True)
    vote_weight = fields.Float(default=1.0)


class CaqaDecisionPack(models.Model):
    _name = 'caqa.decision.pack'
    _description = 'Decision Pack'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(required=True)
    application_id = fields.Many2one('caqa.application', required=True, ondelete='cascade')
    session_id = fields.Many2one('caqa.committee.session', ondelete='set null')
    review_summary = fields.Html()
    site_visit_summary = fields.Html()
    final_recommendation = fields.Selection([('approve', 'Approve'), ('conditional', 'Conditional'), ('reject', 'Reject'), ('suspend', 'Suspend')], default='approve')
    state = fields.Selection([('draft', 'Draft'), ('ready', 'Ready'), ('presented', 'Presented'), ('finalized', 'Finalized')], default='draft')

    def action_ready(self):
        self.write({'state': 'ready'})

    def action_present(self):
        self.write({'state': 'presented'})

    def action_finalize(self):
        self.write({'state': 'finalized'})


class CaqaCommitteeVote(models.Model):
    _name = 'caqa.committee.vote'
    _description = 'Committee Vote'
    _order = 'session_id, id'

    session_id = fields.Many2one('caqa.committee.session', required=True, ondelete='cascade')
    application_id = fields.Many2one('caqa.application', required=True, ondelete='cascade')
    member_id = fields.Many2one('caqa.committee.member', required=True, ondelete='cascade')
    vote = fields.Selection([('approve', 'Approve'), ('conditional', 'Conditional'), ('reject', 'Reject')], required=True)
    justification = fields.Text()


class CaqaFinalDecision(models.Model):
    _name = 'caqa.final.decision'
    _description = 'Final Decision'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'decision_date desc, id desc'

    reference = fields.Char(default=lambda self: _('New'), copy=False, readonly=True, tracking=True)
    application_id = fields.Many2one('caqa.application', required=True, ondelete='cascade', tracking=True)
    institution_id = fields.Many2one(related='application_id.institution_id', store=True, readonly=True)
    session_id = fields.Many2one('caqa.committee.session', ondelete='set null')
    decision_pack_id = fields.Many2one('caqa.decision.pack', ondelete='set null')
    decision = fields.Selection([('approved', 'Approved'), ('conditional_approved', 'Conditionally Approved'), ('rejected', 'Rejected'), ('suspended', 'Suspended')], default='approved', tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('issued', 'Issued'), ('notified', 'Notified'), ('closed', 'Closed')], default='draft', tracking=True)
    decision_date = fields.Date(default=fields.Date.context_today)
    validity_start = fields.Date()
    validity_end = fields.Date()
    conditions_html = fields.Html()
    rejection_reason = fields.Html()
    letter_html = fields.Html()
    appeal_deadline = fields.Date()
    followup_required = fields.Boolean(default=False)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        seq = self.env['ir.sequence']
        for rec in records:
            if rec.reference == _('New'):
                rec.reference = seq.next_by_code('caqa.final.decision') or _('New')
        return records

    def action_issue(self):
        for rec in self:
            if rec.decision == 'conditional_approved' and not rec.conditions_html:
                raise ValidationError(_('Conditional approval requires conditions.'))
            if rec.decision == 'rejected' and not rec.rejection_reason:
                raise ValidationError(_('Rejection requires a reason.'))
            rec.state = 'issued'
            rec.application_id.decision_summary = rec.letter_html or rec.conditions_html or rec.rejection_reason
            if rec.decision == 'approved':
                rec.application_id.action_approve()
            elif rec.decision == 'conditional_approved':
                rec.application_id.action_conditional_approve()
            elif rec.decision == 'rejected':
                rec.application_id.action_reject()

    def action_notify(self):
        self.write({'state': 'notified'})

    def action_close(self):
        self.write({'state': 'closed'})
