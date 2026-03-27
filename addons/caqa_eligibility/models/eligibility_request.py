from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CaqaEligibilityRequest(models.Model):
    _name = 'caqa.eligibility.request'
    _description = 'Eligibility Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'request_date desc, id desc'

    name = fields.Char(required=True, tracking=True)
    reference = fields.Char(default=lambda self: _('New'), copy=False, readonly=True, tracking=True)
    institution_id = fields.Many2one('res.partner', required=True, ondelete='restrict', domain=[('is_caqa_institution', '=', True)], tracking=True)
    institution_type_id = fields.Many2one(related='institution_id.institution_type_id', store=True, readonly=True)
    program_id = fields.Many2one('caqa.program', required=True, ondelete='restrict', tracking=True)
    accreditation_type_id = fields.Many2one('caqa.accreditation.type', required=True, ondelete='restrict', tracking=True)
    cycle_id = fields.Many2one('caqa.accreditation.cycle', required=True, ondelete='restrict', tracking=True)
    standard_version_id = fields.Many2one('caqa.standard.version', required=True, ondelete='restrict', tracking=True)
    request_date = fields.Date(default=fields.Date.context_today, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('eligible', 'Eligible'),
        ('ineligible', 'Ineligible'),
        ('closed', 'Closed'),
    ], default='draft', required=True, tracking=True)
    note = fields.Html()
    review_note = fields.Html()
    checklist_line_ids = fields.One2many('caqa.eligibility.checklist.line', 'request_id', string='Checklist')
    checklist_completion = fields.Float(compute='_compute_scores', store=True)
    profile_readiness = fields.Float(compute='_compute_scores', store=True)
    program_readiness = fields.Float(compute='_compute_scores', store=True)
    readiness_score = fields.Float(compute='_compute_scores', store=True)
    eligible_for_application = fields.Boolean(compute='_compute_scores', store=True)
    application_count = fields.Integer(compute='_compute_application_count')

    _sql_constraints = [
        ('caqa_eligibility_reference_uniq', 'unique(reference)', 'Eligibility reference must be unique.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        seq = self.env['ir.sequence']
        for rec in records:
            if rec.reference == _('New'):
                rec.reference = seq.next_by_code('caqa.eligibility.request') or _('New')
            if not rec.checklist_line_ids:
                rec.action_generate_default_checklist()
        return records

    @api.depends('checklist_line_ids.provided', 'checklist_line_ids.is_required', 'institution_id.active_profile_id.profile_completion', 'program_id.profile_completion')
    def _compute_scores(self):
        for rec in self:
            required_lines = rec.checklist_line_ids.filtered('is_required')
            provided = required_lines.filtered('provided')
            rec.checklist_completion = (len(provided) / len(required_lines) * 100.0) if required_lines else 0.0
            rec.profile_readiness = rec.institution_id.active_profile_id.profile_completion or 0.0
            rec.program_readiness = rec.program_id.profile_completion or 0.0
            rec.readiness_score = round((rec.checklist_completion + rec.profile_readiness + rec.program_readiness) / 3.0, 2)
            rec.eligible_for_application = rec.readiness_score >= 70.0 and rec.checklist_completion >= 80.0

    @api.depends('reference')
    def _compute_application_count(self):
        for rec in self:
            rec.application_count = self.env['caqa.application'].search_count([('eligibility_id', '=', rec.id)]) if 'caqa.application' in self.env else 0

    def action_generate_default_checklist(self):
        checklist_templates = [
            _('Institution profile is completed'),
            _('Program specification is available'),
            _('Mission and vision are documented'),
            _('Quality assurance structure is documented'),
            _('Key governance documents are available'),
        ]
        for rec in self:
            if rec.checklist_line_ids:
                continue
            self.env['caqa.eligibility.checklist.line'].create([{
                'request_id': rec.id,
                'name': item,
                'description': item,
                'is_required': True,
            } for item in checklist_templates])

    def action_set_in_progress(self):
        self.write({'state': 'in_progress'})

    def action_submit(self):
        for rec in self:
            if not rec.checklist_line_ids:
                raise ValidationError(_('Checklist lines are required before submission.'))
            if rec.checklist_completion < 50:
                raise ValidationError(_('Checklist completion is too low for submission.'))
            rec.state = 'submitted'

    def action_under_review(self):
        self.write({'state': 'under_review'})

    def action_mark_eligible(self):
        for rec in self:
            if not rec.eligible_for_application:
                raise ValidationError(_('Eligibility thresholds are not met.'))
            rec.state = 'eligible'

    def action_mark_ineligible(self):
        self.write({'state': 'ineligible'})

    def action_close(self):
        self.write({'state': 'closed'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    def action_view_applications(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Applications'),
            'res_model': 'caqa.application',
            'view_mode': 'tree,form',
            'domain': [('eligibility_id', '=', self.id)],
            'context': {'default_eligibility_id': self.id},
        }


class CaqaEligibilityChecklistLine(models.Model):
    _name = 'caqa.eligibility.checklist.line'
    _description = 'Eligibility Checklist Line'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    request_id = fields.Many2one('caqa.eligibility.request', required=True, ondelete='cascade')
    name = fields.Char(required=True)
    description = fields.Text()
    is_required = fields.Boolean(default=True)
    provided = fields.Boolean()
    reviewer_verified = fields.Boolean()
    note = fields.Char()
