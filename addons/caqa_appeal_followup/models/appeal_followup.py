from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CaqaAppealCase(models.Model):
    _name = 'caqa.appeal.case'
    _description = 'Appeal Case'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'submitted_on desc, id desc'

    reference = fields.Char(default=lambda self: _('New'), copy=False, readonly=True, tracking=True)
    application_id = fields.Many2one('caqa.application', required=True, ondelete='cascade', tracking=True)
    institution_id = fields.Many2one(related='application_id.institution_id', store=True, readonly=True)
    decision_id = fields.Many2one('caqa.final.decision', ondelete='set null', tracking=True)
    subject = fields.Char(required=True)
    reason = fields.Html()
    resolution_text = fields.Html()
    submitted_on = fields.Datetime(default=fields.Datetime.now)
    reviewer_id = fields.Many2one('res.users')
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('under_review', 'Under Review'), ('accepted', 'Accepted'), ('rejected', 'Rejected'), ('closed', 'Closed')], default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        seq = self.env['ir.sequence']
        for rec in records:
            if rec.reference == _('New'):
                rec.reference = seq.next_by_code('caqa.appeal.case') or _('New')
            rec.application_id.action_mark_appealed()
        return records

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_under_review(self):
        self.write({'state': 'under_review'})

    def action_accept(self):
        self.write({'state': 'accepted'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_close(self):
        self.write({'state': 'closed'})


class CaqaFollowupPlan(models.Model):
    _name = 'caqa.followup.plan'
    _description = 'Follow-up Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'due_date, id'

    name = fields.Char(required=True)
    application_id = fields.Many2one('caqa.application', required=True, ondelete='cascade')
    institution_id = fields.Many2one(related='application_id.institution_id', store=True, readonly=True)
    decision_id = fields.Many2one('caqa.final.decision', ondelete='set null')
    owner_id = fields.Many2one('res.users')
    due_date = fields.Date()
    progress_rate = fields.Float(compute='_compute_progress', store=True)
    state = fields.Selection([('draft', 'Draft'), ('active', 'Active'), ('completed', 'Completed'), ('closed', 'Closed')], default='draft', tracking=True)
    note = fields.Html()
    item_ids = fields.One2many('caqa.followup.item', 'plan_id')

    @api.depends('item_ids.completion_rate')
    def _compute_progress(self):
        for rec in self:
            rates = rec.item_ids.mapped('completion_rate')
            rec.progress_rate = round(sum(rates) / len(rates), 2) if rates else 0.0

    def action_activate(self):
        self.write({'state': 'active'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_close(self):
        self.write({'state': 'closed'})


class CaqaFollowupItem(models.Model):
    _name = 'caqa.followup.item'
    _description = 'Follow-up Item'
    _order = 'due_date, id'

    plan_id = fields.Many2one('caqa.followup.plan', required=True, ondelete='cascade')
    title = fields.Char(required=True)
    indicator_id = fields.Many2one('caqa.application.indicator', ondelete='set null')
    responsible_user_id = fields.Many2one('res.users')
    due_date = fields.Date()
    state = fields.Selection([('draft', 'Draft'), ('in_progress', 'In Progress'), ('done', 'Done'), ('waived', 'Waived')], default='draft')
    completion_rate = fields.Float(default=0.0)
