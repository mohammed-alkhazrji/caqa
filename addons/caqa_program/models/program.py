from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CaqaProgram(models.Model):
    _name = 'caqa.program'
    _description = 'Academic Program'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'reference desc, id desc'

    name = fields.Char(required=True, tracking=True)
    arabic_name = fields.Char(tracking=True)
    reference = fields.Char(default=lambda self: _('New'), copy=False, readonly=True, tracking=True)
    code = fields.Char(required=True, tracking=True, index=True)
    institution_id = fields.Many2one('res.partner', required=True, ondelete='restrict', domain=[('is_caqa_institution', '=', True)], tracking=True)
    degree_level = fields.Selection([('diploma', 'Diploma'), ('bachelor', 'Bachelor'), ('master', 'Master'), ('doctorate', 'Doctorate')], default='bachelor', required=True, tracking=True)
    delivery_mode = fields.Selection([('onsite', 'Onsite'), ('online', 'Online'), ('blended', 'Blended')], default='onsite', tracking=True)
    language = fields.Selection([('ar', 'Arabic'), ('en', 'English'), ('bilingual', 'Bilingual')], default='ar', tracking=True)
    college_name = fields.Char(tracking=True)
    department_name = fields.Char(tracking=True)
    duration_years = fields.Float(tracking=True)
    credit_hours = fields.Float(tracking=True)
    start_date = fields.Date(tracking=True)
    coordinator_id = fields.Many2one('res.users', tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('active', 'Active'), ('suspended', 'Suspended'), ('closed', 'Closed')], default='draft', required=True, tracking=True)
    description = fields.Html()
    vision = fields.Html()
    mission = fields.Html()
    profile_completion = fields.Float(compute='_compute_profile_completion', store=True)
    course_ids = fields.One2many('caqa.program.course', 'program_id', string='Courses')
    learning_outcome_ids = fields.One2many('caqa.program.learning.outcome', 'program_id', string='Learning Outcomes')
    course_count = fields.Integer(compute='_compute_counts')
    learning_outcome_count = fields.Integer(compute='_compute_counts')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('caqa_program_code_institution_uniq', 'unique(code, institution_id)', 'Program code must be unique per institution.'),
    ]

    @api.depends('course_ids', 'learning_outcome_ids')
    def _compute_counts(self):
        for rec in self:
            rec.course_count = len(rec.course_ids)
            rec.learning_outcome_count = len(rec.learning_outcome_ids)

    @api.depends('vision', 'mission', 'description', 'duration_years', 'credit_hours', 'coordinator_id', 'course_ids', 'learning_outcome_ids')
    def _compute_profile_completion(self):
        for rec in self:
            checks = [bool(rec.vision), bool(rec.mission), bool(rec.description), rec.duration_years > 0, rec.credit_hours > 0, bool(rec.coordinator_id), bool(rec.course_ids), bool(rec.learning_outcome_ids)]
            rec.profile_completion = (sum(1 for c in checks if c) / len(checks)) * 100 if checks else 0.0

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env['ir.sequence']
        for vals in vals_list:
            if vals.get('reference', _('New')) == _('New'):
                vals['reference'] = sequence.next_by_code('caqa.program') or _('New')
        return super().create(vals_list)

    @api.constrains('duration_years', 'credit_hours')
    def _check_positive_values(self):
        for rec in self:
            if rec.duration_years and rec.duration_years < 0:
                raise ValidationError(_('Program duration cannot be negative.'))
            if rec.credit_hours and rec.credit_hours < 0:
                raise ValidationError(_('Credit hours cannot be negative.'))

    def action_activate(self):
        self.write({'state': 'active'})

    def action_suspend(self):
        self.write({'state': 'suspended'})

    def action_close(self):
        self.write({'state': 'closed'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    def action_view_courses(self):
        self.ensure_one()
        action = self.env.ref('caqa_program.action_caqa_program_course').read()[0]
        action['domain'] = [('program_id', '=', self.id)]
        action['context'] = {'default_program_id': self.id}
        return action

    def action_view_learning_outcomes(self):
        self.ensure_one()
        action = self.env.ref('caqa_program.action_caqa_program_learning_outcome').read()[0]
        action['domain'] = [('program_id', '=', self.id)]
        action['context'] = {'default_program_id': self.id}
        return action
